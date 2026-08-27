"""Create an ODM 1.3.2 document from scratch — two equivalent styles.

Demonstrates:
  * the ODMBuilder fluent API (recommended default for generation)
  * equivalent direct model construction (full control)
  * validating before writing (order + OID + conformance)

Run:  python create_odm.py
Writes: ./odmlib_skill_output/created_odm.xml (under the current working directory)
"""
import os
import warnings

import odmlib
from odmlib import ODMBuilder, create_oid_checker
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)


def build_with_builder():
    """Fluent builder — chainable, keeps children in schema order for you."""
    odm = (
        ODMBuilder(model_package="odm_1_3_2")
        .set_file(
            FileOID="ODM.VS.001",
            FileType="Snapshot",
            CreationDateTime="2026-06-30T00:00:00",
            Granularity="Metadata",
            ODMVersion="1.3.2",
            Originator="Hume Data Labs",
        )
        .add_study("ST.VS", "Vital Signs Demo", "A small demo study", "PROTO-VS")
        .add_metadata_version(OID="MDV.1", Name="Vital Signs MDV")
        .add_item_group_def(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
        .add_item_ref(ItemOID="IT.VSORRES", Mandatory="Yes", OrderNumber=1)
        .add_item_ref(ItemOID="IT.VSPOS", Mandatory="No", OrderNumber=2)
        .add_item_def(OID="IT.VSORRES", Name="Result", DataType="float")
        .with_question("What was the measured result?")
        .add_item_def(OID="IT.VSPOS", Name="Position", DataType="text", Length=8)
        .with_codelist_ref("CL.POS")
        # add_code_list builds CodeListItems from items=; include "Decode" for a
        # decoded codelist, omit it for an EnumeratedItem-style list.
        .add_code_list(
            OID="CL.POS", Name="Position", DataType="text",
            items=[
                {"CodedValue": "SITTING", "Decode": "Sitting"},
                {"CodedValue": "STANDING", "Decode": "Standing"},
                {"CodedValue": "SUPINE", "Decode": "Supine"},
            ],
        )
        .build()
    )
    return odm


def build_with_model():
    """Direct construction — instantiate model classes and assemble the tree."""
    import odmlib.odm_1_3_2.model as ODM

    odm = ODM.ODM(
        FileOID="ODM.VS.001",
        FileType="Snapshot",
        CreationDateTime="2026-06-30T00:00:00",
        Granularity="Metadata",
        ODMVersion="1.3.2",
        Originator="Hume Data Labs",
    )
    odm.Study.append(ODM.Study(OID="ST.VS"))
    odm.Study[0].GlobalVariables = ODM.GlobalVariables(
        StudyName=ODM.StudyName(_content="Vital Signs Demo"),
        StudyDescription=ODM.StudyDescription(_content="A small demo study"),
        ProtocolName=ODM.ProtocolName(_content="PROTO-VS"),
    )
    odm.Study[0].MetaDataVersion.append(
        ODM.MetaDataVersion(OID="MDV.1", Name="Vital Signs MDV")
    )
    mdv = odm.Study[0].MetaDataVersion[0]
    igd = ODM.ItemGroupDef(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
    igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.VSORRES", Mandatory="Yes", OrderNumber=1))
    mdv.ItemGroupDef.append(igd)
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.VSORRES", Name="Result", DataType="float"))
    return odm


def validate(odm):
    errors = odm.validate(
        collect_errors=True,
        oid_checker=create_oid_checker("odm_1_3_2"),
        conformance_checker=MetadataSchema(),
    )
    if errors:
        print(f"  {len(errors)} validation error(s):")
        for e in errors:
            print("   -", str(e).splitlines()[0])
        return False
    print("  valid (order + OID integrity + conformance)")
    return True


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)

    print("Builder style:")
    odm_a = build_with_builder()
    validate(odm_a)

    print("Direct-model style:")
    odm_b = build_with_model()
    validate(odm_b)

    out = os.path.join(OUTDIR, "created_odm.xml")
    odm_a.write_xml(out)
    print(f"Wrote {out} ({os.path.getsize(out)} bytes)")

    # XSD validation against the schema odmlib bundles (no download needed).
    from odmlib.odm_parser import ODMSchemaValidator
    validator = ODMSchemaValidator(standard="odm", version="1.3.2")
    schema_errors = list(validator.xsd.iter_errors(out))
    if schema_errors:
        print(f"  XSD: {len(schema_errors)} error(s)")
        for e in schema_errors[:5]:
            print("   -", e.reason)
    else:
        print("  XSD: valid against bundled ODM 1.3.2 schema")
