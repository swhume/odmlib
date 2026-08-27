"""Dynamic OID ref/def check generation from model introspection.

Inspects odmlib model class definitions to automatically derive:

- Which classes are OID definitions (have an attribute named ``OID``).
- Which attributes are OID references (any attribute whose name contains
  ``"OID"`` but is not the definition attribute itself).
- The mapping from reference attribute names to definition element classes.
- The reverse mapping from definition element classes to reference attributes.

This replaces the manually-coded dictionaries in the ``rules/oid_ref.py``
files for each model package.  The dynamic system is derived directly from
the model classes, so it stays in sync automatically when the models evolve.

Usage::

    from odmlib.oid_generator import create_oid_checker

    checker = create_oid_checker("odm_1_3_2")
    odm.verify_oids(checker)

.. versionadded:: 0.2.0
"""
from __future__ import annotations

import importlib
import warnings
from typing import Any, Optional

from odmlib.exceptions import ErrorReporting, OdmlibOIDError
from odmlib.odm_element import ODMElement
import odmlib.typed as T


# ---------------------------------------------------------------------------
# Override Mappings
# ---------------------------------------------------------------------------
# These handle naming irregularities where the convention
# (strip "OID" suffix → try "<base>Def", then "<base>") doesn't resolve
# to a valid definition class in a given model package.
#
# Convention example:
#   "FormOID"   → "Form"   → "FormDef"   → found in model → OK
#   "CodeListOID" → "CodeList" → "CodeListDef" → NOT found → "CodeList" → found → OK
#
# Override example:
#   "CollectionExceptionConditionOID" → "CollectionExceptionCondition"
#   → "CollectionExceptionConditionDef" NOT found → "CollectionExceptionCondition"
#   NOT found → falls to this override → "ConditionDef"
#
# An override is only applied when the target class EXISTS in the model
# being introspected (checked via model_classes lookup).  This means the
# same override dict works correctly across all model packages.

_REF_DEF_OVERRIDES: dict[str, str] = {
    # ODM 1.3.2 -- classes whose names diverge from the <strip>Def / <strip>
    # convention.
    "CollectionExceptionConditionOID": "ConditionDef",

    # ODM 2.0 -- workflow and timing constraint OIDs whose targets cannot be
    # inferred from the attribute name alone.
    "StartConditionOID": "ConditionDef",
    "EndConditionOID": "ConditionDef",
    "ConditionOID": "ConditionDef",
    "ArmOID": "Arm",
    "EpochOID": "Epoch",
    "WorkflowOID": "WorkflowDef",
    "StudyEventGroupOID": "StudyEventGroupDef",
    "TransitionOID": "Transition",

    # RoleCodeListOID (found in ItemRef) references a CodeList but the
    # naming convention doesn't resolve (RoleCodeListDef / RoleCodeList
    # don't exist as model classes).
    "RoleCodeListOID": "CodeList",
}


# Document references are ID-based rather than OID-named: leaf/@ID
# (Define-XML) and Leaf/@ID (ODM 2.0) are the definitions, referenced by
# DocumentRef/@leafID, DocumentRef/@LeafID and
# ItemGroupDef/@def:ArchiveLocationID.  These pairs are surfaced by
# ODMElement._init_oid_check alongside the OID-named attributes; they
# are only wired up when the target class exists in the model package.
_ID_REF_DEF_PAIRS: dict[str, str] = {
    "leafID": "leaf",
    "ArchiveLocationID": "leaf",
    # ODM 2.0 spells the element Leaf and the reference LeafID.
    "LeafID": "Leaf",
}


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

def discover_model_classes(model_module: Any) -> dict[str, type]:
    """Return all ODMElement subclasses found in *model_module*.

    Args:
        model_module: An imported odmlib model module, e.g.
            ``odmlib.odm_1_3_2.model``.

    Returns:
        Mapping of class name → class object for every
        :class:`~odmlib.odm_element.ODMElement` subclass exposed at module
        level.
    """
    classes: dict[str, type] = {}
    for name in dir(model_module):
        obj = getattr(model_module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, ODMElement)
            and obj is not ODMElement
        ):
            classes[name] = obj
    return classes


def discover_oid_definitions(model_classes: dict[str, type]) -> list[str]:
    """Find all model classes that define an OID.

    A class is a "definition" element when it has an attribute literally
    named ``"OID"`` in its ``_attrs`` dict (regardless of descriptor type).
    This mirrors the runtime behaviour in
    :meth:`~odmlib.odm_element.ODMElement._init_oid_check`, which registers
    any ``attr == "OID"`` as a definition.

    Args:
        model_classes: Mapping returned by :func:`discover_model_classes`.

    Returns:
        List of class names that have an ``OID`` attribute.
    """
    oid_defs: list[str] = []
    for name, cls in model_classes.items():
        attrs = getattr(cls, "_attrs", {})
        if "OID" in attrs:
            oid_defs.append(name)
        elif "ID" in attrs and name in _ID_REF_DEF_PAIRS.values():
            oid_defs.append(name)
    return oid_defs


