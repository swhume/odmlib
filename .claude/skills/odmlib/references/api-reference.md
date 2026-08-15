# odmlib API reference

Verified against odmlib 0.2.1. Names and signatures below are the public surface most
applications need. When in doubt, introspect the installed package
(`python -c "import odmlib, inspect; ..."`) rather than guessing.

## Contents

1. Top-level imports (`odmlib` namespace)
2. Model packages and importing model classes
3. Loading: facade and explicit loaders
4. Creating: the `ODMBuilder` fluent API
5. `ODMElement` — methods on every element
6. Validation: OID checker, conformance, XSD, modes
7. Exception hierarchy
8. Dataset-JSON and conversion helpers

---

## 1. Top-level imports (`odmlib` namespace)

These are re-exported from the package root for convenience:

```python
from odmlib import (
    ODMBuilder,                       # fluent document builder
    open_odm, open_define,            # context-manager facades (also in odmlib.context)
    permissive, ValidationMode,       # permissive loading
    get_mode, set_mode,               # lower-level mode control
    create_oid_checker, DynamicOIDRef,# OID integrity checking
    # exception hierarchy:
    OdmlibError, OdmlibValidationError, OdmlibRequiredAttributeError,
    OdmlibOIDError, OdmlibConformanceError, OdmlibElementOrderError,
    OdmlibErrorLimitError,            # appended when validate(max_errors=N) truncates
    OdmlibSchemaValidationError, OdmlibTypeError, OdmlibParsingError,
    OdmlibLoaderStateError, OdmlibSerializationError, OdmlibNamespaceError,
    OdmlibWarning, OdmlibDeprecationWarning, OdmlibInteroperabilityWarning,
    ErrorCollector,                   # error sink; ErrorCollector(max_errors=N) to cap
    ErrorReporting,                   # mixin: collecting-checker protocol
    is_collecting_checker,            # can this checker enumerate its errors?
    flatten_cerberus_errors,          # nested cerberus dict -> [(dotted_path, message)]
)

# Lazily exported (imported on first access) — Dataset-JSON and conversions:
from odmlib import (
    DatasetJSON, Column, SourceSystem,
    DefineFlattener, DefineBuilder,
    dataset_xml_to_dataset_json, dataset_json_to_dataset_xml,
)
```

`odmlib.__version__` holds the installed version.

## 2. Model packages and importing model classes

Model classes live under `odmlib.<package>.model`. Import the module and instantiate by
element name:

```python
import odmlib.odm_1_3_2.model as ODM
root = ODM.ODM(FileOID="ODM.1", FileType="Snapshot", CreationDateTime="2026-06-30T00:00:00",
               Granularity="Metadata", ODMVersion="1.3.2", Originator="Hume Data Labs")
root.Study.append(ODM.Study(OID="ST.1"))
```

Available packages: `odm_1_3_2`, `odm_2_0`, `define_2_0`, `define_2_1`, `dataset_json_1_1`,
`arm_1_0`, `ct_1_1_1`, `dataset_1_0_1`. See `models.md` for the key classes in each.

## 3. Loading: facade and explicit loaders

### Facade (`odmlib.context`)

```python
open_odm(input_file, output_file=None, model_package="odm_1_3_2",
         format=None, permissive=False, write_on_exit=True) -> ODMContext
open_define(input_file, output_file=None, model_package="define_2_1",
            format=None, permissive=False, write_on_exit=True) -> DefineContext
```

Used as context managers; `__enter__` returns the loaded root object. `format` auto-detects
from the extension (`.json` → JSON, else XML). On a clean exit the document is written to
`output_file` (defaults to `input_file`) unless `write_on_exit=False`. `permissive=True`
loads in fully permissive mode; pass a `ValidationMode` flag for targeted relaxation.

### Explicit loaders

