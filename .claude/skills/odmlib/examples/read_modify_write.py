"""Load, modify, and save an ODM file with the context-manager facade.

Demonstrates:
  * open_odm(...) load -> modify -> auto-save on clean exit
  * write_on_exit=False for read-only inspection (never touches the file)
  * output_file=... to write somewhere other than the input

Run:  python read_modify_write.py   (creates its own input first)
Writes: ./odmlib_skill_output/rmw_input.xml, ./odmlib_skill_output/rmw_output.xml
"""
import os
import warnings

import odmlib
from odmlib import ODMBuilder
from odmlib.context import open_odm

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)
INPUT = os.path.join(OUTDIR, "rmw_input.xml")
OUTPUT = os.path.join(OUTDIR, "rmw_output.xml")


def make_input():
    odm = (
        ODMBuilder(model_package="odm_1_3_2")
        .set_file(FileOID="ODM.RMW", FileType="Snapshot",
                  CreationDateTime="2026-06-30T00:00:00", Granularity="Metadata",
                  ODMVersion="1.3.2", Originator="Hume Data Labs")
        .add_study("ST.RMW", "Round Trip", "Load-modify-save demo", "PROTO-RMW")
        .add_metadata_version(OID="MDV.1", Name="MDV")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .build()
    )
    odm.write_xml(INPUT)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)
    make_input()

    # Read-only: write_on_exit=False guarantees the input is never modified.
    with open_odm(INPUT, write_on_exit=False) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        print("Before:", len(mdv.ItemGroupDef), "ItemGroupDef;",
              "FileOID =", odm.FileOID)

    # Modify and save to a NEW file via output_file (input stays untouched).
    import odmlib.odm_1_3_2.model as ODM
    with open_odm(INPUT, output_file=OUTPUT) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        mdv.ItemGroupDef.append(
            ODM.ItemGroupDef(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
        )
        odm.FileOID = "ODM.RMW.UPDATED"

    # Confirm the change landed in the output file.
    with open_odm(OUTPUT, write_on_exit=False) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        names = [igd.Name for igd in mdv.ItemGroupDef]
        print("After: ", len(mdv.ItemGroupDef), "ItemGroupDef", names,
              "; FileOID =", odm.FileOID)
    print(f"Wrote {OUTPUT} ({os.path.getsize(OUTPUT)} bytes); input unchanged")
