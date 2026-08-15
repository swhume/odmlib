# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

odmlib is a Python package for working with CDISC ODM (Operational Data Model) documents and its extensions (Define-XML, 
Dataset-XML, CT-XML). It provides an object-oriented interface for creating, parsing, and validating ODM files with 
XML and JSON serialization support.

**Supported Standards:**
- ODM 1.3.2 (`odmlib.odm_1_3_2`)
- ODM 2.0 (draft) (`odmlib.odm_2_0`)
- Define-XML 2.0 (`odmlib.define_2_0`)
- Define-XML 2.1 (`odmlib.define_2_1`)
- Dataset-XML 1.0.1 (`odmlib.dataset_1_0_1`)
- CT-XML 1.1.1 (`odmlib.ct_1_1_1`)
- ARM 1.0 (`odmlib.arm_1_0`)
- Dataset-JSON 1.1 (`odmlib.dataset_json_1_1`)

## Development Setup

```bash
# Install for development with all dev dependencies (preferred)
pip install -e ".[dev]"

# Or minimal install without dev tools
pip install -e .
```

**Dependencies:** xmlschema, validators, Cerberus, pathvalidate

**Dev dependencies (installed via `.[dev]`):** pytest, pytest-cov, sphinx, sphinx-rtd-theme, mypy

## Conduction Code Reviews

Read REVIEW.md and execute a codebase analysis following all listed constraints.

## For Planning and Research

For research and codebase exploration, use parallel Explore subagents by default.

## Running Tests

The project uses Python's built-in `unittest` framework. Tests can be run via pytest (preferred) or unittest directly:

```bash
# Run all tests (pytest - preferred)
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=odmlib --cov-report=term-missing

# Run a specific test file
python -m pytest tests/test_odm_loader.py -v

# Run all tests (unittest - also works)
python -m unittest discover tests -v

# Run a specific test case (unittest)
python -m unittest tests.test_odm_loader.TestODMLoader.test_odm_to_xml -v
```

## Architecture

### Core Design Pattern: Metaclass + Descriptors

odmlib uses Python metaclasses and descriptors to define ODM models declaratively. This architecture enables:
- Type validation at assignment time
- Automatic XML/JSON serialization
- Element ordering preservation
- Namespace management

**Key Base Classes:**
- `ODMElement` (odm_element.py): Base class for all ODM objects with metaclass `ODMMeta`
- `Descriptor` (descriptor.py): Base descriptor for attributes
- `Typed` subclasses (typed.py): Type-validated descriptors (String, Integer, OID, etc.)
- `ODMObject` / `ODMListObject` (typed.py): Descriptors for child elements

### Model Definition Pattern

Models are defined by creating classes that inherit from `ODMElement` and use descriptors:

```python
class StudyEventDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Description = T.ODMObject(element_class=Description)
    FormRef = T.ODMListObject(element_class=FormRef)
```

The metaclass `ODMMeta` automatically:
- Preserves declaration order using `OrderedDict`
- Separates attributes (`_attrs`) from child elements (`_elems`)
- Tracks namespace information (`_attr_ns`)
- Creates a `_fields` list of all properties

### Loader Architecture

The package uses a strategy pattern for loading documents:

1. **DocumentLoader** (document_loader.py): Abstract base class
2. **Specialized Loaders:**
   - `XMLODMLoader` / `JSONODMLoader` (odm_loader.py): For standard ODM
   - `XMLDefineLoader` / `JSONDefineLoader` (define_loader.py): For Define-XML
3. **Facade:** `ODMLoader` (loader.py): Wraps specialized loaders with common interface

**Loading Flow:**
```python
loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
loader.open_odm_document("file.xml")
odm = loader.root()  # Returns odmlib object hierarchy
mdv = loader.MetaDataVersion()  # Get first MetaDataVersion
```

### Serialization

All `ODMElement` objects support bidirectional conversion:

- **to_xml()** → ElementTree, carrying **no** xmlns declarations (see below)
- **to_xml_string()** → self-contained XML string; `xml_declaration=True` (keyword-only)
  prepends `<?xml version='1.0' encoding='UTF-8'?>`
- **to_json()** → JSON string, or `write_json(filename)`
- **to_dict()** → Python dict (namespace info stripped)

The `ODMWriter` class handles writing XML with proper namespace registration.

String and file output line up exactly: `to_xml_string()` returns the bytes `write_xml()`
writes *after* its declaration, and `to_xml_string(xml_declaration=True)` returns exactly
what `write_xml()` writes.