```python
import odmlib.odm_loader    as OL   # XMLODMLoader, JSONODMLoader
import odmlib.define_loader as DL   # XMLDefineLoader, JSONDefineLoader
import odmlib.arm_loader    as AL   # XMLArmLoader, JSONArmLoader
import odmlib.loader        as LD   # ODMLoader facade wrapper

OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri=None, local_model=False)
OL.JSONODMLoader(model_package="odm_1_3_2")
DL.XMLDefineLoader(model_package="define_2_0", ns_uri=None, ...)   # set define_2_1 explicitly!
DL.JSONDefineLoader(model_package="define_2_0")
AL.XMLArmLoader(model_package="arm_1_0", ...)
```

`ns_uri=None` derives the namespace from the model package. `local_model=True` treats
`model_package` as a full importable module path (for custom/extension models).

Wrap a specialized loader in `LD.ODMLoader` and drive it:

```python
loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
loader.open_odm_document(filename)          # parse a file
loader.load_odm_string(odm_string)          # or parse from a string
odm   = loader.root()                       # root ODM object
study = loader.Study(idx=0)                 # a Study (object, not list)
mdv   = loader.MetaDataVersion(idx=0)       # a MetaDataVersion (object, not list)
obj   = loader.create_odmlib(doc, odm_key)  # load from an existing dict/Element
```

`ODMLoader` delegates unknown attributes to the wrapped loader, so loader-specific methods
remain reachable.

**Shape reminder:** on the loaded object, `Study` and `MetaDataVersion` are lists in
`odm_1_3_2`/`odm_2_0` (`odm.Study[0].MetaDataVersion[0]`) but single objects in
`define_2_1`/`arm_1_0` (`define.Study.MetaDataVersion`).

## 4. Creating: the `ODMBuilder` fluent API

`ODMBuilder(model_package="odm_1_3_2")`. Every `add_*`/`with_*`/`set_*` returns `self`;
`build()` returns the top-level `ODM` object. Selected methods:

```python
.set_file(**kwargs)                          # FileOID, FileType, CreationDateTime, ODMVersion, ...
.add_study(OID, study_name, study_description, protocol_name, **kwargs)   # positional first 4!
.add_metadata_version(**kwargs)              # OID, Name, ...
.add_item_group_def(**kwargs)                # OID, Name, Repeating, ...
.add_item_ref(**kwargs)                      # ItemOID, Mandatory, OrderNumber, ...
.add_item_def(**kwargs)                      # OID, Name, DataType, ...
.add_code_list(OID, Name, DataType, items=None, **kwargs)
   # items=[{"CodedValue": "M", "Decode": "Male"}]  -> CodeListItem (with Decode)
   # items=[{"CodedValue": "SYSBP"}]                -> EnumeratedItem (no Decode)
.add_method_def(OID, Name, Type, description, formal_expression=None, expression_context=None, **kwargs)
.add_condition_def(OID, Name, description=None, formal_expression=None, expression_context=None, **kwargs)
.add_measurement_unit(OID, Name, symbol, **kwargs)
.add_study_event_def(**kwargs) / .add_study_event_ref(**kwargs)
.add_form_def(**kwargs) / .add_form_ref(**kwargs)        # ODM 1.3.2 only
.add_item_group_ref(**kwargs)
.with_description(text, lang="en")           # attach to most-recent element
.with_question(text, lang="en")              # most-recent ItemDef
.with_codelist_ref(codelist_oid)             # most-recent ItemDef
.with_measurement_unit_ref(mu_oid)           # most-recent ItemDef (ODM 1.3.2)
.with_range_check(comparator, check_values, soft_hard=None, ErrorMessage=None, **kwargs)
.with_alias(context, name)
.attach(parent, element) / .attach_to_current(element)   # graft a pre-built element
.current                                     # PROPERTY (no parens): dict of active context
   # e.g. builder.current["mdv"], builder.current["item_def"], builder.current["form_def"]
.build()                                     # -> ODM object
```

`add_form_*` and `with_measurement_unit_ref` raise on ODM 2.0 (those constructs do not
exist there). The builder constructs the correct study shape per model automatically.

