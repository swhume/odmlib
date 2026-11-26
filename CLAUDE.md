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

## Claude Code Skill

This repository contains a Claude Code skill for odmlib at `.claude/skills/odmlib/`
(SKILL.md, four `references/*.md`, eight runnable `examples/*.py`). Because it lives under
`.claude/skills/` in this repo, it is active automatically when working *in* this repository.

It is **not** shipped in the PyPI package. To use it elsewhere, copy the directory into the
target project's `.claude/skills/`, or into `~/.claude/skills/` for all projects:

```bash
cp -r .claude/skills/odmlib ~/.claude/skills/
```

`.claude/skills/odmlib.skill` is a packed zip of that same directory, for distribution.

**When editing the library, keep the skill true.** The skill asserts library behavior in
prose, and three test files guard the machine-checkable half:

```bash
python -m pytest tests/test_skill_contract.py    # signatures, front matter, import surface
python -m pytest tests/test_skill_examples.py    # all 8 examples must exit 0
python -m pytest tests/test_skill_bundle.py      # packed bundle matches source
```

After editing SKILL.md, a reference, or an example, repack the bundle or
`test_skill_bundle.py` will fail:

```bash
python scripts/build_skill_bundle.py             # --check reports drift without writing
```

The skill documents odmlib 0.2.1 and later. If you change a documented signature or default,
update the skill and the expected table in `tests/test_skill_contract.py` together.

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

### Type checking

odmlib has known mypy errors, listed in `scripts/mypy_baseline.txt`. Check for *new* ones
with the version CI pins (`pip install "mypy==2.4.1"`):

```bash
python scripts/mypy_baseline.py            # exit 1 only on errors not in the baseline
python scripts/mypy_baseline.py --update   # after fixing errors, shrink the baseline and commit it
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
- Resolves `element_class=T.SELF` to the class being defined, for a recursive element
  (ODM 2.0 `ItemGroupData` holds `ItemGroupData`). Assigning a descriptor after the class
  body registers nothing, so use `T.SELF`
- Raises `OdmlibTypeError` for a descriptor *class* where an instance belongs
  (`Context = T.String` instead of `T.String()`)

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
cd = loader.ClinicalData()  # First ClinicalData (0.3.0; also ReferenceData(idx))
```

`ClinicalData()`/`ReferenceData()` call the XML/JSON ODM loaders' `load_clinicaldata` /
`load_referencedata`. They are deliberately **not** on the `DocumentLoader` ABC (that would
break third-party loaders); the facade raises `OdmlibTypeError` for a loader without them.

### Serialization

All `ODMElement` objects support bidirectional conversion:

- **to_xml_string()** → self-contained XML string; `xml_declaration=True` (keyword-only)
  prepends `<?xml version='1.0' encoding='UTF-8'?>`
- **to_element()** → namespace-resolved ElementTree Element (Clark notation). Use this when
  you want a tree — it parses, embeds, canonicalizes and pretty-prints correctly
- **to_xml()** → the internal tree builder shared by `to_xml_string()` and `ODMWriter`;
  carries **no** xmlns declarations and uses prefix-literal tags (see below)
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
with no exception. **Use `to_element()`** when you want an Element — it returns a
namespace-resolved tree that does not have any of these problems.

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

**Loading reads its own namespaces too (0.3.0).** Each model package has
`AUXILIARY_NAMESPACES` and a re-runnable `register_namespaces()` for its non-default prefixes.
Every loader (XML and JSON) calls it from `create_document`, and registers the default
namespace itself. The XML loaders and the parser then resolve child elements against the
namespaces captured at `create_document` (`DocumentLoader._ns_map`), not the live registry.
That way, opening a Define-XML 2.0 file cannot empty an open 2.1 document's `def:` lists.
An unknown child prefix raises `OdmlibParsingError`. A namespaced attribute (`{uri}name`)
sets a field only when `uri` belongs to that field's namespace, resolved from the field's
own model. Anything else is ignored, with an `OdmlibWarning`.