**Never `ET.tostring(obj.to_xml())`.** `to_xml()` emits prefix-literal tags (`def:leaf`,
not Clark notation) and no `xmlns`; declarations are attached by `to_xml_string()` and
`ODMWriter.write_odm()`. On Define-XML that markup raises `ParseError: unbound prefix`; on
ODM it parses into no namespace and re-loads with `FileOID` correct and every `Study` gone,
with no exception.

### Namespace Management

`NamespaceRegistry` (ns_registry.py) is a Borg singleton that:
- Maintains global prefix→URI mappings
- Handles default namespace designation
- Injects xmlns attributes into XML serialization
- Each model package registers its namespaces at import time

Because that state is process-wide, loading a document captures a **per-document snapshot**
(`bind_document_namespaces` / `get_document_namespaces`), which serialization consults
first — so opening a second document cannot change how the first one is written. The
loader binds the snapshot **recursively**, so nested elements reached by walking the tree
(`define.Study.MetaDataVersion`) serialize like their root.

**Residual limitation:** an element constructed *after* the load and grafted in carries no
snapshot and falls back to global state. Bind it explicitly:
`NS.bind_document_namespaces(new_elem, NS.get_document_namespaces(root))`.

**Important:** Use `NS.NamespaceRegistry.reset()` to clear state between tests.

### OID Validation System

Two-phase OID checking system (see `odm_element.py` methods):

1. **Index Building:** `build_oid_index()` creates an OID→object lookup
2. **Validation:** `verify_oids(oid_checker)` checks:
   - Uniqueness (no duplicate OIDs)
   - Ref/Def integrity (references point to valid definitions)
   - Type matching (e.g., FormOID refs must point to FormDef)

**OID Checkers:** Each model package has a `rules/oid_ref.py` with an `OIDRef` class that defines:
- `ref_def`: Maps reference attributes (e.g., "FormOID") to definition elements (e.g., "FormDef")
- `def_ref`: Reverse mapping for checking unreferenced definitions
- `skip_attr` / `skip_elem`: Elements excluded from validation

### Conformance Validation

Uses Cerberus schemas (see `rules/metadata_schema.py` in each model package):
- `verify_conformance(validator)` checks structure against schema
- Schemas are manually maintained per model (not auto-generated yet)

### XSD Schema Validation

odmlib bundles the official CDISC XSDs under `odmlib/schemas/<standard>/<version>/`
and validates against them via `ODMSchemaValidator` (odm_parser.py):

```python
from odmlib.odm_parser import ODMSchemaValidator
validator = ODMSchemaValidator(standard="define", version="2.1")
validator.validate_file("define.xml")   # raises OdmlibSchemaValidationError
validator.validate_tree(tree)           # returns bool
```

`schema_manager.py::_MAIN_SCHEMA` maps `(standard, version)` → root XSD filename.
Registered pairs: `("odm","1.3.2")`, `("odm","2.0")`, `("define","2.0")`,
`("define","2.1")`, `("arm","1.0")`, `("arm","1.0-define2.1")`.

**Key rule:** a `_MAIN_SCHEMA` key must exactly match its on-disk directory name —
`get_schema_path` builds `odmlib/schemas/<standard>/<version>/<filename>`. A key that
doesn't match resolves to a non-existent path and fails only at validation time.

**ARM has two entries** because ARM 1.0 layers onto Define-XML and the two Define-XML
versions use different `def:` namespace URIs:
- `("arm","1.0")` — the CDISC original, redefines `define/2.0`
- `("arm","1.0-define2.1")` — odmlib-derived, redefines `define/2.1`; this is the
  pairing `odmlib.arm_1_0.model` targets, since that model extends `define_2_1.model`

Both are supersets of their base Define-XML schema, so they also validate ARM-free
Define-XML documents. Compiled schemas are cached by path in `odm_parser._SCHEMA_CACHE`.

Both `standard` and `version` are required — there is no default. Pass
`xsd_file=<path>` for a custom or local schema.

### Element Ordering

ODM requires specific element order in XML. odmlib enforces this:
- `verify_order()`: Checks if elements match model declaration order
- `reorder_object()`: Reorders instance dict to match model order
- Order violations raise `ValueError`

## Important Model Differences

### ODM 1.3.2 vs 2.0

ODM v2.0 changes:
- Flatter structure: `StudyEventDef` contains `ItemGroupRef` directly (no `FormDef`/`FormRef`)
- New elements: `WorkflowRef`, `WorkflowDef`
- Different namespace URI: `http://www.cdisc.org/ns/odm/v2.0`
- The ODM v2.0 standard is complete, but the JSON implementation is still draft. 
- The ODM v2.0 odmlib model is still draft.

