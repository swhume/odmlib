"""Per-model skip configuration for dynamic OID ref/def generation.

Defines the ``skip_attr`` and ``skip_elem`` lists for each supported model
package.  These lists mirror the hard-coded skip behaviour in the legacy
manual ``OIDRef`` classes:

- **skip_attr**: OID-containing attribute names that should *not* be
  validated as OID references (e.g. ``FileOID``, which is a top-level file
  identifier, not a reference to another element).
- **skip_elem**: Element class names whose ``OID`` attributes should *not*
  be registered as definitions (e.g. ``ODM``, whose ``FileOID`` is a
  file-level identifier rather than a metadata OID).

Usage (via :func:`odmlib.oid_generator.create_oid_checker`)::

    checker = create_oid_checker("define_2_1")
    odm.verify_oids(checker)

.. versionadded:: 0.2.0
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# ODM 1.3.2
# ---------------------------------------------------------------------------
# Skip FileOID and PriorFileOID since these are file-level identifiers, not
# references to metadata elements.  Skip "ODM" element class for the same
# reason.

ODM_132_SKIP_ATTRS: list[str] = ["FileOID", "PriorFileOID"]
ODM_132_SKIP_ELEMS: list[str] = ["ODM"]

# ---------------------------------------------------------------------------
# Define-XML 2.0
# ---------------------------------------------------------------------------
# In addition to the ODM file-level attributes, Define-XML skips the
# structural attributes StudyOID, MetaDataVersionOID, and ItemGroupOID
# because a Define-XML file describes a single study/version and these
# cross-references are guaranteed valid by the file structure itself.

DEFINE_20_SKIP_ATTRS: list[str] = [
    "FileOID",
    "PriorFileOID",
    "StudyOID",
    "MetaDataVersionOID",
    "ItemGroupOID",
]
DEFINE_20_SKIP_ELEMS: list[str] = [
    "ODM",
    "Study",
    "MetaDataVersion",
    "ItemGroupDef",
]

# ---------------------------------------------------------------------------
# Define-XML 2.1
# ---------------------------------------------------------------------------
# Same rationale as Define-XML 2.0.

DEFINE_21_SKIP_ATTRS: list[str] = [
    "FileOID",
    "PriorFileOID",
    "StudyOID",
    "MetaDataVersionOID",
    "ItemGroupOID",
]
DEFINE_21_SKIP_ELEMS: list[str] = [
    "ODM",
    "Study",
    "MetaDataVersion",
    "ItemGroupDef",
]

# ---------------------------------------------------------------------------
# ODM 2.0
# ---------------------------------------------------------------------------
# Skip file-level identifiers plus certain workflow/timing OID attributes
# whose targets are complex structural elements (can reference multiple
# element types) and cannot be reliably resolved to a single definition class
# via the naming convention.

ODM_20_SKIP_ATTRS: list[str] = [
    "FileOID",
    "PriorFileOID",
    # Workflow transition OIDs: source/target can be any structural element
    "StartOID",
    "SourceOID",
    "TargetOID",
    "EndOID",
    # Duration timing: StructuralElementOID can reference multiple types
    "StructuralElementOID",
    # Relative timing: predecessor/successor OIDs span multiple element types
    "PredecessorOID",
    "SuccessorOID",
    # Target transition: references Transition (which itself has transitions)
    "TargetTransitionOID",
]
ODM_20_SKIP_ELEMS: list[str] = ["ODM"]

# ---------------------------------------------------------------------------
# ARM 1.0 (Analysis Results Metadata)
# ---------------------------------------------------------------------------
# ARM extends Define-XML 2.1 and inherits its skip configuration.
# Additionally, ParameterOID in AnalysisResult references an ItemDef
# but uses a non-standard naming pattern (not ending in "OID" of the
# target element type), so the dynamic generator handles it via the
# standard OIDRef detection.

ARM_10_SKIP_ATTRS: list[str] = [
    "FileOID",
    "PriorFileOID",
    "StudyOID",
    "MetaDataVersionOID",
    "ItemGroupOID",
]
ARM_10_SKIP_ELEMS: list[str] = [
    "ODM",
    "Study",
    "MetaDataVersion",
    "ItemGroupDef",
]


# ---------------------------------------------------------------------------
# Lookup helper
# ---------------------------------------------------------------------------

_CONFIGS: dict[str, tuple[list[str], list[str]]] = {
    "odm_1_3_2": (ODM_132_SKIP_ATTRS, ODM_132_SKIP_ELEMS),
    "define_2_0": (DEFINE_20_SKIP_ATTRS, DEFINE_20_SKIP_ELEMS),
    "define_2_1": (DEFINE_21_SKIP_ATTRS, DEFINE_21_SKIP_ELEMS),
    "odm_2_0": (ODM_20_SKIP_ATTRS, ODM_20_SKIP_ELEMS),
    "arm_1_0": (ARM_10_SKIP_ATTRS, ARM_10_SKIP_ELEMS),
}


def get_skip_config(model_package: str) -> tuple[list[str], list[str]]:
    """Return ``(skip_attrs, skip_elems)`` for *model_package*.

    Falls back to empty lists for unknown packages so that a
    :class:`~odmlib.oid_generator.DynamicOIDRef` can still be created for
    custom model packages.

    Args:
        model_package: Model package name, e.g. ``"odm_1_3_2"``.

    Returns:
        A ``(skip_attrs, skip_elems)`` tuple of lists.
    """
    skip_attrs, skip_elems = _CONFIGS.get(model_package, ([], []))
    # Return copies so callers can safely extend without mutating module state.
    return list(skip_attrs), list(skip_elems)
