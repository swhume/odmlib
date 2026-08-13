"""Create, write, and read back a Dataset-JSON v1.1 file.

Dataset-JSON carries one dataset per file: file/study metadata, Column definitions, and
rows as arrays in column order, with foreign keys (studyOID, metaDataVersionOID,
itemGroupOID) back to ODM/Define-XML. The v1.1 wire format is NDJSON.

Demonstrates:
  * building a DatasetJSON with Column definitions and row arrays
  * write_ndjson + read_ndjson round-trip (the v1.1 format)
  * keeping records == len(rows)

Run:  python dataset_json_roundtrip.py
Writes: ./odmlib_skill_output/dm.ndjson (under the current working directory)
"""
import os
import warnings

import odmlib
from odmlib import DatasetJSON, Column, SourceSystem

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "dm.ndjson")


def build_dataset():
    rows = [
        ["SUBJ-001", 42],
        ["SUBJ-002", None],     # None == missing value
    ]
    return DatasetJSON(
        datasetJSONCreationDateTime="2026-06-30T00:00:00",
        datasetJSONVersion="1.1.0",
        fileOID="DJ.DM.001",
        studyOID="ST.001",
        metaDataVersionOID="MDV.1",
        metaDataRef="define.xml",
        originator="Hume Data Labs",
        sourceSystem=SourceSystem(name="odmlib", version=odmlib.__version__),
        itemGroupOID="IG.DM",
        name="DM",
        label="Demographics",
        records=len(rows),
        columns=[
            Column(itemOID="IT.USUBJID", name="USUBJID",
                   label="Unique Subject Identifier", dataType="string"),
            Column(itemOID="IT.AGE", name="AGE", label="Age", dataType="integer"),
        ],
        rows=rows,
    )


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)

    ds = build_dataset()
    ds.write_ndjson(OUT)
    print(f"Wrote {OUT} ({os.path.getsize(OUT)} bytes)")
    print("columns:", ds.column_names, "| records:", ds.records)

    # Read it back. Dataset-JSON has its own root class, so use read_ndjson
    # (not the generic ODM loader, which expects an <ODM> root).
    ds2 = DatasetJSON.read_ndjson(OUT)
    print("read back: name =", ds2.name, "| label =", ds2.label,
          "| rows =", len(ds2.rows), "| first row =", ds2.rows[0])