## 5. `ODMElement` — methods on every element

Every model object subclasses `ODMElement` and inherits:

```python
# Serialize
.to_json() -> str            .to_dict() -> dict
.to_xml(...) -> Element      .to_xml_string() -> str    # Element carries NO xmlns; string does
.write_xml(odm_file)         .write_json(odm_file)

# Search the subtree
.find(obj_name, attr, val)            # first match or None
.find_all(obj_name, attr, val)        # list of matches
.find_by(obj_name, **kwargs)          # first match by attribute kwargs, or None

# OID indexing / integrity
.build_oid_index() -> OIDIndex
.verify_oids(oid_checker) -> bool
.unreferenced_oids(oid_checker) -> dict[str, str]   # {orphan_oid: expected_ref_attr}

# Order and conformance
.verify_order() -> bool               # raises OdmlibElementOrderError if out of order
.reorder_object()                     # fix order in place (emits OdmlibWarning)
.verify_conformance(validator)        # Cerberus conformance

# Unified validation (preferred entry point)
.validate(collect_errors=False, oid_checker=None, conformance_checker=None, max_errors=None)
```

`validate()` runs `verify_order()` always, then `verify_oids` and `verify_conformance` if
those checkers are supplied. With `collect_errors=False` it fails fast and returns `True`;
with `collect_errors=True` it returns a list of `OdmlibError` (empty == valid).

**`collect_errors=True` returns every defect all three layers can find** — one error per
misordered element, per duplicate OID, per dangling/mistyped reference, and per failing
conformance field. The list length tracks the number of *defects*, so filter by exception
type rather than by index. `max_errors=N` caps it (enforced inside the layers) and appends
a final `OdmlibErrorLimitError`, giving at most `N + 1` entries; it is ignored in fail-fast
mode. Full OID enumeration needs a checker implementing the collecting protocol — the
`DynamicOIDRef` from `create_oid_checker()` does, the deprecated `OIDRef` classes do not
and contribute at most one error. See `references/validation.md`.

`unreferenced_oids()` is annotated `-> list` and its docstring says "list" — both are wrong,
it returns a `dict` mapping orphan OID → the ref attribute expected to point at it. How
noisy that dict is depends on the model package's `skip_elem` set (`odm_1_3_2` skips only
`ODM`, so structural OIDs appear; `define_2_1` skips `Study`/`MetaDataVersion`/
`ItemGroupDef` too).

### Serialization details

`to_xml_string()` takes **no arguments** in 0.2.1. It calls `to_xml()`, attaches the xmlns
declarations, and returns UTF-8 text **without** an XML declaration.

```python
.to_xml_string() -> str      # self-contained: default xmlns + every USED prefix; no <?xml ...?>
.to_xml(parent_elem=None, top_elem=None) -> Element   # NO xmlns anywhere; prefix-literal tags
.write_xml(odm_file, odm_writer=ODMWriter)            # <?xml ...?> + the to_xml_string() bytes
```

- **The Element from `to_xml()` is not a document.** Tags/attributes are literal
  `prefix:name` strings (`def:leaf`, `xlink:href`), not Clark notation, and no `xmlns` is
  attached. `ET.tostring()` on it produces markup that fails to parse for Define-XML
  (`ParseError: unbound prefix`) and parses into *no namespace* for ODM — where odmlib will
  re-load it with `FileOID` intact and every `Study` silently dropped. `ET.canonicalize()`
  also fails on it. Use `to_xml_string()`; use `to_xml()` only to graft fragments.
- **Byte relationship:** `write_xml()` output ==
  `b"<?xml version='1.0' encoding='UTF-8'?>\n" + to_xml_string().encode("utf-8")`. Both paths
  use `short_empty_elements=True` and identical attribute order.
- **Any element serializes**, not just the root — but see the namespace-binding caveat below.
- **XSD validation accepts a string**: `ODMSchemaValidator(...).xsd.iter_errors(xml_string)`
  works with no file involved.