def discover_oid_references(model_classes: dict[str, type]) -> dict[str, list[str]]:
    """Find all OID reference attributes across all model classes.

    An attribute is an OID reference when its name contains the substring
    ``"OID"`` but is NOT itself named exactly ``"OID"`` (which would be a
    definition).  This mirrors the runtime check
    ``elif "OID" in attr: oid_checker.add_oid_ref(obj, attr)`` in
    :meth:`~odmlib.odm_element.ODMElement._init_oid_check`.

    Args:
        model_classes: Mapping returned by :func:`discover_model_classes`.

    Returns:
        Mapping of ``ref_attr_name → [class_names …]`` listing every class
        that carries each reference attribute.
    """
    refs: dict[str, list[str]] = {}
    for cls_name, cls in model_classes.items():
        attrs = getattr(cls, "_attrs", {})
        for attr_name in attrs:
            if ("OID" in attr_name and attr_name != "OID") or attr_name in _ID_REF_DEF_PAIRS:
                if attr_name not in refs:
                    refs[attr_name] = []
                refs[attr_name].append(cls_name)
    return refs


def build_ref_def_mapping(
    ref_attrs: dict[str, list[str]],
    oid_defs: list[str],
    model_classes: dict[str, type],
) -> dict[str, str]:
    """Build the mapping from reference attribute names to definition classes.

    Resolution order for each reference attribute:

    1. Check :data:`_REF_DEF_OVERRIDES`; only apply the override if its
       target class exists in *model_classes* (so the same override dict
       works for all model packages).
    2. Strip the ``"OID"`` suffix from the attribute name and try
       ``<base>Def`` first, then ``<base>`` as the definition class name.

    If neither step resolves to a known definition class, the attribute is
    not added to the mapping and will not be validated.

    Args:
        ref_attrs: Mapping returned by :func:`discover_oid_references`.
        oid_defs: List returned by :func:`discover_oid_definitions`.
        model_classes: Mapping returned by :func:`discover_model_classes`.

    Returns:
        Mapping of ``ref_attr_name → definition_class_name``.
    """
    ref_def: dict[str, str] = {}
    oid_def_set = set(oid_defs)

    for attr_name in ref_attrs:
        # --- Step 0: ID-based ref/def pairs (Define-XML leaf references) -------
        if attr_name in _ID_REF_DEF_PAIRS:
            target = _ID_REF_DEF_PAIRS[attr_name]
            if target in model_classes:
                ref_def[attr_name] = target
            continue

        # --- Step 1: check overrides ------------------------------------------
        if attr_name in _REF_DEF_OVERRIDES:
            target = _REF_DEF_OVERRIDES[attr_name]
            # Only use the override when the target class exists in this model.
            if target in model_classes:
                ref_def[attr_name] = target
            # Either way, do not fall through to the convention for
            # override-registered names.
            continue

        # --- Step 2: naming convention ----------------------------------------
        if attr_name.endswith("OID"):
            base = attr_name[:-3]  # strip "OID" suffix
            if base + "Def" in oid_def_set:
                ref_def[attr_name] = base + "Def"
            elif base in oid_def_set:
                ref_def[attr_name] = base
            # else: unresolvable — silently skip; the attr will not be
            # validated but will not cause false positives either.

    return ref_def


def build_def_ref_mapping(
    ref_def: dict[str, str],
) -> dict[str, list[str]]:
    """Build the reverse mapping from definition classes to reference attributes.

    This is used by :meth:`DynamicOIDRef.check_unreferenced_oids` to find
    which reference attributes (if any) point to each definition class.

    Args:
        ref_def: Mapping returned by :func:`build_ref_def_mapping`.

    Returns:
        Mapping of ``definition_class_name → [ref_attr_names …]``.
    """
    def_ref: dict[str, list[str]] = {}
    for attr_name, def_class in ref_def.items():
        if def_class not in def_ref:
            def_ref[def_class] = []
        if attr_name not in def_ref[def_class]:
            def_ref[def_class].append(attr_name)
    return def_ref


# ---------------------------------------------------------------------------
# Main dynamic checker
# ---------------------------------------------------------------------------

