"""Load, modify, and save an ODM file with the context-manager facade.

Writing is OPT-IN: since 0.2.1 a bare open_odm(path) loads read-only and writes
nothing on exit. There are two ways to ask for a write.

Demonstrates:
  * open_odm(...) with no write argument -> read-only, the file is never touched
  * write_on_exit=False -> the same, stated explicitly
  * output_file=... -> write the modified document somewhere other than the input
  * write_on_exit=True -> update the input file IN PLACE

Run:  python read_modify_write.py   (creates its own input first)
Writes: ./odmlib_skill_output/rmw_input.xml, ./odmlib_skill_output/rmw_output.xml,
        ./odmlib_skill_output/rmw_inplace.xml
"""
import os
import shutil
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
INPLACE = os.path.join(OUTDIR, "rmw_inplace.xml")


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

    # 1. Read-only by DEFAULT: no write argument at all, so nothing is written.
    #    The edit below is deliberately discarded on exit to prove the point.
    before_mtime = os.path.getmtime(INPUT)
    with open_odm(INPUT) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        print("Before:", len(mdv.ItemGroupDef), "ItemGroupDef;",
              "FileOID =", odm.FileOID)
        odm.FileOID = "ODM.RMW.DISCARDED"      # goes nowhere: default is read-only
    assert os.path.getmtime(INPUT) == before_mtime, "default must not write"

    with open_odm(INPUT, write_on_exit=False) as odm:   # same thing, said explicitly
        assert odm.FileOID == "ODM.RMW", "step 1 must not have been persisted"

    # 2. Modify and save to a NEW file via output_file (input stays untouched).
    import odmlib.odm_1_3_2.model as ODM
    with open_odm(INPUT, output_file=OUTPUT) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        mdv.ItemGroupDef.append(
            ODM.ItemGroupDef(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
        )
        odm.FileOID = "ODM.RMW.UPDATED"

    # 3. Confirm the change landed in the output file.
    with open_odm(OUTPUT, write_on_exit=False) as odm:
        mdv = odm.Study[0].MetaDataVersion[0]
        names = [igd.Name for igd in mdv.ItemGroupDef]
        print("After: ", len(mdv.ItemGroupDef), "ItemGroupDef", names,
              "; FileOID =", odm.FileOID)
    print(f"Wrote {OUTPUT} ({os.path.getsize(OUTPUT)} bytes); input unchanged")

    # 4. In-place update: write_on_exit=True writes back to the file it opened.
    #    Copy first so the pristine input survives for re-runs.
    shutil.copyfile(INPUT, INPLACE)
    with open_odm(INPLACE, write_on_exit=True) as odm:
        odm.FileOID = "ODM.RMW.INPLACE"

    with open_odm(INPLACE) as odm:                     # read-only re-read to confirm
        print("In place:", INPLACE, "-> FileOID =", odm.FileOID)
    assert odm.FileOID == "ODM.RMW.INPLACE"