**Missing prefixes (0.3.0).** `set_odm_namespace_attributes()` declares every used prefix
it finds in the registry/snapshot. A used prefix that is missing — typically after
`reset()`, which drops what models registered on import — is declared from
`ns_registry.FIXED_PREFIX_URIS` when odmlib binds it to one URI in every model (`xs`,
`xlink`, `nciodm`, `data`, `arm`). Anything else (`def`, `odm`, custom prefixes) can't be
resolved without guessing the version, so it emits an `OdmlibInteroperabilityWarning` and the
output stays unparseable until the prefix is registered. If a model ever binds a fixed
prefix to another URI, remove it from the table; `tests/test_namespace_fallback.py` checks
the table against every `model.py`.

**Important:** Use `NS.NamespaceRegistry.reset()` to clear state between tests.

### OID Validation System

Two-phase OID checking system (see `odm_element.py` methods):

1. **Index Building:** `build_oid_index()` creates an OID→object lookup
2. **Validation:** `verify_oids(oid_checker)` checks:
   - Uniqueness (no duplicate OIDs)
   - Ref/Def integrity (references point to valid definitions)
   - Type matching (e.g., FormOID refs must point to FormDef)

**OID Checkers:** `create_oid_checker(model_package)` (`oid_generator.py`) builds a
`DynamicOIDRef` by introspecting the model's classes, with per-model skip lists and
overrides in `oid_generator_config.py`. It defines:
- `ref_def`: Maps reference attributes (e.g., "FormOID") to definition elements (e.g., "FormDef")
- `def_ref`: Reverse mapping for checking unreferenced definitions
- `skip_attr` / `skip_elem`: Elements excluded from validation

The manual `rules/oid_ref.py` `OIDRef` classes were removed in 0.3.0;
`tests/test_oid_generator.py` keeps their `ref_def` tables as a frozen snapshot.

For ODM 2.0, `Query` is a `skip_elem`: its OID must be unique but it is never reported as
unreferenced. A data-only ClinicalData file (metadata in an earlier file) can pass
`extra_skip_attrs=oid_generator_config.ODM_20_DATA_ONLY_SKIP_ATTRS`; references into
AdminData are still checked.

The checker also has `ref_def_any_of` (0.3.0) for references that may point at several
element types — ODM 2.0's workflow and timing references (`StartOID`, `SourceOID`, `TargetOID`, `EndOID`, `StructuralElementOID`,
`PredecessorOID`, `SuccessorOID`), from `_REF_DEF_ANY_OF`. The target sets follow the ODM
v2.0 spec as transcribed in the cdisc-org/DataExchange-ODM-LinkML model; for ODM 2.0 only
`FileOID`/`PriorFileOID` are skipped.

### Exceptions

Every odmlib exception derives from `OdmlibError` (`exceptions.py`) and, since 0.3.0,
from nothing else: `OdmlibValidationError` is not a `ValueError` and `OdmlibTypeError`
is not a `TypeError`. Library code must raise an odmlib class, never a bare
`ValueError`/`TypeError`; `tests/test_exception_contract.py` scans the source and fails
otherwise. `xhtml.py` is the one allowlisted module, because its callers catch and wrap
its `ValueError`. In tests, assert the specific class (`OdmlibRequiredAttributeError`,
`OdmlibOIDError`, ...), not a builtin.

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
- Order violations raise `OdmlibElementOrderError`
- Model order is also the order odmlib *writes*. Where the XSD allows more than one order
  without declaring an interleaved group, a loaded document can come back reordered (still
  valid). The known case is Define-XML ItemDef's `def:ValueListRef` before `def:Origin`,
  which ODM 1.3.2's repeatable extension group allows. It is pinned in
  `tests/_roundtrip.py::KNOWN_REORDERINGS`.