class DynamicOIDRef(ErrorReporting):
    """Dynamically-generated OID ref/def checker.

    Drop-in replacement for the manually-coded ``OIDRef`` classes in the
    ``rules/oid_ref.py`` files.  Introspects the model module at
    instantiation time to build the ref/def mappings automatically.

    Implements the same interface as the manual ``OIDRef`` classes so it can
    be passed directly to
    :meth:`~odmlib.odm_element.ODMElement.verify_oids`.

    Via the :class:`~odmlib.exceptions.ErrorReporting` mixin it also supports
    the collecting-checker protocol, so
    :meth:`~odmlib.odm_element.ODMElement.validate` with
    ``collect_errors=True`` reports *every* duplicate and every bad reference
    rather than only the first. The deprecated manual ``OIDRef`` classes do
    not, and contribute at most one error.

    Note:
        A checker accumulates every OID it sees, so it is single-use per
        document. Call :meth:`reset` before validating a second document (or
        re-validating the same one), otherwise every OID is reported as a
        duplicate.

    Args:
        model_package: Model package name, e.g. ``"odm_1_3_2"`` or
            ``"define_2_1"``.
        skip_attrs: Attribute names to ignore during validation (e.g.
            ``["FileOID", "PriorFileOID"]``).
        skip_elems: Element class names to ignore when registering OID
            definitions (e.g. ``["ODM"]``).

    Example::

        from odmlib.oid_generator import create_oid_checker

        checker = create_oid_checker("odm_1_3_2")
        odm.verify_oids(checker)

    .. versionadded:: 0.2.0
    """

    def __init__(
        self,
        model_package: str,
        skip_attrs: Optional[list[str]] = None,
        skip_elems: Optional[list[str]] = None,
    ) -> None:
        self.model_package = model_package
        self.model = importlib.import_module(f"odmlib.{model_package}.model")

        # --- Model introspection ---
        self.model_classes = discover_model_classes(self.model)
        self.oid_defs = discover_oid_definitions(self.model_classes)
        self.ref_attrs = discover_oid_references(self.model_classes)

        # --- Static mappings ---
        self.ref_def = build_ref_def_mapping(
            self.ref_attrs, self.oid_defs, self.model_classes
        )
        self.def_ref = build_def_ref_mapping(self.ref_def)

        # --- Runtime state (populated during verify_oids traversal) ---
        # self.oid: OID value → element class name (reference targets only;
        # excludes skip_elem element types)
        self.oid: dict[str, str] = {}
        # self.unique_oids: OID value → element class name for EVERY
        # definition, including skip_elem types — skip_elem only exempts an
        # element from reference-target checking, not from uniqueness
        self.unique_oids: dict[str, str] = {}
        # self.oid_ref: attr name → set of referenced OID values
        self.oid_ref: dict[str, set] = {attr: set() for attr in self.ref_def}
        self.is_verified: bool = False

        # --- Skip lists ---
        self.skip_attr: list[str] = list(skip_attrs) if skip_attrs else []
        self.skip_elem: list[str] = list(skip_elems) if skip_elems else []

    # ------------------------------------------------------------------
    # Runtime population (called by ODMElement._init_oid_check)
    # ------------------------------------------------------------------

    def add_oid(self, oid: str, element: str) -> None:
        """Register an OID definition.

        Called automatically during
        :meth:`~odmlib.odm_element.ODMElement._init_oid_check` traversal.

        Args:
            oid: The OID value to register.
            element: The class name of the element that owns this OID.

        Raises:
            OdmlibOIDError: If *oid* is already registered (duplicate OID).
                Inside a :meth:`~odmlib.exceptions.ErrorReporting.collecting`
                block the error goes to the sink instead and the traversal
                continues, so the reference checks that follow still run.

        Note:
            On a duplicate, the **first** definition is kept — that is what
            the error message asserts, and it keeps :attr:`oid` stable so the
            reference pass gives a deterministic verdict. A corner case worth
            knowing: if the first definition is a ``skip_elem`` type it lands
            only in :attr:`unique_oids`, so the reference pass then reports
            "not found" for everything pointing at it.
        """
        if oid in self.unique_oids:
            self.report(OdmlibOIDError(
                f"OID {oid} is not unique - element {element}",
                attribute="OID",
                hint=(
                    f"Each OID must be unique within a MetaDataVersion. "
                    f"OID '{oid}' is already defined in a {self.unique_oids[oid]} element."
                ),
            ))
            return                                   # first definition wins
        self.unique_oids[oid] = element
        if element in self.skip_elem:
            return
        self.oid[oid] = element

    def add_oid_ref(self, oid: str, attr: str) -> None:
        """Register an OID reference.

        Called automatically during
        :meth:`~odmlib.odm_element.ODMElement._init_oid_check` traversal.

        Args:
            oid: The referenced OID value.
            attr: The attribute name (e.g. ``"FormOID"``, ``"ItemOID"``).
        """
        if attr in self.skip_attr:
            return
        if attr in self.oid_ref:
            self.oid_ref[attr].add(oid)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def is_oids_verified(self) -> bool:
        """Return ``True`` if :meth:`check_oid_refs` has been called."""
        return bool(self.oid and self.is_verified)

    def check_oid_refs(self) -> bool:
        """Validate that all OID references point to valid definitions.

        For each collected OID reference, checks:

        1. The referenced OID exists in the OID definitions.
        2. The definition element type matches what the reference attribute
           expects (per :attr:`ref_def`).

        Returns:
            ``True`` if all references are valid.

        Raises:
            OdmlibOIDError: On the first invalid or mismatched reference.
                Inside a :meth:`~odmlib.exceptions.ErrorReporting.collecting`
                block every bad reference is reported to the sink instead.
        """
        self.is_verified = True
        for attr, oid_set in self.oid_ref.items():
            if attr in self.skip_attr:
                continue
            # oid_set is a set, so iteration order varies with PYTHONHASHSEED.
            # Sort for stable, reproducible error ordering. key=str guards
            # against a non-string OID from a permissive load.
            for oid in sorted(oid_set, key=str):
                if oid not in self.oid:
                    self.report(OdmlibOIDError(
                        f"OID {oid} referenced in attribute {attr} is not found.",
                        attribute=attr,
                        hint=(
                            f"Define an element with OID '{oid}' before "
                            f"referencing it via {attr}."
                        ),
                    ))
                    continue        # one error per bad ref, not two
                expected_type = self.ref_def.get(attr)
                actual_type = self.oid.get(oid)
                if expected_type and actual_type and expected_type != actual_type:
                    self.report(OdmlibOIDError(
                        f"OID reference for attribute {attr} element types do "
                        f"not match: {expected_type} and {actual_type}",
                        attribute=attr,
                        hint=(
                            f"Attribute '{attr}' should reference a "
                            f"{expected_type}, but OID '{oid}' is defined on "
                            f"a {actual_type}."
                        ),
                    ))
        return True

    def reset(self) -> None:
        """Clear all state collected by a previous verification pass.

        A checker accumulates every OID it sees, so reusing one instance for a
        second document — or a second ``validate()`` call on the same document
        — reports every OID as a duplicate. Call ``reset()`` between runs, or
        build a fresh checker with
        :func:`~odmlib.oid_generator.create_oid_checker`.
        """
        self.oid.clear()
        self.unique_oids.clear()
        for oid_set in self.oid_ref.values():
            oid_set.clear()
        self.is_verified = False

    def check_unreferenced_oids(self) -> dict[str, str]:
        """Find OID definitions that are not referenced anywhere.

        Returns:
            Mapping of ``oid_value → ref_attr_name`` for each OID that is
            defined but never referenced.  An empty dict means every
            definition is used.
        """
        all_referenced: set[str] = set()
        for oid_set in self.oid_ref.values():
            all_referenced.update(oid_set)

        orphans: dict[str, str] = {}
        for oid, element_type in self.oid.items():
            if element_type in self.skip_elem:
                continue
            if oid not in all_referenced:
                # Look up which ref_attr is associated with this element type.
                ref_attr = next(
                    (
                        attr
                        for attr, def_class in self.ref_def.items()
                        if def_class == element_type
                    ),
                    element_type,  # fallback: use class name itself
                )
                orphans[oid] = ref_attr
        return orphans


