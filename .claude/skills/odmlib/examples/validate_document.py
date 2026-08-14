"""Validate ODM/Define documents, and see what each check catches.

Demonstrates:
  * validate(collect_errors=True, oid_checker=..., conformance_checker=...)
  * how dangling OID references are caught (the most common real defect)
  * reading the rich error messages (element path + hint)
  * that collect_errors=True enumerates EVERY defect, not one per layer:
    broken_document() plants three independent OID defects and all three are
    reported in a single pass
  * max_errors=N to cap the list on a badly broken document
  * fail-fast mode (the default) still raises on the first problem
  * XSD validation against the bundled CDISC schemas -- a separate layer that
    catches structural defects validate() does not

validate() is both a gate and a report. For the parts it does NOT cover --
orphan OIDs, usage lookup, OID inventory -- see report_oid_integrity.py.

Run:  python validate_document.py
"""
import warnings

import odmlib
from odmlib import (
    ODMBuilder,
    create_oid_checker,
    OdmlibError,
    OdmlibErrorLimitError,
)
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema


def good_document():
    """An ItemRef whose ItemOID has a matching ItemDef — clean."""
    return (
        ODMBuilder(model_package="odm_1_3_2")
        .set_file(FileOID="ODM.OK", FileType="Snapshot",
                  CreationDateTime="2026-06-30T00:00:00", Granularity="Metadata",
                  ODMVersion="1.3.2", Originator="Hume Data Labs")
        .add_study("ST.1", "Demo", "Demo study", "PROTO-1")
        .add_metadata_version(OID="MDV.1", Name="MDV")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber="1")
        .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
        .build()
    )


def broken_document():
    """THREE independent OID defects — all three are reported in one pass.

    1. ItemRef -> IT.MISSING1, which no ItemDef defines (dangling)
    2. ItemRef -> IT.MISSING2, which no ItemDef defines (dangling)
    3. IT.DUP defined twice (duplicate)

    Duplicates are checked before references, but a duplicate no longer aborts
    the traversal, so the dangling refs are found in the same run.
    """
    return (
        ODMBuilder(model_package="odm_1_3_2")
        .set_file(FileOID="ODM.BAD", FileType="Snapshot",
                  CreationDateTime="2026-06-30T00:00:00", Granularity="Metadata",
                  ODMVersion="1.3.2", Originator="Hume Data Labs")
        .add_study("ST.2", "Demo", "Demo study", "PROTO-2")
        .add_metadata_version(OID="MDV.2", Name="MDV")
        .add_item_group_def(OID="IG.X", Name="X", Repeating="No")
        .add_item_ref(ItemOID="IT.MISSING1", Mandatory="Yes", OrderNumber="1")
        .add_item_ref(ItemOID="IT.MISSING2", Mandatory="Yes", OrderNumber="2")
        .add_item_def(OID="IT.DUP", Name="A", DataType="integer")
        .add_item_def(OID="IT.DUP", Name="B", DataType="integer")
        .build()
    )


def report(label, odm, planted=None, max_errors=None):
    """Collect-mode validation.

    A FRESH checker every call — a checker accumulates OIDs and is single-use per
    document (checker.reset() is the alternative).
    """
    errors = odm.validate(
        collect_errors=True,
        oid_checker=create_oid_checker("odm_1_3_2"),
        conformance_checker=MetadataSchema(),
        max_errors=max_errors,
    )
    if not errors:
        print(f"{label}: VALID")
        return
    print(f"{label}: {len(errors)} error(s) returned")
    for e in errors:
        for line in str(e).splitlines():
            print("   ", line)
    if planted is not None:
        truncated = isinstance(errors[-1], OdmlibErrorLimitError)
        found = len(errors) - 1 if truncated else len(errors)
        note = f"capped at max_errors={max_errors}" if truncated else "all reported"
        print(f"    ^ {planted} defects planted, {found} reported — {note}")


def fail_fast(label, odm):
    """The default mode: raises the first problem, reports nothing else."""
    try:
        odm.validate(oid_checker=create_oid_checker("odm_1_3_2"))
    except OdmlibError as e:
        print(f"{label}: raised {type(e).__name__} — {str(e).splitlines()[0]}")
    else:
        print(f"{label}: VALID")


def schema_validate():
    """XSD validation: a different layer, catching different defects.

    validate() checks the object model (OIDs, conformance, order). XSD checks
    the *serialized* file against the official CDISC schema, which odmlib
    bundles -- nothing to download. Select one by (standard, version):

        ("odm","1.3.2")  ("odm","2.0")  ("define","2.0")  ("define","2.1")
        ("arm","1.0")    ARM 1.0 inside a Define-XML 2.0 document
        ("arm","1.0-define2.1")  ARM 1.0 inside a Define-XML 2.1 document

    ARM has two entries because it layers onto Define-XML and the two
    Define-XML versions use different def: namespace URIs; they are not
    interchangeable. Use "1.0-define2.1" with the arm_1_0 model package.

    Both standard and version are required -- there is no default. For a
    custom or local schema, pass xsd_file="/path/to/schema.xsd" instead.
    """
    import os
    import tempfile
    from odmlib.odm_parser import ODMSchemaValidator

    validator = ODMSchemaValidator(standard="odm", version="1.3.2")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "good.xml")
        good_document().write_xml(path)

        # validate_file() returns None on success and raises on failure
        validator.validate_file(path)
        print("good_document: XSD VALID")

        # iter_errors() enumerates every schema problem instead of raising on
        # the first -- the better choice when producing a report
        errors = list(validator.xsd.iter_errors(path))
        print(f"good_document: {len(errors)} schema errors")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)

    print("\n-- collect_errors=True: every defect --")
    report("good_document", good_document())
    report("broken_document", broken_document(), planted=3)

    print("\n-- max_errors: cap the list --")
    report("broken_document", broken_document(), planted=3, max_errors=2)

    print("\n-- collect_errors=False (default): fail fast --")
    fail_fast("good_document", good_document())
    fail_fast("broken_document", broken_document())

    print("\n-- XSD validation against the bundled CDISC schema --")
    schema_validate()
