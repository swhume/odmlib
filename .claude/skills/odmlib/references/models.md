# odmlib model packages

A *model package* is a Python module tree under `odmlib.<package>.model` whose classes
mirror the elements of one CDISC standard at one version. Picking the right package is the
first decision in any task. This file covers the packages this skill targets — ODM 1.3.2,
ODM 2.0, Define-XML 2.1, Dataset-JSON 1.1, and ARM 1.0 — plus the structural differences
that cause the most trouble.

## Quick selection

| You are working with… | Use package | Load with |
|---|---|---|
| An ODM 1.3.2 study/CRF metadata or clinical data file | `odm_1_3_2` | `open_odm` / `XMLODMLoader` |
| An ODM 2.0 (draft) file | `odm_2_0` | `open_odm(model_package="odm_2_0")` / `XMLODMLoader` |
| A Define-XML 2.1 data definition (`define.xml`) | `define_2_1` | `open_define` / `XMLDefineLoader(model_package="define_2_1")` |
| A Dataset-JSON 1.1 dataset | `dataset_json_1_1` | `DatasetJSON` model / JSON loader |
| Analysis Results Metadata (ARM 1.0) | `arm_1_0` | `XMLArmLoader` |

Other packages exist (`define_2_0`, `ct_1_1_1`, `dataset_1_0_1` for Dataset-XML) and load
the same way; they are simply outside this skill's primary scope.

## One rule that catches everyone: `Study`/`MetaDataVersion` shape

The single biggest portability trap between packages: whether `Study` and `MetaDataVersion`
are lists or single objects.

| Model | `Study` | `MetaDataVersion` | Access |
|---|---|---|---|
| `odm_1_3_2`, `odm_2_0` | list | list | `odm.Study[0].MetaDataVersion[0]` |
| `define_2_1`, `arm_1_0` | single object | single object | `define.Study.MetaDataVersion` |

ODM allows multiple studies and metadata versions per file, so both are lists. Define-Xml
and ARM describe exactly one study/version, so both are plain objects — indexing them with
`[0]` raises. Children *within* an MDV (`ItemGroupDef`, `ItemDef`, `CodeList`, …) are lists
in every model.

## ODM 1.3.2 (`odm_1_3_2`) — the default

The reference model. Study identity is carried in a `GlobalVariables` element:

```python
import odmlib.odm_1_3_2.model as ODM
study = ODM.Study(OID="ST.1")
study.GlobalVariables = ODM.GlobalVariables(
    StudyName=ODM.StudyName(_content="My Study"),
    StudyDescription=ODM.StudyDescription(_content="…"),
    ProtocolName=ODM.ProtocolName(_content="PROTO-1"),
)
```

Common metadata classes: `ODM`, `Study`, `GlobalVariables`, `BasicDefinitions`,
`MeasurementUnit`, `MetaDataVersion`, `Protocol`, `StudyEventDef`, `StudyEventRef`,
`FormDef`, `FormRef`, `ItemGroupDef`, `ItemGroupRef`, `ItemDef`, `ItemRef`, `CodeList`,
`CodeListItem`, `EnumeratedItem`, `Decode`, `MethodDef`, `ConditionDef`, `RangeCheck`,
`Alias`, `Description`, `Question`, `TranslatedText`, `CodeListRef`, `MeasurementUnitRef`.
Clinical-data classes (`ClinicalData`, `SubjectData`, `ItemData`, …) also exist; the
metadata side is the best-tested.

Note (documented library limitation): the packaged ODM 1.3.2 model does not include
`ItemData[Type]` or `ds:Signature`.

## ODM 2.0 draft (`odm_2_0`) — structurally different

ODM 2.0 is a draft and differs from 1.3.2 in ways that break naive code reuse:

- **No `GlobalVariables`.** `StudyName` and `ProtocolName` are scalar attributes on
  `Study`, and the study description is an object-valued `Description` element.
- **No `FormDef`/`FormRef`** in the same shape — study structure is modeled via
  `StudyStructure`, `Epoch`, `Arm`, `WorkflowRef`, etc.
- Adds elements like `StudyStructure`, `Arm`, `Epoch`, `Include`, `Coding`, `Definition`,
  `Prompt`, `CRFCompletionInstructions`, `ImplementationNotes`, `SourceItems`.

The `ODMBuilder` constructs the correct shape for whichever package you pass, so prefer the
builder when generating ODM 2.0. If you construct raw objects, do not copy a 1.3.2 study
skeleton — build the 2.0 shape. Because 2.0 is a draft, expect it to evolve; confirm
element availability by introspecting `odmlib.odm_2_0.model`.