# ---------------------------------------------------------------------------
# Factory function (public API)
# ---------------------------------------------------------------------------

def create_oid_checker(
    model_package: str,
    extra_skip_attrs: Optional[list[str]] = None,
    extra_skip_elems: Optional[list[str]] = None,
) -> DynamicOIDRef:
    """Create a :class:`DynamicOIDRef` checker for a model package.

    This is the primary public API for creating OID checkers.  It loads
    the per-model skip configuration from
    :mod:`odmlib.oid_generator_config` and merges any caller-provided
    extras before constructing the checker.

    Args:
        model_package: Model package name, e.g. ``"odm_1_3_2"``,
            ``"define_2_1"``, ``"odm_2_0"``.
        extra_skip_attrs: Additional attribute names to skip during
            validation (merged with model-level defaults).
        extra_skip_elems: Additional element class names to skip
            (merged with model-level defaults).

    Returns:
        A configured :class:`DynamicOIDRef` instance ready for use with
        :meth:`~odmlib.odm_element.ODMElement.verify_oids`.

    Example::

        from odmlib.oid_generator import create_oid_checker

        # Replace manual OIDRef usage:
        #   from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
        #   checker = OIDRef()
        # With:
        checker = create_oid_checker("odm_1_3_2")
        odm.verify_oids(checker)

    .. versionadded:: 0.2.0
    """
    from odmlib.oid_generator_config import get_skip_config

    skip_attrs, skip_elems = get_skip_config(model_package)
    if extra_skip_attrs:
        skip_attrs = list(skip_attrs) + extra_skip_attrs
    if extra_skip_elems:
        skip_elems = list(skip_elems) + extra_skip_elems

    return DynamicOIDRef(
        model_package,
        skip_attrs=skip_attrs,
        skip_elems=skip_elems,
    )