#### Namespace binding helpers (`odmlib.ns_registry`)

```python
NS.get_document_namespaces(odm_obj) -> dict | None    # the per-document snapshot, or None
NS.bind_document_namespaces(odm_obj, snapshot=None)   # attach a snapshot to an element
```

A loaded document's namespaces are captured as a snapshot so a later load of a different
document cannot change how it serializes. The snapshot is bound **only** to objects the loader
returns directly — `root()`, `Study()`, `MetaDataVersion()`, `create_odmlib()`. An element
reached by walking the tree (`define.Study.MetaDataVersion`), or constructed after the load and
grafted in, has **no** snapshot and falls back to current global registry state — so its
`to_xml_string()` can emit a different `xmlns:def` than its own root. Rebind it explicitly:

```python
NS.bind_document_namespaces(mdv, NS.get_document_namespaces(define))
```

## 6. Validation: OID checker, conformance, XSD, modes

```python
from odmlib import create_oid_checker
checker = create_oid_checker("odm_1_3_2",          # also "define_2_1", "odm_2_0", ...
                             extra_skip_attrs=None, # attrs to ignore
                             extra_skip_elems=None) # element classes to ignore
odm.verify_oids(checker)                            # or pass to validate(oid_checker=checker)
```

**Checkers are single-use per document** — `verify_oids()` accumulates into `checker.oid`,
so a second pass with the same checker raises a false "not unique". Construct a new one per
verification, or call `checker.reset()` (clears `oid`, `unique_oids`, `oid_ref`, and
`is_verified`). In collect mode `validate()` warns when handed a checker that still holds
state. Static mappings usable without verifying: `oid_defs` (list of defining class names),
`ref_def`, `def_ref`, `ref_attrs`, `skip_attr`, `skip_elem`; `oid` and `oid_ref` populate
during `verify_oids()`.

```python
from odmlib.<package>.rules.metadata_schema import MetadataSchema   # e.g. odm_1_3_2, define_2_1
conformance = MetadataSchema()                       # no-arg
odm.validate(conformance_checker=conformance)
```

```python
from odmlib.odm_parser import ODMSchemaValidator     # XSD validation (schemas are bundled)
# bundled pairs: ("odm","1.3.2"), ("odm","2.0"), ("define","2.0"), ("define","2.1"),
#                ("arm","1.0"), ("arm","1.0-define2.1")
validator = ODMSchemaValidator(standard="define", version="2.1")
validator.validate_file("define.xml")                # raises OdmlibSchemaValidationError
validator.validate_tree(parsed_tree)                 # -> bool
for err in validator.xsd.iter_errors("define.xml"):  # collect all, with .reason / .path
    print(err.reason, err.path)
# ARM (ADaM): match the document's Define-XML version; the pairings are not interchangeable
ODMSchemaValidator(standard="arm", version="1.0-define2.1")   # def: v2.1 — what arm_1_0 models
ODMSchemaValidator(standard="arm", version="1.0")             # def: v2.0
# custom/local schema only:
# ODMSchemaValidator(xsd_file="/path/to/schema.xsd")
```

Modes (`odmlib.mode`, re-exported at top level):

```python
ValidationMode.STRICT          # default, all checks
ValidationMode.SKIP_REQUIRED   # omit required-attribute checks
ValidationMode.SKIP_VALUESET   # omit value-set enforcement
ValidationMode.SKIP_TYPE       # omit type checks / unknown-attr rejection
ValidationMode.SKIP_FORMAT     # omit format validators (datetime, SAS name, ...)
ValidationMode.PERMISSIVE      # all of the above combined
permissive(mode=ValidationMode.PERMISSIVE)   # context manager
get_mode() / set_mode(mode)                  # manual control (set_mode returns a reset token)
```

## 7. Exception hierarchy

