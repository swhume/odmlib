"""Build, round-trip, modify, and validate a Define-XML 2.1 document.

Define-XML is an ODM extension, but its model differs from ODM in a way that trips
everyone: in the define_2_1 (and arm_1_0) models, **Study and MetaDataVersion are single
objects, not lists** — so it is `define.Study.MetaDataVersion`, never `define.Study[0]`.
(In odm_1_3_2 / odm_2_0 they ARE lists.)

Demonstrates:
  * direct model construction of a Define-XML 2.1 document (the builder targets ODM)
  * the singular Study / MetaDataVersion access pattern
  * locating an ItemDef by OID with find(), then renaming it
  * object-model validation (order + OID integrity)
  * XSD validation against the Define-XML 2.1 schema that odmlib bundles (no download)

Run:  python define_roundtrip.py
Writes: ./odmlib_skill_output/define_built.xml, ./odmlib_skill_output/define_modified.xml
"""
import os
import warnings

import odmlib
import odmlib.define_2_1.model as DEF
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib import create_oid_checker
from odmlib.odm_parser import ODMSchemaValidator

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)
BUILT = os.path.join(OUTDIR, "define_built.xml")
MODIFIED = os.path.join(OUTDIR, "define_modified.xml")


def build_define():
    """Construct a minimal but schema-valid Define-XML 2.1 document."""
    odm = DEF.ODM(
        FileOID="DEF.DM.001", FileType="Snapshot",
        CreationDateTime="2026-06-30T00:00:00", ODMVersion="1.3.2",
        Context="Submission", Originator="Hume Data Labs",
    )
    # Study and MetaDataVersion are SINGLE objects in the define model — assign, don't append.
    study = DEF.Study(OID="ST.DM")
    study.GlobalVariables = DEF.GlobalVariables(
        StudyName=DEF.StudyName(_content="Define Demo"),
        StudyDescription=DEF.StudyDescription(_content="A minimal Define-XML 2.1 demo"),
        ProtocolName=DEF.ProtocolName(_content="PROTO-DM"),
    )
    mdv = DEF.MetaDataVersion(OID="MDV.1", Name="Data Definitions", DefineVersion="2.1.0")
    standards = DEF.Standards()
    standards.Standard = [DEF.Standard(OID="STD.SDTMIG", Name="SDTMIG", Type="IG",
                                       Version="3.4", Status="Final")]
    mdv.Standards = standards

    igd = DEF.ItemGroupDef(
        OID="IG.DM", Name="DM", Repeating="No", IsReferenceData="No",
        SASDatasetName="DM", Domain="DM", Purpose="Tabulation",
        Structure="One record per subject", ArchiveLocationID="LF.DM",
    )
    igd.ItemRef = [
        DEF.ItemRef(ItemOID="IT.DM.USUBJID", Mandatory="Yes", OrderNumber=1, KeySequence=1),
        DEF.ItemRef(ItemOID="IT.DM.AGE", Mandatory="No", OrderNumber=2),
    ]
    # ArchiveLocationID above points at a def:leaf ID, so the leaf must exist — it is
    # also a required child of a Define-XML ItemGroupDef. Omit it and OID validation
    # reports "OID LF.DM referenced in attribute ArchiveLocationID is not found."
    igd.leaf = DEF.leaf(
        ID="LF.DM",
        href="dm.xpt",
        title=DEF.title(_content="Demographics dataset"),
    )
    mdv.ItemGroupDef = [igd]
    mdv.ItemDef = [
        DEF.ItemDef(OID="IT.DM.USUBJID", Name="USUBJID", DataType="text", Length=20),
        DEF.ItemDef(OID="IT.DM.AGE", Name="AGE", DataType="integer", Length=3),
    ]
    study.MetaDataVersion = mdv          # SINGLE object
    odm.Study = study                    # SINGLE object
    return odm


def validate(odm, label):
    errors = odm.validate(collect_errors=True,
                          oid_checker=create_oid_checker("define_2_1"))
    print(f"  {label}: object-model {'valid' if not errors else f'{len(errors)} error(s)'}")
    return not errors


def schema_check(path):
    # odmlib bundles the Define-XML 2.1 schema — resolve it by (standard, version).
    validator = ODMSchemaValidator(standard="define", version="2.1")
    errs = list(validator.xsd.iter_errors(path))
    if errs:
        print(f"  XSD: {len(errs)} error(s) -> {errs[0].reason}")
    else:
        print("  XSD: valid against bundled Define-XML 2.1 schema")


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)

    # Build -> validate -> write -> schema-check
    odm = build_define()
    validate(odm, "built")
    odm.write_xml(BUILT)
    print(f"Wrote {BUILT} ({os.path.getsize(BUILT)} bytes)")
    schema_check(BUILT)

    # Reload with the explicit Define loader (singular Study/MetaDataVersion access)
    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
    loader.open_odm_document(BUILT)
    define = loader.root()
    mdv = define.Study.MetaDataVersion          # NOT define.Study[0]...
    print(f"Reloaded: Study={define.Study.OID}, MDV={mdv.OID}, "
          f"datasets={len(mdv.ItemGroupDef)}, variables={len(mdv.ItemDef)}")
    for igd in mdv.ItemGroupDef:
        print(f"  dataset {igd.OID} ({igd.Name}): {len(igd.ItemRef)} variables")

    # Modify: locate an ItemDef by OID with find(), rename it, write a new file
    age = mdv.find("ItemDef", "OID", "IT.DM.AGE")
    print(f"Renaming {age.OID}: {age.Name!r} -> 'AGE (years)'")
    age.Name = "AGE (years)"
    validate(define, "modified")
    define.write_xml(MODIFIED)
    schema_check(MODIFIED)
    print(f"Wrote {MODIFIED} ({os.path.getsize(MODIFIED)} bytes)")
