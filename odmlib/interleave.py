"""Order-preserving storage for XSD repeating groups that interleave two child types.

A few ODM 2.0 content models put two child element types in one repeating group, so
the two can alternate freely:

- ``ItemGroupDef``: ``(ItemGroupRef?, ItemRef?)+``
- ``StudyEventGroupDef``: ``(StudyEventGroupRef?, StudyEventRef?)+``
- ``WorkflowDef``: ``(Transition?, Branching?)+``

odmlib exposes each type as its own list (``igd.ItemRef``, ``igd.ItemGroupRef``). Those
lists are :class:`GroupMemberList` views onto one :class:`InterleavedGroup`, which holds
every member in document order. Loading keeps the source order, serialization writes it
back, and a child appended to either list goes to the end of the combined sequence.

A model opts in by declaring its member descriptors with the same ``group`` name::

    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef, group="ItemGroupDefGroup")
    ItemRef = T.ODMListObject(element_class=ItemRef, group="ItemGroupDefGroup")

Membership is by identity: a child object belongs to exactly one list of one group.

.. versionadded:: 0.3.0
"""
from __future__ import annotations
from collections import Counter
from difflib import SequenceMatcher
from typing import Any, Iterable, List, Optional, Sequence, Tuple

_MISSING = object()


class InterleavedGroup:
    """The ordered sequence shared by the per-type lists of one repeating group.

    Attributes:
        names: The member element names, in model declaration order.
        sequence: Every member child, in document order.
        views: ``{name: GroupMemberList}`` for the lists attached to this group.
    """

    def __init__(self, names: Sequence[str]) -> None:
        self.names = tuple(names)
        self.sequence: List[Any] = []
        self.views: dict = {}

    def resync(self, view: "GroupMemberList") -> None:
        """Bring :attr:`sequence` back in line after an arbitrary change to *view*.

        Every child of *view* is placed relative to the children of the *other*
        lists, which never move:

        - a child that was already in *view* keeps one of the slots *view*'s
          children held, and the slots are refilled in *view*'s new order, so
          ``sort()`` and ``reverse()`` reorder a type without changing the
          interleaving pattern;
        - a child that replaces another (``view[i] = x``, slice assignment) takes
          the slot of the child it replaced;
        - any other new child goes immediately before the next child of *view*,
          or at the end when none follows, so ``insert(len(view), x)`` is exactly
          ``append(x)``.

        Children no longer in *view* drop out.
        """
        other_ids = set()
        for other in self.views.values():
            if other is not view:
                other_ids.update(id(child) for child in other)
        others = []
        old = []
        old_anchor = []            # how many other-list children precede each old child
        for child in self.sequence:
            if id(child) in other_ids:
                others.append(child)
            else:
                old.append(child)
                old_anchor.append(len(others))
        new = list(view)
        anchor: List[Optional[int]] = [None] * len(new)
        kept_ids = {id(child) for child in old} & {id(child) for child in new}
        kept_slots = sorted(a for child, a in zip(old, old_anchor) if id(child) in kept_ids)
        kept_positions = [j for j, child in enumerate(new) if id(child) in kept_ids]
        for j, slot in zip(kept_positions, kept_slots):
            anchor[j] = slot
        matcher = SequenceMatcher(None, [id(c) for c in old], [id(c) for c in new],
                                  autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "replace":
                for offset, j in enumerate(range(j1, j2)):
                    if anchor[j] is None:
                        anchor[j] = old_anchor[min(i1 + offset, i2 - 1)]
        following = len(others)
        for j in reversed(range(len(new))):
            if anchor[j] is None:
                anchor[j] = following
            following = anchor[j]
        sequence = []
        placed = 0
        floor = 0
        for child, slot in zip(new, anchor):
            floor = max(floor, slot)            # keep view order whatever the anchors
            while placed < floor:
                sequence.append(others[placed])
                placed += 1
            sequence.append(child)
        sequence.extend(others[placed:])
        self.sequence[:] = sequence


class GroupMemberList(list):
    """A per-type list that is a write-through view onto an :class:`InterleavedGroup`.

    It is a real ``list``: reading, iterating, indexing and comparing behave exactly as
    before. Every mutating method also updates the shared sequence, so the document
    order of the group survives edits. ``append``/``extend`` add to the end of the
    combined sequence; see :meth:`InterleavedGroup.resync` for the other operations.

    A detached list (one replaced by assigning a new list to the attribute) behaves as a
    plain list. ``copy.copy()`` of a view returns a plain list.
    """

    def __init__(self, items: Iterable[Any] = (), group: Optional[InterleavedGroup] = None,
                 name: Optional[str] = None) -> None:
        list.__init__(self, items)
        self._group = group
        self._name = name

    # --- mutators: append/extend are O(1) per item; the rest resync --------

    def append(self, item: Any) -> None:
        list.append(self, item)
        if self._group is not None:
            self._group.sequence.append(item)

    def extend(self, items: Iterable[Any]) -> None:
        items = list(items)
        list.extend(self, items)
        if self._group is not None:
            self._group.sequence.extend(items)

    def __iadd__(self, items: Iterable[Any]) -> "GroupMemberList":
        self.extend(items)
        return self

    def _resync(self) -> None:
        if self._group is not None:
            self._group.resync(self)

    def insert(self, index: Any, item: Any) -> None:
        list.insert(self, index, item)
        self._resync()

    def remove(self, item: Any) -> None:
        list.remove(self, item)
        self._resync()

    def pop(self, index: Any = -1) -> Any:
        item = list.pop(self, index)
        self._resync()
        return item

    def clear(self) -> None:
        list.clear(self)
        self._resync()

    def sort(self, *args: Any, **kwargs: Any) -> None:
        list.sort(self, *args, **kwargs)
        self._resync()

    def reverse(self) -> None:
        list.reverse(self)
        self._resync()

    def __setitem__(self, index: Any, value: Any) -> None:
        list.__setitem__(self, index, value)
        self._resync()

    def __delitem__(self, index: Any) -> None:
        list.__delitem__(self, index)
        self._resync()

    def __imul__(self, count: Any) -> "GroupMemberList":
        list.__imul__(self, count)
        self._resync()
        return self

    # --- copying and pickling -----------------------------------------------

    def __copy__(self) -> list:
        # a shallow copy sharing the group would write through to it; hand back data
        return list(self)

    def __reduce__(self) -> Tuple[Any, ...]:
        # restore through __setstate__ so the items are not re-appended to the
        # (already restored) group, which the default list protocol would do
        return (_new_member_list, (), {"items": list(self), "group": self._group,
                                       "name": self._name})

    def __setstate__(self, state: dict) -> None:
        list.__init__(self, state["items"])
        self._group = state["group"]
        self._name = state["name"]


def _new_member_list() -> GroupMemberList:
    return GroupMemberList()


def attach(instance: Any, name: str, names: Sequence[str], items: Iterable[Any]) -> GroupMemberList:
    """Store *items* as the *name* list of *instance*'s interleaved group.

    Called by the ``ODMListObject`` descriptor on every assignment, including the empty
    list created on first access. A list that replaces an existing one takes over the
    replaced children's positions in order; any extra children go to the end.

    Args:
        instance: The element that owns the group.
        name: The member being assigned, e.g. ``"ItemRef"``.
        names: Every member name of the group, in model declaration order.
        items: The children to store.

    Returns:
        The new view, to be stored in ``instance.__dict__[name]``.
    """
    names = tuple(names)
    stored = instance.__dict__
    group = None
    for member in names:
        view = stored.get(member)
        if isinstance(view, GroupMemberList) and view._group is not None \
                and view._group.names == names:
            group = view._group
            break
    if group is None:
        group = InterleavedGroup(names)
        # adopt a sibling stored as a plain list (e.g. written straight to __dict__)
        for member in names:
            sibling = stored.get(member)
            if member != name and isinstance(sibling, list):
                adopted = GroupMemberList(sibling, group, member)
                group.views[member] = adopted
                group.sequence.extend(adopted)
                stored[member] = adopted
    new = GroupMemberList(items, group, name)
    old = group.views.get(name)
    if old is not None:
        old_ids = {id(child) for child in old}
        fill = iter(new)
        sequence = []
        for child in group.sequence:
            if id(child) in old_ids:
                replacement = next(fill, _MISSING)
                if replacement is not _MISSING:
                    sequence.append(replacement)
            else:
                sequence.append(child)
        sequence.extend(fill)
        group.sequence[:] = sequence
        old._group = None
    else:
        group.sequence.extend(new)
    group.views[name] = new
    return new


def detach(value: Any) -> None:
    """Remove a view's children from its group and turn it into a plain list."""
    if isinstance(value, GroupMemberList) and value._group is not None:
        group = value._group
        gone = {id(child) for child in value}
        group.sequence[:] = [child for child in group.sequence if id(child) not in gone]
        group.views.pop(value._name, None)
        value._group = None


def ordered_members(instance: Any, names: Sequence[str]) -> List[Tuple[str, Any]]:
    """Return ``[(name, child), ...]`` for a group's members in document order.

    Falls back to model order (every child of the first name, then the second) when the
    lists are not views of one group, e.g. lists stored straight into ``__dict__``.
    Children found in a list but missing from the shared sequence are never dropped:
    they follow the ordered ones, in model order.
    """
    stored = instance.__dict__
    present = [(name, stored[name]) for name in names if isinstance(stored.get(name), list)]
    owner: dict = {}
    remaining: Counter = Counter()
    for name, members in present:
        for child in members:
            owner.setdefault(id(child), name)
            remaining[id(child)] += 1
    group = None
    views = [members for _, members in present]
    if views and all(isinstance(v, GroupMemberList) and v._group is not None for v in views):
        candidate = views[0]._group
        if all(v._group is candidate and candidate.views.get(v._name) is v for v in views):
            group = candidate
    ordered: List[Tuple[str, Any]] = []
    if group is not None:
        for child in group.sequence:
            if remaining[id(child)] > 0:
                ordered.append((owner[id(child)], child))
                remaining[id(child)] -= 1
    for name, members in present:
        for child in members:
            if remaining[id(child)] > 0:
                ordered.append((name, child))
                remaining[id(child)] -= 1
    return ordered
