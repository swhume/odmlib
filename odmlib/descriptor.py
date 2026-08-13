"""Base descriptor protocol for ODM element attributes.

This module provides the :class:`Descriptor` base class that implements
the Python descriptor protocol for ODM element attributes. All odmlib
attribute types inherit from this class.
"""
from __future__ import annotations
import weakref
from typing import Any, Optional
from odmlib.exceptions import OdmlibRequiredAttributeError
import odmlib.mode as _mode


# Elements instantiated as a side effect of reading an unset optional child
# attribute (the auto-vivification that makes `elem.Child.Sub.append(...)`
# work). Serialization skips members of this set that were never populated,
# so read-only inspection cannot inject spurious empty elements into output.
_AUTO_CREATED: "weakref.WeakSet" = weakref.WeakSet()


def _effectively_empty(elem: Any) -> bool:
    """True when every stored value is None, an empty list, or itself a
    pristine auto-created element."""
    for value in elem.__dict__.values():
        if value is None:
            continue
        if isinstance(value, list):
            if value:
                return False
            continue
        try:
            auto_created = value in _AUTO_CREATED
        except TypeError:
            auto_created = False
        if auto_created and _effectively_empty(value):
            continue
        return False
    return True


def is_pristine_auto_created(elem: Any) -> bool:
    """True if *elem* was auto-created by attribute access and never populated.

    Used by serialization to skip empty elements that exist only because an
    unset optional child attribute was read.
    """
    try:
        if elem not in _AUTO_CREATED:
            return False
    except TypeError:
        return False
    return _effectively_empty(elem)


class Descriptor:
    """Base descriptor for all ODM element attributes.

    Implements the Python descriptor protocol (``__get__``, ``__set__``,
    ``__delete__``). When accessed on a class, returns the descriptor
    itself. When accessed on an instance, returns the value from the
    instance's ``__dict__``.

    For required attributes without a set value, raises
    :exc:`~odmlib.exceptions.OdmlibRequiredAttributeError`.
    For optional list attributes without a value, auto-initializes to []
    (stored on the instance so the append idiom works).
    For unset optional scalar attributes, returns ``None``.
    For unset single child elements, auto-instantiates the element class
    when it can be constructed empty (returns ``None`` otherwise); the
    auto-created child is skipped by serialization unless populated.

    Args:
        name (str): Attribute name (set by :class:`ODMMeta` during class creation).
        required (bool): If True, attribute must be provided at construction.
        element_class (type): For child element descriptors, the expected class.
        valid_values (list): List of permitted values (empty = any value).
        namespace (str): XML namespace prefix (default: "odm").
    """

    def __init__(self, name: Optional[str] = None, required: bool = False,
                 element_class: Optional[type] = None,
                 valid_values: Optional[list] = None,
                 namespace: str = "odm") -> None:
        self.name = name
        self.required = required
        self.element_class = element_class
        self.valid_values = valid_values if valid_values is not None else []
        self.namespace = namespace

    def __get__(self, instance: Any, cls: type) -> Any:
        """Return the descriptor itself (class access) or the stored value (instance access).

        Args:
            instance: The object instance, or None if accessed on the class.
            cls: The owner class.

        Returns:
            The descriptor itself when accessed on the class, or the stored
            attribute value when accessed on an instance.

        Raises:
            OdmlibRequiredAttributeError: If the attribute is required and has
                not been set on the instance.
        """
        if instance is None:
            return self
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        # Attribute not set on instance — raise only for plain required attributes
        # (not ODMObject/ODMListObject, which have element_class set and auto-initialize)
        if self.required and self.element_class is None:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_REQUIRED):
                raise OdmlibRequiredAttributeError(
                    f"Missing attribute or element {self.name} in {cls.__name__}",
                    attribute=self.name,
                    element_type=cls.__name__,
                    hint=f"Attribute '{self.name}' is required when constructing {cls.__name__}",
                )
            else:
                return None
        # Auto-initialize optional LIST attributes: the stored empty list is
        # what makes the `elem.Child.append(...)` idiom work.
        if isinstance(self, list):
            self.__set__(instance, [])
            return instance.__dict__[self.name]
        # Unset optional scalar: read as None without mutating the instance.
        if self.element_class is None:
            return None
        # Unset single child element: auto-create so chained population works
        # (`rc.ErrorMessage.TranslatedText.append(...)`). The instance is
        # tracked so serialization can skip it if it is never populated.
        try:
            child = self.element_class()
        except OdmlibRequiredAttributeError:
            # cannot be constructed empty — leave the attribute unset
            return None
        instance.__dict__[self.name] = child
        _AUTO_CREATED.add(child)
        return child

    def __set__(self, instance: Any, value: Any) -> None:
        """Store ``value`` in the instance's ``__dict__`` under this descriptor's name.

        Args:
            instance: The object instance on which to set the value.
            value: The value to store.
        """
        instance.__dict__[self.name] = value

    def __delete__(self, instance: Any) -> None:
        """Remove this attribute from the instance's ``__dict__``.

        Args:
            instance: The object instance from which to remove the attribute.
        """
        del instance.__dict__[self.name]