### Define-XML Extensions

Define-XML models extend base ODM elements with additional attributes/elements:
- Inherit from `odm_1_3_2.model` classes
- Add Define-specific elements (e.g., `ValueList`, `WhereClause`)
- Register "def" namespace (v2.0: `http://www.cdisc.org/ns/def/v2.0`, v2.1: `http://www.cdisc.org/ns/def/v2.1`)
- Use `XMLDefineLoader` / `JSONDefineLoader` instead of standard loaders

## Common Patterns

### Creating ODM Objects Bottom-Up

Build from leaves to root:
```python
tt = TranslatedText(_content="Study Name", lang="en")
sn = StudyName(TranslatedText=[tt])
gv = GlobalVariables(StudyName=sn)
```

### Finding Elements by Attribute

Use the `find()` method (defined in `ODMElement`):
```python
item = mdv.find("ItemDef", "OID", "IT.AGE")  # Find in list
form_ref = sed.find("FormRef", "Mandatory", "Yes")  # Find in nested list
```

### Working with Specific Models

Specify `model_package` when creating loaders:
```python
# For Define-XML 2.1
loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1"))

# For ODM 2.0
loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
```

### Define-XML Roundtrip (DefineFlattener / DefineBuilder)

The `dataset_json_1_1` package provides a pair of classes for flattening and rebuilding Define-XML v2.1:

- **`DefineFlattener`** (`odmlib/dataset_json_1_1/define_flattener.py`): Converts a loaded Define-XML v2.1 object tree into 11 core tabular Dataset-JSON datasets (study, standards, datasets, variables, value_level, where_clauses, methods, comments, documents, codelists, codelist_terms) **plus 2 lossless-roundtrip extension datasets** (`aliases`, `origins`). The extensions are listed in `EXTRA_TABLE_NAMES`; `flatten_all()`/`write_all()` always emit all 13.
- **`DefineBuilder`** (`odmlib/dataset_json_1_1/define_builder.py`): The inverse — reconstructs a full Define-XML v2.1 ODM object tree from those datasets. Enables authoring Define-XML from tabular sources (Excel, CSV, databases). The `aliases`/`origins` datasets are **optional**: `read_all()` skips them if absent and the builder behaves exactly as before (backward compatible) — they are applied via no-op-when-absent post-passes (`_apply_aliases`, `_apply_origins`).
- **Escape hatch:** `DefineBuilder.add_post_build_hook(fn)` runs `fn(odm_root)` just before `build()` returns (mutate in place, or return a replacement root) for any element the datasets still cannot express. The fluent `ODMBuilder` has the analogous `attach(parent, element)` / `attach_to_current(element)` plus a `current` property.

```python
from odmlib.dataset_json_1_1 import DefineFlattener, DefineBuilder

# Flatten: Define-XML -> 11 Dataset-JSON tables
flat = DefineFlattener(odm_root).flatten_all()
flattener.write_all('/output/dir')

# Rebuild: 11 Dataset-JSON tables -> Define-XML
datasets = DefineBuilder.read_all('/output/dir')
rebuilt = DefineBuilder(datasets).build()
rebuilt.write_xml('rebuilt_define.xml')
```

### Custom Extensions

To create proprietary extensions:
1. Create new model file importing base models
2. Extend existing classes with new descriptors
3. Register any new namespaces
4. Use `local_model=True` in loader with module path
5. Update OID checkers and Cerberus schemas if needed
6. If the extension ships its own XSD, add it under `odmlib/schemas/<standard>/<version>/`
   and register the pair in `schema_manager._MAIN_SCHEMA` (directory name must match the key)

## Known Limitations

- **No ItemData[Type] support:** ItemData with typed elements (deprecated in ODM v2.0)
- **No ds:Signature support:** Digital signatures not implemented
- **Manual OID checks:** Ref/Def checks are manually coded, not auto-generated from models
- **Single MetaDataVersion:** Loaders return first MDV by default; use `idx` parameter for others
- **Order of declaration matters:** Elements must be declared in the order they appear in ODM spec

## Testing Conventions

- Tests use `unittest.TestCase` (not pytest)
- Test data files located in `tests/data/`
- Each major element type has a dedicated test file (e.g., `test_itemDef.py`)
- Tests include: object creation, XML/JSON round-tripping, validation, conformance checks
- Some tests use snapshot comparison (e.g., `tests/data/cdash_demo_v20.xml`)