## Define-XML 2.1 (`define_2_1`) — an ODM extension

Define-XML is ODM plus a `def:` namespace and Define-specific elements. Load it as
**Define**, not ODM, and remember `Study`/`MetaDataVersion` are single objects here:

```python
from odmlib.context import open_define
with open_define("define.xml") as define:                 # model_package="define_2_1" default
    mdv = define.Study.MetaDataVersion                    # single objects — no [0]
    print(len(mdv.ItemGroupDef), len(mdv.ItemDef), len(mdv.CodeList))
```

With the explicit loader, set the version — the Define loader's own default is `define_2_0`:

```python
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
```

Define-2.1-specific classes include: `ItemGroupDef`/`ItemDef` (extended with Define
attributes), `ValueListDef`, `ValueListRef`, `WhereClauseDef`, `WhereClauseRef`,
`CommentDef`, `MethodDef`, `Origin`, `CodeList` (with `ExternalCodeList`), `leaf`, `title`,
`DocumentRef`, `PDFPageRef`, `AnnotatedCRF`, `SupplementalDoc`, `Standards`/`Standard`,
`Class`/`SubClass`. Default `def:` namespace URI: `http://www.cdisc.org/ns/def/v2.1`.

## Dataset-JSON 1.1 (`dataset_json_1_1`)

One dataset per file. The root `DatasetJSON` object carries file/study metadata, a list of
`Column` definitions, and `rows` as arrays of values in column order. Foreign keys
(`studyOID`, `metaDataVersionOID`, `itemGroupOID`) point back at ODM/Define-XML. Required
fields: `datasetJSONCreationDateTime`, `datasetJSONVersion`, `itemGroupOID`, `records`,
`name`, `label`. See `dataset-json.md`.

## ARM 1.0 (`arm_1_0`)

Analysis Results Metadata layered on Define-XML. Adds `AnalysisResultDisplays`,
`ResultDisplay`, `AnalysisResult`, `AnalysisDatasets`/`AnalysisDataset`, `AnalysisVariable`,
`Documentation`, `ProgrammingCode`, `Code` on top of the Define-style `MetaDataVersion`
(so `Study`/`MetaDataVersion` are single objects, as in Define). Load through the same
`ODMLoader` facade with the ARM loader and its namespace:

```python
import odmlib.arm_loader as AL
import odmlib.loader as LD
loader = LD.ODMLoader(AL.XMLArmLoader(model_package="arm_1_0",
                                      ns_uri="http://www.cdisc.org/ns/arm/v1.0"))
loader.open_odm_document("definev21-adam.xml")
odm = loader.root()
mdv = odm.Study.MetaDataVersion
ard = mdv.AnalysisResultDisplays            # container; supports len()/index/iter
```

odmlib does **not** bundle an ARM XSD (the packaged Define-XML 2.1 schema doesn't declare
the `arm:` namespace), so schema-validate ARM only by pointing `ODMSchemaValidator` at an
ARM-aware schema via `xsd_file=`. The object-model + OID validation (`validate(...)`) needs
no schema files and works on ARM as on any model.

## Namespace URIs (for `ns_uri=` on explicit loaders)

- ODM 1.3.2: `http://www.cdisc.org/ns/odm/v1.3`
- Define-XML 2.1 (`def:`): `http://www.cdisc.org/ns/def/v2.1`
- CT-XML: `http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC`

The loaders derive these from the model package automatically when `ns_uri=None`; override
only for non-standard namespaces or custom extensions.

## Custom / proprietary extensions

odmlib is designed for extending these models. The pattern (see the `acme_odm_1_0` example
in the odmlib_examples repo) is a small local model package:

1. Register each custom namespace at import time:
   `odmlib.ns_registry.NamespaceRegistry(prefix="acme", uri="http://…")`.
2. Subclass the relevant model classes. The loader instantiates by class name and only
   recurses into child descriptors declared in a class's *own* `__dict__`, so each extension
   class must re-declare the base children it should carry (e.g. `Name = ODM.ItemDef.Name`),
   and add new attributes with `odmlib.typed.<Type>(namespace="acme")`.
3. Load with the extension package and `local_model=True`:
   `OL.XMLODMLoader(model_package="acme_odm_1_0", ns_uri=ODM_NS, local_model=True)` — this
   imports the model by name from the working directory rather than from inside odmlib.

For OID checking on an extension, pass `extra_skip_attrs` / `extra_skip_elems` to
`create_oid_checker` for attributes/elements that carry OID-shaped values but are not true
defs/refs. See `validation.md`.
