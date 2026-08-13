# Dataset-JSON 1.1 and conversions

Dataset-JSON 1.1 (`dataset_json_1_1`) carries actual dataset *data* — one dataset per file —
alongside enough metadata to interpret it, with foreign keys back to ODM/Define-XML. odmlib
models it with the `DatasetJSON`, `Column`, and `SourceSystem` classes (all importable from
the top-level `odmlib` namespace).

## The `DatasetJSON` object

```python
from odmlib import DatasetJSON, Column, SourceSystem

ds = DatasetJSON(
    # required:
    datasetJSONCreationDateTime="2026-06-30T00:00:00",
    datasetJSONVersion="1.1.0",
    itemGroupOID="IG.DM",          # FK to a Define-XML ItemGroupDef
    records=2,
    name="DM",
    label="Demographics",
    # common optional metadata:
    fileOID="DJ.DM.001",
    studyOID="ST.001",             # FK to ODM/Define Study
    metaDataVersionOID="MDV.1",    # FK to MetaDataVersion
    metaDataRef="define.xml",      # URI to the metadata file
    originator="Hume Data Labs",
    sourceSystem=SourceSystem(name="odmlib", version="0.2.1"),
    # column definitions (order defines the row value order):
    columns=[
        Column(itemOID="IT.USUBJID", name="USUBJID", label="Unique Subject ID", dataType="string"),
        Column(itemOID="IT.AGE",     name="AGE",     label="Age",               dataType="integer"),
    ],
    # rows: list of arrays, each matching column order; None == missing:
    rows=[
        ["SUBJ-001", 42],
        ["SUBJ-002", None],
    ],
)
ds.write_ndjson("dm.ndjson")     # NDJSON is the Dataset-JSON v1.1 wire format
ds.write_json("dm.json")         # plain JSON is also available
ds.column_names                  # -> ["USUBJID", "AGE"]
```

The Dataset-JSON v1.1 specification serializes as **NDJSON** (newline-delimited JSON:
a metadata header line followed by one line per data row), so `write_ndjson` /
`read_ndjson` are the primary I/O. `write_json` / `to_dict` / `from_dict` handle a single
plain-JSON object when that is more convenient.

Field-name reminders specific to Dataset-JSON (note the camelCase, distinct from ODM's
PascalCase): `datasetJSONCreationDateTime`, `datasetJSONVersion`, `itemGroupOID`,
`metaDataVersionOID`, `studyOID`, `fileOID`. `Column` uses `itemOID`, `name`, `label`,
`dataType` (and optional `length`, `keySequence`, `targetDataType`, etc.). `records` must
equal `len(rows)` — set it accordingly. Metadata-only files are allowed with `records=0` and
no `rows`.

## Loading a Dataset-JSON file

Dataset-JSON has its own root class (`DatasetJSON`), not `<ODM>`, so read it with the
purpose-built classmethods rather than the generic ODM loader:

```python
from odmlib import DatasetJSON
ds = DatasetJSON.read_ndjson("dm.ndjson")        # NDJSON (the v1.1 wire format)

import json
ds = DatasetJSON.from_dict(json.load(open("dm.json", encoding="utf-8")))   # plain JSON
print(ds.name, ds.label, len(ds.rows), ds.column_names)
```

## Conversions

Two helpers convert between Dataset-XML (the older XML transport, `dataset_1_0_1`) and
Dataset-JSON. Both are importable from the top-level `odmlib` namespace.

```python
from odmlib import dataset_xml_to_dataset_json, dataset_json_to_dataset_xml

# Dataset-XML ODM object -> {dataset_name: DatasetJSON}
#   define_mdv (optional): a loaded Define-XML MetaDataVersion used to enrich column
#   metadata (labels, data types) that Dataset-XML alone does not carry.
result = dataset_xml_to_dataset_json(odm_obj, define_mdv=None)   # -> dict[str, DatasetJSON]

# DatasetJSON -> Dataset-XML model object
xml_model = dataset_json_to_dataset_xml(
    dataset_json,            # a DatasetJSON instance
    dataset_xml_model,       # the target Dataset-XML model module/object
    study_oid=None,
    mdv_oid=None,
)
```

Passing a `define_mdv` to `dataset_xml_to_dataset_json` is what lets the resulting columns
carry proper labels and types — Dataset-XML by itself is thin on metadata, so load the
matching Define-XML first and hand its `MetaDataVersion` in.

## Bridging Define-XML metadata: `DefineFlattener`

The most useful conversion in practice turns a Define-XML 2.1 object tree into the flat,
column-oriented datasets that tabular tools want. `DefineFlattener` does this directly:

```python
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib.dataset_json_1_1.define_flattener import DefineFlattener   # also: odmlib.DefineFlattener

loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1",
                                         ns_uri="http://www.cdisc.org/ns/def/v2.1"))
loader.open_odm_document("defineV21-SDTM.xml")
odm = loader.root()

flattener = DefineFlattener(odm)
datasets = flattener.flatten_all()        # dict of name -> DatasetJSON (study, datasets,
                                          # variables, valuelevel, codelists, dictionaries, …)
for name, ds in datasets.items():
    print(f"{name}: {ds.records} rows, {len(ds.columns)} columns")

paths = flattener.write_all("out/")       # write each flattened dataset to a file
```

Each value in `datasets` is a `DatasetJSON`, so you can inspect it with `column_names` /
`rows` / `to_dict()` or write it out. `DefineBuilder` goes the other direction, assembling
Define-XML structures programmatically. This area is evolving toward v1.0 — introspect the
installed classes for current methods.