**Interleaved repeating groups** (`interleave.py`, 0.3.0). Where the XSD lets two child
types alternate — ODM 2.0 `ItemGroupDef` (`ItemGroupRef`/`ItemRef`), `StudyEventGroupDef`
(`StudyEventGroupRef`/`StudyEventRef`), `WorkflowDef` (`Transition`/`Branching`),
`ItemGroupData` (nested `ItemGroupData`/`ItemData`) — the
member descriptors are declared `T.ODMListObject(..., group="<XSD group name>")`.
`ODMMeta` records them in `_groups`/`_group_of`, and each list is stored as a
`GroupMemberList`: a real `list` that writes through to one shared `InterleavedGroup`
sequence. The XML loader appends members in document order, `to_xml()` writes the shared
order, `append` goes last, and `verify_order()` treats a group as one slot. Read the
combined order with `elem.children("ItemRef", "ItemGroupRef")` — never concatenate the
lists. ODM 2.0 JSON keeps one array per type, so it does not carry the interleaving.

## Important Model Differences

### ODM 1.3.2 vs 2.0

ODM v2.0 changes:
- Flatter structure: `StudyEventDef` contains `ItemGroupRef` directly (no `FormDef`/`FormRef`)
- New elements: `WorkflowRef`, `WorkflowDef`
- Different namespace URI: `http://www.cdisc.org/ns/odm/v2.0`
- The ODM v2.0 standard is complete, but the JSON implementation is still draft. 
- The ODM v2.0 odmlib model is still draft.
- `TranslatedText.div` (`T.XHTMLDiv`, `xhtml.py`) holds an `xhtml:div` child as a
  self-contained markup string; `ODMMeta` lists such descriptors in `_markup`, which are
  stored like attributes but written as a child after `_content`.
- Every ODM v2.0 metadata file the plan surveyed loads in strict mode (crfutils relies on
  it). Keep `tests/test_odm_2_0_xsd_alignment.py` green: it also checks reachability
  from `ODM` and that no `_content` is required where the XSD allows empty text.
- `xsi:*` attributes a class does not model are ignored on load (all models);
  `ODM.schemaLocation` is modelled and round-trips.
- **ClinicalData layer (0.3.0).** The whole ODM 2.0 XSD is modelled (149 elements; the
  alignment guard's allowlists are empty). Do not copy 1.3.2 shapes: there is no
  `FormData` (StudyEventData holds ItemGroupData), values are `Value` child elements (no
  `ItemData/@Value`), and AuditRecord/Signature/Annotation follow the data children,
  then Query, with no `AuditRecords`/`Signatures`/`Annotations` containers.
  `ItemGroupData` nests itself via `T.SELF`. The containers (ClinicalData, SubjectData,
  StudyEventData, ItemGroupData) iterate one level down and are always truthy.

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
refs = igd.children("ItemRef", "ItemGroupRef")  # children in written (document) order
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
- **Single MetaDataVersion:** Loaders return first MDV by default; use `idx` parameter for others
- **Order of declaration matters:** Elements must be declared in the order they appear in ODM spec

## Testing Conventions

- Tests use `unittest.TestCase` (not pytest)
- Test data files located in `tests/data/`. **It is read-only during a run:** a session
  fixture in `conftest.py` fails the run if any file there is created, changed or deleted.
  Write generated output to `tempfile.TemporaryDirectory()` with `self.addCleanup(...)`.
- `tests/data/odm_v2/` holds ODM v2.0 fixtures vendored from the odm-v2 skill and pinned by
  sha256 in its `MANIFEST.json` (licences in `PROVENANCE.md`). Never edit them in place:
  fix them in odm-v2, then run
  `python scripts/sync_odm_v2_fixtures.py --source <odm-v2>/.claude/skills/odm-v2/examples`
  (`--check` reports drift).
- Each major element type has a dedicated test file (e.g., `test_itemDef.py`)
- Tests include: object creation, XML/JSON round-tripping, validation, conformance checks
- Some tests use snapshot comparison (e.g., `tests/data/cdash_demo_v20.xml`)
- **Round trips (`tests/test_json_roundtrip.py`, helpers in `tests/_roundtrip.py`).** Every
  fixture in `CORE_FIXTURES`, plus the vendored ODM v2.0 documents, runs through five legs:
  XML->XML, XML->JSON->XML, JSON->JSON, XML tree vs JSON tree, and vs the vendored JSON.
  The normalizer (N1-N5) is the complete list of forgiven differences. A new difference is
  a library bug: fix it in the library, never by widening the normalizer. To add a
  document, append a `Fixture` to `CORE_FIXTURES`.
