# odmlib

[![CI](https://github.com/swhume/odmlib/actions/workflows/ci.yml/badge.svg)](https://github.com/swhume/odmlib/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/odmlib.svg)](https://badge.fury.io/py/odmlib)
[![Python versions](https://img.shields.io/pypi/pyversions/odmlib)](https://pypi.org/project/odmlib/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

A Python library for creating, parsing, and validating CDISC ODM (Operational Data Model)
documents and extensions including Define-XML, Dataset-XML, Dataset-JSON, CT-XML, and ARM.

## Supported Standards

| Standard | Package | Status |
|----------|---------|--------|
| ODM 1.3.2 | `odmlib.odm_1_3_2` | Stable |
| ODM 2.0 | `odmlib.odm_2_0` | Draft |
| Define-XML 2.0 | `odmlib.define_2_0` | Stable |
| Define-XML 2.1 | `odmlib.define_2_1` | Stable |
| Dataset-XML 1.0.1 | `odmlib.dataset_1_0_1` | Stable |
| CT-XML 1.1.1 | `odmlib.ct_1_1_1` | Stable |
| ARM 1.0 | `odmlib.arm_1_0` | Stable |
| Dataset-JSON v1.1 | `odmlib.dataset_json_1_1` | Stable |
| Dataset-JSON (legacy) | `odmlib.dataset_json` | Deprecated |

## Installation

```bash
pip install odmlib
```

For development:

```bash
git clone https://github.com/swhume/odmlib.git
cd odmlib
pip install -e ".[dev]"
```

With optional Pandas support:

```bash
pip install odmlib[dataframe]
```

## Loading Documents

### Load an ODM-XML file

```python
import odmlib.odm_loader as OL
import odmlib.loader as LD

loader = LD.ODMLoader(OL.XMLODMLoader())
loader.open_odm_document("study.xml")

# Load the full document tree
odm = loader.root()

# Or load just the MetaDataVersion (faster for large files)
mdv = loader.MetaDataVersion()

for item_group in mdv.ItemGroupDef:
    print(f"{item_group.OID}: {item_group.Name}")

# Find a specific element by attribute value
item = mdv.find("ItemDef", "OID", "IT.AGE")
print(item.DataType)
```

### Load an ODM-JSON file

```python
import odmlib.odm_loader as OL
import odmlib.loader as LD

loader = LD.ODMLoader(OL.JSONODMLoader())
loader.open_odm_document("study.json")
mdv = loader.MetaDataVersion()
```

### Load from a string

```python
import odmlib.odm_loader as OL
import odmlib.loader as LD

loader = LD.ODMLoader(OL.XMLODMLoader())
loader.load_odm_string(xml_string)
odm = loader.root()
```

### Load a Define-XML file

```python
import odmlib.define_loader as DL
import odmlib.loader as LD

# Define-XML 2.1 (default)
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
loader.open_odm_document("define.xml")
mdv = loader.MetaDataVersion()

for item_def in mdv.ItemDef:
    print(f"{item_def.OID}: {item_def.Name} ({item_def.DataType})")

# Find all value lists
vl = mdv.find("ValueListDef", "OID", "VL.AEDECOD")
```

### Load an ARM-extended Define-XML file

```python
import odmlib.arm_loader as AL
import odmlib.loader as LD

loader = LD.ODMLoader(AL.XMLArmLoader())
loader.open_odm_document("define-adam.xml")
mdv = loader.MetaDataVersion()

for rd in mdv.AnalysisResultDisplays:
    print(f"{rd.OID}: {rd.Name}")
    for ar in rd.AnalysisResult:
        print(f"  Result: {ar.OID} ({ar.AnalysisPurpose})")
```

## Creating Documents

### Create an ODM document programmatically

```python
import odmlib.odm_1_3_2.model as ODM
import odmlib.ns_registry as NS

# Register the namespace (required once before creating XML)
NS.NamespaceRegistry(prefix="odm",
    uri="http://www.cdisc.org/ns/odm/v1.3",
    is_default=True, is_reset=True)

# Build elements bottom-up
tt = ODM.TranslatedText(_content="Subject identifier", lang="en")
desc = ODM.Description(TranslatedText=[tt])
item_def = ODM.ItemDef(
    OID="IT.SUBJID", Name="SUBJID", DataType="text",
    Length=8, Description=desc
)

item_ref = ODM.ItemRef(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
igd = ODM.ItemGroupDef(
    OID="IG.DM", Name="Demographics", Repeating="No",
    ItemRef=[item_ref]
)

mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Version 1")
mdv.ItemGroupDef.append(igd)
mdv.ItemDef.append(item_def)

gv = ODM.GlobalVariables(
    StudyName=ODM.StudyName(_content="My Study"),
    StudyDescription=ODM.StudyDescription(_content="Phase II trial"),
    ProtocolName=ODM.ProtocolName(_content="PROT-001"),
)
study = ODM.Study(OID="S.001", GlobalVariables=gv, MetaDataVersion=[mdv])
odm = ODM.ODM(
    FileOID="F.001", FileType="Snapshot",
    CreationDateTime="2024-01-01T00:00:00", Study=[study]
)

odm.write_xml("study.xml")
odm.write_json("study.json")
```

### Use the fluent builder

The `ODMBuilder` provides a chainable API that tracks the current study,
MetaDataVersion, and ItemGroupDef context automatically.

```python
from odmlib.builder import ODMBuilder

odm = (ODMBuilder("odm_1_3_2")
    .set_file(FileOID="F.001", FileType="Snapshot",
              CreationDateTime="2024-01-01T00:00:00")
    .add_study(OID="S.001",
               study_name="My Study",
               study_description="Phase II trial",
               protocol_name="PROT-001")
    .add_metadata_version(OID="MDV.001", Name="Version 1")
    .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
    .add_item_def(OID="IT.SUBJID", Name="SUBJID", DataType="text", Length=8)
    .add_item_def(OID="IT.AGE", Name="AGE", DataType="integer")
    .add_code_list(
        OID="CL.SEX", Name="Sex", DataType="text",
        items=[
            {"CodedValue": "M", "Decode": "Male"},
            {"CodedValue": "F", "Decode": "Female"},
        ]
    )
    .build())

odm.write_xml("study.xml")
```

## Context Managers

Context managers load a document on entry and write it back on clean exit,
making read-modify-write workflows concise.

```python
from odmlib.context import open_odm, open_define

# Modify an ODM file in-place
with open_odm("study.xml") as odm:
    odm.FileOID = "F.002"
    mdv = odm.Study[0].MetaDataVersion[0]
    mdv.ItemGroupDef.append(new_igd)
# study.xml is overwritten automatically

# Write to a different output file
with open_odm("study.xml", output_file="study_updated.xml") as odm:
    odm.FileOID = "F.002"

# Define-XML (defaults to define_2_1 model)
with open_define("define.xml") as define:
    mdv = define.Study[0].MetaDataVersion[0]
    print(len(mdv.ItemDef))

# JSON format is auto-detected from the file extension
with open_odm("study.json") as odm:
    odm.FileOID = "F.002"
```

## Serialization

All odmlib elements support bidirectional conversion:

```python
# To/from XML
xml_string = item_def.to_xml_string()
xml_elem = item_def.to_xml()           # xml.etree.ElementTree.Element

# To/from JSON
json_string = mdv.to_json()
python_dict = mdv.to_dict()

# Write to file
odm.write_xml("output.xml")
odm.write_json("output.json")
```

## Validation

odmlib provides four independent validation layers.

### OID uniqueness and ref/def integrity

```python
from odmlib.oid_generator import create_oid_checker

checker = create_oid_checker("odm_1_3_2")
odm.verify_oids(checker)               # raises OdmlibOIDError on failure

# Find unreferenced definitions
orphans = odm.unreferenced_oids(checker)
```

### Cerberus conformance validation

```python
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema

validator = MetadataSchema()
odm.verify_conformance(validator)      # raises on failure
```

### XML schema (XSD) validation

```python
from odmlib.odm_parser import ODMSchemaValidator

validator = ODMSchemaValidator()                   # uses packaged ODM 1.3.2 XSD
validator.validate_file("study.xml")               # raises OdmlibSchemaValidationError on failure

# Custom schema or different standard/version
validator = ODMSchemaValidator(standard="define", version="2.1")
```

### Combined validation with error collection

Collect all errors in a single pass instead of stopping at the first failure:

```python
from odmlib.oid_generator import create_oid_checker

checker = create_oid_checker("odm_1_3_2")
errors = odm.validate(collect_errors=True, oid_checker=checker)
for err in errors:
    print(err)
```

### Element ordering

```python
try:
    odm.verify_order()
except OdmlibElementOrderError:
    odm.reorder_object()    # fix ordering automatically (issues a warning)
```

## OID Index Lookup

Build an index for fast OID lookups across the entire document tree:

```python
idx = odm.build_oid_index()
elements = idx.find_all("IT.AGE")    # returns list of odmlib objects with that OID
```

## Finding Elements

```python
# First match
item = mdv.find("ItemDef", "OID", "IT.AGE")

# All matches
text_items = mdv.find_all("ItemDef", "DataType", "text")

# Multi-attribute match
item = mdv.find_by("ItemDef", DataType="integer", Length=4)
```

## Dataset-JSON

```python
from odmlib.dataset_json_1_1 import DatasetJSON, Column

ds = DatasetJSON(
    datasetJSONVersion="1.1.0",
    fileOID="F.DS.001",
    creationDateTime="2024-01-01T00:00:00",
    datasetJSONCreationDateTime="2024-01-01T00:00:00",
    records=3,
    name="DM",
    label="Demographics",
)
ds.columns = [
    Column(itemOID="IT.DM.SUBJID", name="SUBJID", label="Subject ID",
           dataType="string", targetDataType="string"),
    Column(itemOID="IT.DM.AGE", name="AGE", label="Age",
           dataType="integer", targetDataType="integer"),
]
ds.rows = [["SUBJ-001", 34], ["SUBJ-002", 28], ["SUBJ-003", 45]]

ds.write_json("dm.json")
```

Convert between Dataset-XML and Dataset-JSON:

```python
from odmlib.dataset_json_1_1 import dataset_xml_to_dataset_json, dataset_json_to_dataset_xml

dataset_json = dataset_xml_to_dataset_json("dm.xml", "define.xml")
dataset_json.write_json("dm.json")
```

Flatten Define-XML 2.1 metadata into Dataset-JSON datasets:

```python
from odmlib.dataset_json_1_1 import DefineFlattener

flattener = DefineFlattener("define.xml")
datasets = flattener.flatten()           # dict of dataset name → DatasetJSON
datasets["IG"].write_json("ig.json")
```

## Pandas Integration

Requires `pip install odmlib[dataframe]`.

```python
from odmlib.dataframe import (
    metadata_to_dataframe,
    clinical_data_to_dataframe,
    define_metadata_to_dataframes,
    dataset_json_to_dataframe,
    dataframe_to_items,
)

# Export all ItemDef metadata as a DataFrame
df = metadata_to_dataframe(mdv, "ItemDef")
print(df[["OID", "Name", "DataType", "Length"]].to_string())

# Flatten ClinicalData to a tabular DataFrame
df = clinical_data_to_dataframe(odm)

# Flatten all Define-XML metadata tables at once
dfs = define_metadata_to_dataframes("define.xml")
print(dfs["variables"].head())

# Convert Dataset-JSON to DataFrame
df = dataset_json_to_dataframe(ds)

# Create odmlib elements from a DataFrame
items = dataframe_to_items(df, ODM.ItemDef)
```

## Namespace Management

When creating documents from scratch, register namespaces before writing XML.
The `is_reset=True` flag clears any previously registered namespaces.

```python
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="odm",
    uri="http://www.cdisc.org/ns/odm/v1.3",
    is_default=True, is_reset=True)

# For Define-XML, add additional namespaces
NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=odmlib --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_odm_loader.py -v
```

## Documentation

- [API Reference](https://swhume.github.io/odmlib)
- [Example Programs](https://github.com/swhume/odmlib_examples)
- [CDISC ODM Specification](https://www.cdisc.org/standards/data-exchange/odm)

## Dependencies

- [xmlschema](https://pypi.org/project/xmlschema/) — XML Schema validation
- [validators](https://pypi.org/project/validators/) — email/URL validation
- [Cerberus](https://docs.python-cerberus.org/) — conformance schema validation
- [pathvalidate](https://pypi.org/project/pathvalidate/) — filename validation

**Optional:**

- [pandas](https://pandas.pydata.org/) ≥ 1.5 — DataFrame integration (`pip install odmlib[dataframe]`)

## Known Limitations

- No `ItemData[Type]` support (typed item data elements, deprecated in ODM v2.0)
- No `ds:Signature` support (digital signatures)
- Single `MetaDataVersion` per load by default (use `idx` parameter for others)
- ODM v2.0 implementation is still draft

## License

[MIT](LICENSE.md)

## Contributing

Issues and pull requests are welcome at
[https://github.com/swhume/odmlib/issues](https://github.com/swhume/odmlib/issues).
