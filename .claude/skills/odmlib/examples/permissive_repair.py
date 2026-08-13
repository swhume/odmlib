"""Load a non-conformant file permissively, repair it, then validate strictly.

Strict loading (the default) refuses files that violate the standard. Permissive mode
lets you load a broken/legacy file to inspect and fix it. Permissive mode is for reading
and repairing — never for emitting output. Fix, return to strict, then validate.

Demonstrates:
  * writing a deliberately non-conformant file
  * loading it under permissive mode (would fail under strict)
  * repairing the issue and validating cleanly before re-writing

Run:  python permissive_repair.py
Writes: ./odmlib_skill_output/broken_input.xml, ./odmlib_skill_output/repaired.xml
"""
import os
import warnings

import odmlib
from odmlib import permissive, create_oid_checker
from odmlib.context import open_odm

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)
BROKEN = os.path.join(OUTDIR, "broken_input.xml")
REPAIRED = os.path.join(OUTDIR, "repaired.xml")


def write_broken_file():
    """Hand-write an ODM file missing a required attribute (Repeating on ItemGroupDef).

    This is exactly the kind of file hand-rolled markup produces and strict odmlib
    rejects. We write it as raw text on purpose to simulate a bad external input.
    """
    xml = """<?xml version="1.0" encoding="utf-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" FileOID="ODM.BROKEN" FileType="Snapshot"
     CreationDateTime="2026-06-30T00:00:00" Granularity="Metadata" ODMVersion="1.3.2"
     Originator="Hume Data Labs">
  <Study OID="ST.B">
    <GlobalVariables>
      <StudyName>Broken Demo</StudyName>
      <StudyDescription>Missing a required attribute</StudyDescription>
      <ProtocolName>PROTO-B</ProtocolName>
    </GlobalVariables>
    <MetaDataVersion OID="MDV.1" Name="MDV">
      <ItemGroupDef OID="IG.DM" Name="Demographics"/>
    </MetaDataVersion>
  </Study>
</ODM>
"""
    with open(BROKEN, "w", encoding="utf-8") as fh:
        fh.write(xml)


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)
    write_broken_file()

    # Permissive load so we can get the broken file into the object model at all.
    with permissive():
        with open_odm(BROKEN, write_on_exit=False) as odm:
            igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
            print("Loaded permissively. ItemGroupDef.Repeating =",
                  getattr(igd, "Repeating", None))

            # --- Repair: supply the missing required attribute ---
            igd.Repeating = "No"

    # Back in strict mode: validate the repaired tree before writing it out.
    errors = odm.validate(
        collect_errors=True,
        oid_checker=create_oid_checker("odm_1_3_2"),
    )
    if errors:
        print("Still invalid after repair:")
        for e in errors:
            print("   -", str(e).splitlines()[0])
    else:
        odm.write_xml(REPAIRED)
        print(f"Repaired and validated. Wrote {REPAIRED} ({os.path.getsize(REPAIRED)} bytes)")