```
OdmlibError                         (base)
├─ OdmlibValidationError            (also ValueError in 0.2.x)
│  ├─ OdmlibRequiredAttributeError
│  ├─ OdmlibOIDError
│  ├─ OdmlibConformanceError        (.cerberus_errors, .field_path, .expand())
│  ├─ OdmlibElementOrderError
│  ├─ OdmlibErrorLimitError         (max_errors truncation marker — collected, never raised)
│  └─ OdmlibSchemaValidationError   (.wrapped)
├─ OdmlibTypeError                  (also TypeError in 0.2.x)
├─ OdmlibParsingError
│  └─ OdmlibLoaderStateError
├─ OdmlibSerializationError
└─ OdmlibNamespaceError
Warnings: OdmlibWarning ─ OdmlibDeprecationWarning, OdmlibInteroperabilityWarning
Helpers:  ErrorCollector  (.errors, .warnings, .has_errors, .is_full, .truncated,
                           .add_error, .add_warning, .raise_if_errors)
          ErrorReporting  (.report, .collecting)  + is_collecting_checker(checker)
```

`OdmlibConformanceError.expand()` splits a bundled Cerberus result into one error per
failing field (what `validate(collect_errors=True)` does internally); each carries
`field_path` plus the complete raw dict on `cerberus_errors`.

Validation/type errors carry `element_path`, `hint`, `attribute`, and `element_type` where
known, so their `str()` is already a useful diagnostic. The dual inheritance from
`ValueError`/`TypeError` is a 0.2.x compatibility bridge and is scheduled for removal in
0.3.0 — prefer catching `OdmlibError` and its subclasses.

### Loading files you do not control

The hierarchy above covers *validation*. Ingestion is only partly covered: parse failures
are wrapped, but **filesystem errors are not**, so `except OdmlibError` alone is not enough
around a load of an untrusted path.

| Input | Raised | `OdmlibError`? |
|---|---|---|
| Malformed / truncated XML | `OdmlibParsingError` | yes |
| Well-formed XML, unrecognized root (e.g. HTML) | `OdmlibParsingError` | yes |
| Path does not exist | `FileNotFoundError` | no |
| Path is a directory | `IsADirectoryError` | no |
| Valid root, missing required attribute | `OdmlibRequiredAttributeError` | yes |

So catch broadly **at the load boundary only**, and translate into your own domain error:

```python
try:
    loader.open_odm_document(path)
    odm = loader.root()
except OdmlibError:
    raise                                  # a real conformance problem — let it through
except Exception as e:                     # ParseError / AttributeError / OSError
    raise MyIngestError(f"{path} is not a readable ODM document: {e}") from e
```

Keep the broad `except` tight around the two loader calls; anywhere else it will swallow
bugs. Parse failures are `OdmlibParsingError`, but the filesystem errors above are not, so
the broad `except` remains the safe pattern at the load boundary.

## 8. Dataset-JSON and conversion helpers

```python
from odmlib import DatasetJSON, Column, SourceSystem
ds = DatasetJSON(datasetJSONCreationDateTime=..., datasetJSONVersion="1.1.0",
                 itemGroupOID="IG.DM", name="DM", label="Demographics", records=1,
                 columns=[Column(itemOID="IT.AGE", name="AGE", label="Age", dataType="integer")],
                 rows=[[42]])
ds.write_ndjson("dm.ndjson")    # NDJSON — the Dataset-JSON v1.1 wire format
ds.write_json("dm.json")        # plain JSON alternative
ds.column_names                 # -> ["AGE"]

DatasetJSON.read_ndjson("dm.ndjson")               # read NDJSON
DatasetJSON.from_dict(parsed_json_dict)            # build from a plain-JSON dict

from odmlib import dataset_xml_to_dataset_json, dataset_json_to_dataset_xml
from odmlib import DefineFlattener, DefineBuilder   # DefineFlattener(odm).flatten_all()
```

See `dataset-json.md` for the converter signatures and Define-XML bridging.
