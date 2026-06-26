# Changelog

All notable changes to odmlib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]- 2026-06-23

### Added

#### Context Manager `write_on_exit` Opt-Out
- `odmlib/context.py`: added `write_on_exit: bool = True` parameter to
  `ODMContext`, `DefineContext`, `open_odm`, and `open_define`. Passing
  `write_on_exit=False` suppresses the auto-save on clean exit, enabling
  read-only inspection through the context managers without modifying or
  creating any file. The default (`True`) preserves the documented
  in-place save behaviour — additive change, no compat impact.
- `tests/test_context_managers.py`: 10 new tests covering the opt-out
  (XML, JSON, `open_odm`, `open_define`, and the input-preservation
  regression guard for the default-output-file footgun) plus explicit
  default-still-writes guards.

#### ODM v2.0 Model/XSD Alignment (safe subset)
- `odmlib/data/valuesets.json`: added 12 missing `odm_2_0` value-set keys
  (`ReturnValue.DataType`, `ItemRef.Core/Repeat/Other/IsNonStandard/HasNoData`,
  `CodeListItem.Other`, `Telecom.TelecomType`, `ItemGroupDef.IsNonStandard/HasNoData`,
  `CodeList.IsNonStandard`, `ODM.Context`) bound to the ODM 2.0
  `ODM-enumerations.xsd` value lists.
- `tests/test_odm_2_0_model.py`: new construction + XML/JSON round-trip suite
  for the major ODM 2.0 classes.
- `tests/test_odm_2_0_known_gaps.py`: new strict-`xfail` markers pinning the
  five deferred structural ODM 2.0 model/XSD gaps so CI documents the known
  state and fails loudly if a gap is silently fixed or regressed. (Its
  ItemDef test is now a passing regression guard — see Changed below.)

### Changed
- **ODM 2.0 `TranslatedText.Type` is now required** (`odmlib/odm_2_0/model.py`),
  matching the XSD (`use="required"`, free-text media type). `ODMBuilder`
  now defaults `Type="text/plain"` for the ODM 2.0 model shape only via a new
  `_translated_text()` helper.
  
- `odmlib/valueset.py`: `ValueSet.value_set()` no longer raises for an
  unknown *attribute* — it returns the new `ValueSet.UNKNOWN_ATTRIBUTE`
  sentinel so `validate()` returns `False` and the `SKIP_VALUESET` permissive
  guard can bypass an unregistered value set. Unknown *version* still raises.
  **Behavioral note:** in strict mode an unregistered value-set attribute now
  raises `OdmlibTypeError` (from `ValidValues.__set__`) instead of the former
  `OdmlibValidationError` (from `value_set()`).

- **ODM v2.0 `ItemDef` aligned with the ODM 2.0 XSD**
  (`odmlib/odm_2_0/model.py`). Removed the XSD-rejected attributes
  `FractionDigits`, `DatasetVarName`, and `SDSVarName`; added the
  XSD-defined optional attributes `DisplayFormat` and `VariableSet`. Code
  that set the removed attributes on an `odm_2_0` `ItemDef` should migrate —
  those values were schema-invalid and are no longer serialized. (Closes
  the ROADMAP v0.2.1 ItemDef gap / `ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`
  §3.7; the XSD `ItemDef/ValueListRef` child element remains deferred.)

### Known Limitations
- **ODM v2.0 structural model/XSD gaps deferred to v0.2.1.** Five features
  produce schema-invalid output if used under `model_package="odm_2_0"`:
  `ConditionDef` (no required `MethodSignature`), text-based
  `FormalExpression`, `Protocol.StudyEventRef` (removed in the 2.0 schema),
  `MetaDataVersion.StudyTiming` placement, and `StudyEventGroupDef` (missing
  required child group). The affected `ODMBuilder` helpers carry docstring
  caveats. See ROADMAP "v0.2.1 — ODM v2.0 Model/XSD Alignment" and
  `ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`.

#### ODM v2.0 XSD Schema Validation
- `odmlib/schema_manager.py`: registered `("odm", "2.0") → "ODM.xsd"`
  in `_MAIN_SCHEMA`. `ODMSchemaValidator(standard="odm", version="2.0")`
  now resolves the bundled `odmlib/schemas/odm/2.0/ODM.xsd` (target
  namespace `http://www.cdisc.org/ns/odm/v2.0`) and exposes the same
  `validate_tree()` / `validate_file()` API used for ODM 1.3.2 and
  Define-XML.
- The v2.0 XSD set (`ODM.xsd` + `ODM-foundation.xsd` + 7 modular
  includes + xlink/xml/xhtml) was already shipping in
  `odmlib/schemas/odm/2.0/` via the `schemas/**/*.xsd` package-data
  glob; the registry entry is the only missing wiring.
- `tests/test_schema_manager.py`: 4 new tests verifying
  `get_schema_dir("odm", "2.0")`, `get_schema_path("odm", "2.0")`,
  the resolved filename (`ODM.xsd`), and the integration
  file-existence check.
- `tests/test_odm_validator.py`: new `TestODMv20Validator` class
  validating `tests/data/odmv2_example.xml` and
  `tests/data/cdash_demo_v20.xml` end to end, plus a regression test
  that an ODM 1.3.2 document fails v2.0 validation. New
  `test_explicit_odm_v20_works()` in
  `TestODMValidatorConstructorContract`.
- `docs/source/guides/validation.rst`: rewrote the "Schema Validation"
  section to document `ODMSchemaValidator` (the previous text
  referenced a nonexistent `SchemaManager` class).

#### Permissive Loading Mode
- New `odmlib/mode.py` module with `ValidationMode` flag enum and
  `permissive()` context manager for loading non-conformant ODM documents
- `ValidationMode.STRICT` (default) — all validation enforced (existing
  behavior, unchanged)
- `ValidationMode.SKIP_REQUIRED` — omit required-attribute checks during
  construction and access
- `ValidationMode.SKIP_TYPE` — omit type checks (Typed, Integer, Float,
  ODMObject, ODMListObject, Positive, NonNegative, and unknown-attribute
  rejection)
- `ValidationMode.SKIP_FORMAT` — omit format validators (datetime, SAS
  name/format, email, URL, filename, regex, sized string)
- `ValidationMode.SKIP_VALUESET` — omit ValidValues and
  ExtendedValidValues enforcement
- `ValidationMode.PERMISSIVE` — composite flag that skips all validation
  categories
- `permissive()` context manager with automatic cleanup via
  `contextvars.ContextVar`; supports graduated control via flag
  combinations
- `open_odm()` and `open_define()` context managers accept
  `permissive=True` or a specific `ValidationMode` combination
- `ValidationMode`, `permissive`, `get_mode`, `set_mode` exported from
  `odmlib` package root
- New how-to guide: `docs/source/guides/permissive_loading.rst`
- `tests/test_permissive_mode.py` — 70 tests covering all validation
  categories, context manager safety, integration with loaders, and the
  load-fix-validate workflow

#### Error Reporting and Diagnostics
- New `odmlib/exceptions.py` module with a structured exception hierarchy
- `OdmlibError` — base class for all odmlib exceptions
- `OdmlibValidationError` — replaces bare `ValueError` for validation failures; includes
  `element_path`, `hint`, `attribute`, `element_type`, and `actual_value` attributes
- `OdmlibRequiredAttributeError` — raised when a required attribute is missing at construction
- `OdmlibOIDError` — raised for OID uniqueness or ref/def integrity failures
- `OdmlibConformanceError` — raised when Cerberus conformance validation fails; exposes
  raw `cerberus_errors` dict for programmatic inspection
- `OdmlibElementOrderError` — raised when child elements violate ODM-spec ordering
- `OdmlibTypeError` — replaces bare `TypeError` for type/enum validation failures
- `OdmlibParsingError` — raised when an XML or JSON document cannot be parsed
- `OdmlibLoaderStateError` — raised when a loader method is called before the document is opened
- `OdmlibSerializationError` — raised when the model cannot be serialized to XML or JSON
- `OdmlibNamespaceError` — raised for namespace registration or lookup failures
- `OdmlibWarning`, `OdmlibDeprecationWarning`, `OdmlibInteroperabilityWarning` — warning hierarchy
- `ErrorCollector` — accumulates validation errors instead of raising on the first failure;
  `has_errors`, `add_error()`, `add_warning()`, `raise_if_errors()` API
- `ODMElement.validate()` method — unified validation entry point supporting both
  fail-fast (default) and collect-all-errors (`collect_errors=True`) modes
- All exceptions and `ErrorCollector` exported from `odmlib` package root
- `tests/test_exceptions.py` — 47 tests covering hierarchy, formatting, backward compat, and model integration
- `tests/test_collect_errors.py` — 10 tests covering fail-fast and collect-all-errors validation modes

#### Dataset-JSON v1.1 ODMElement Model
- New `odmlib/dataset_json_1_1/` package — spec-conformant Dataset-JSON v1.1 support using
  the ODMElement/descriptor pattern (one dataset per file, matching the v1.1 specification)
  - `DatasetJSON` — root element with `to_json()`, `from_json()`, `write_json()`, `read_json()`,
    `write_ndjson()`, `read_ndjson()`, `to_dict()`, `from_dict()`, `add_row()`, `add_column()`,
    `column_names` property
  - `Column` — column metadata with validated `dataType` and optional `targetDataType`,
    `length`, `displayFormat`, `keySequence`
  - `SourceSystem` — optional nested source system metadata object
  - `DatasetJSONElement` base class disables XML serialization (`to_xml()` raises
    `NotImplementedError`) and handles mixed list types in `to_dict()`
- New `odmlib/dataset_json_1_1/define_flattener.py` — converts Define-XML v2.1 metadata into
  11 tabular Dataset-JSON datasets (study, standards, datasets, variables, value_level,
  where_clauses, methods, comments, documents, codelists, codelist_terms)
  - `DefineFlattener.flatten_all()` returns dict of dataset name → DatasetJSON
  - `DefineFlattener.write_all(output_dir)` writes individual JSON files
  - O(1) ItemDef and WhereClauseDef lookups via index
  - `_safe_get()` utility for traversing deeply nested optional attributes
- New `odmlib/dataset_json_1_1/converter.py` — bidirectional Dataset-XML ↔ Dataset-JSON v1.1
  - `dataset_xml_to_dataset_json(odm_obj)` returns dict[str, DatasetJSON] (one per ItemGroupOID)
  - `dataset_json_to_dataset_xml(dataset_json, model)` converts back to Dataset-XML
- Updated `odmlib/dataframe.py` — Pandas integration for the new model
  - `dataset_json_to_dataframe()` — DatasetJSON v1.1 → DataFrame
  - `define_metadata_to_dataframes(odm_root)` — Define-XML v2.1 → dict of DataFrames
  - `dataframe_to_dataset_json(df, name, label, oid)` — DataFrame → DatasetJSON v1.1
- `DatasetJSON`, `Column`, `SourceSystem`, `DefineFlattener`, `dataset_xml_to_dataset_json`,
  `dataset_json_to_dataset_xml` exported from `odmlib` package root
- New how-to guide: `docs/source/guides/dataset_json.rst`
- New API reference page: `docs/source/odmlib.dataset_json_1_1.rst`
- New tests: `tests/test_dataset_json_1_1_model.py` (68 tests),
  `tests/test_define_flattener.py` (45 tests),
  `tests/test_dataset_json_1_1_converter.py` (21 tests),
  `tests/test_dataframe_phase3.py` (39 tests)

#### Interoperability and Format Support
- New `odmlib/dataframe.py` — optional Pandas DataFrame integration
  - `metadata_to_dataframe(mdv, element_type, attributes=None)` — exports odmlib metadata
    elements (ItemDef, ItemGroupDef, CodeList, etc.) as a DataFrame
  - `clinical_data_to_dataframe(clinical_data, item_group_oid)` — flattens ODM 1.3.2
    hierarchical clinical data (SubjectData → StudyEventData → FormData → ItemGroupData)
    into a tabular DataFrame
  - `dataset_to_dataframe(clinical_data)` — flattens Dataset-XML 1.0.1 ClinicalData
    (flat structure, no SubjectData) into a DataFrame
  - `dataframe_to_items(df, model_module, element_type, column_mapping=None)` — creates
    odmlib element instances from a DataFrame (one row per element); skips invalid rows
  - Graceful degradation: importing the module always succeeds; calling any function
    raises `ImportError` with install hint when pandas is absent
- Optional dependency group `dataframe` added to `pyproject.toml`:
  `pip install odmlib[dataframe]` installs pandas ≥ 1.5
- pandas ≥ 1.5 added to the `dev` dependency group so the full test suite
  runs against pandas in CI development environments
- New `tests/test_dataframe.py` — tests for DataFrame integration
  (skipped automatically when pandas is not installed)
- New how-to guide: `docs/source/guides/interoperability.rst`
- New API reference page: `odmlib.dataframe` added to Sphinx `index.rst`

#### Packaging Modernization
- `pyproject.toml` for modern Python packaging (replaces `setup.py` as primary config)
- GitHub Actions CI: automated testing on Python 3.9–3.13
- GitHub Actions: automated PyPI publishing on tagged releases
- `CHANGELOG.md` for tracking changes going forward
- Semantic versioning policy starting at 0.2.0

### Changed

#### Exception Hierarchy: OdmlibSchemaValidationError
- `OdmlibSchemaValidationError` now inherits from `OdmlibValidationError`
  (and therefore from `OdmlibError`). Previously it inherited only from
  `Exception` and was excluded from the unified hierarchy. A single
  `except OdmlibValidationError` now catches both XSD violations raised by
  `ODMSchemaValidator.validate_file()` and in-memory model validation
  failures (required-attr, OID, conformance, element order).
- The class has moved from `odmlib/odm_parser.py` to `odmlib/exceptions.py`.
  `from odmlib.odm_parser import OdmlibSchemaValidationError` continues to
  work via re-export — no migration required for existing callers.
- Also exported from the package root: `from odmlib import OdmlibSchemaValidationError`.
- Backward compatibility: `ex.args[0]` still returns the wrapped
  `xmlschema` exception, so callers using `ex.args[0].msg` are unaffected.
  The wrapped exception is also accessible via the new `ex.wrapped`
  attribute.

#### Minimum Python Version
- Bumped minimum supported Python version from 3.9 to 3.10. Python 3.9
  reached end-of-life in October 2025 and is no longer tested in CI.
  Users on 3.9 should upgrade; install requires `requires-python = ">=3.10"`.
- CI matrix now tests Python 3.10, 3.11, 3.12, and 3.13.
- Workflow hardening: `fail-fast: false` (all matrix versions report
  independently), action versions bumped to Node 24-compatible releases
  (`actions/checkout@v5`, `actions/setup-python@v6`,
  `peaceiris/actions-gh-pages@v4`), least-privilege `GITHUB_TOKEN`
  permissions, and a concurrency group so superseded runs on the same
  ref are cancelled.

#### Permissive Loading Mode
- `odmlib/descriptor.py`: `Descriptor.__get__` returns `None` for unset
  required attributes when `SKIP_REQUIRED` mode is active (previously
  always raised `OdmlibRequiredAttributeError`)
- `odmlib/odm_element.py`: `ODMElement.__init__` and `__setattr__`
  bypass unknown-attribute rejection and required-attribute enforcement
  when appropriate mode flags are active
- `odmlib/typed.py`: all 25 `__set__` methods check the current
  `ValidationMode` before raising validation exceptions
- `odmlib/context.py`: `open_odm()` and `open_define()` accept a new
  `permissive` parameter; `ODMContext` and `DefineContext` manage mode
  lifecycle in `__enter__`/`__exit__`

#### Structured odmlib Exceptions
- All ~70 `ValueError`/`TypeError` raises across 16 files replaced with structured odmlib exceptions
- `odmlib/odm_element.py`: `verify_order()` now raises `OdmlibElementOrderError` with a hint to use
  `reorder_object()`; `reorder_object()` issues an `OdmlibWarning` before silently reordering
- `odmlib/odm_1_3_2`, `odmlib/define_2_0`, `odmlib/define_2_1` conformance checkers now raise
  `OdmlibConformanceError` with structured `cerberus_errors` attribute instead of `ValueError(dict)`

#### Dynamic OID Ref/Def Generation
- New `odmlib/oid_generator.py` module with fully dynamic OID ref/def checking derived
  from model class introspection — eliminates manual maintenance of `oid_ref.py` files
- `DynamicOIDRef` class — drop-in replacement for the manual `OIDRef` classes with the
  same `add_oid()`, `add_oid_ref()`, `check_oid_refs()`, and `check_unreferenced_oids()` API
- `create_oid_checker(model_package, extra_skip_attrs=None, extra_skip_elems=None)` factory
  function — primary public API for creating OID checkers; exported from `odmlib` package root
- `odmlib/oid_generator_config.py` — per-model skip-attribute and skip-element configuration
- **ODM 2.0 OID checking** now supported for the first time via `create_oid_checker("odm_2_0")`
- Manual `OIDRef` classes in `rules/oid_ref.py` for all three model packages
  (`odm_1_3_2`, `define_2_0`, `define_2_1`) now emit `OdmlibDeprecationWarning` on
  instantiation; they remain functional and will be removed in v0.3.0
- `tests/test_oid_generator.py` — 57 new tests covering model introspection, mapping
  correctness, DynamicOIDRef behavior, end-to-end validation, and deprecation warnings

#### ARM 1.0 Model Support
- New `odmlib/arm_1_0/` package — CDISC Analysis Results Metadata (ARM) v1.0 model using
  the ODMElement/descriptor pattern
  - Supports ARM elements: `AnalysisResultDisplays`, `ResultDisplay`, `AnalysisResult`,
    `AnalysisDatasets`, `AnalysisDataset`, `AnalysisVariable`, `ProgrammingCode`, `Code`,
    `Documentation`, `AnalysisDocumentation`, and supporting elements
  - Integrates with Define-XML 2.1 for analysis results metadata
  - ARM namespace (`arm`) registered automatically on import

#### Valueset Regex Validation
- `odmlib/valueset.py`: `ValueSet.validate(value)` — validates a value against the
  valueset's allowed values, including regex pattern matching for string-type entries
- `odmlib/valueset.py`: `ValueSet.describe()` — returns a human-readable description
  of the valid values for error messages
- `odmlib/data/valuesets.json`: `MetaDataVersion.DefineVersion` converted from enumerated
  list to regex pattern `^2\.[01](\.\d+)?$` for flexible version matching
- `tests/test_valueset.py` — 30 tests for regex validation and describe functionality

#### Element Search Methods
- `ODMElement.find_all(element_type, attribute, value)` — find all matching child elements
  in a list attribute
- `ODMElement.find_by(**kwargs)` — find a child element matching multiple attribute criteria

#### ODMBuilder Fluent API
- New `odmlib/builder.py` — `ODMBuilder` class providing a fluent/chained API for building
  ODM documents programmatically with `add_study()`, `add_metadata_version()`,
  `add_item_group_def()`, `add_item_def()`, `add_code_list()`, and `build()` methods

#### Updated Packaging
- Unified version to `0.2.0` across `pyproject.toml`, `odmlib/__init__.py`, and `docs/source/conf.py`
- `odmlib/__version__` now read dynamically from installed package metadata via `importlib.metadata`
- Installation: `pip install -e ".[dev]"` replaces `python setup.py develop`
- Installation: `pip install -e .` replaces `python setup.py install`
- `requirements.txt` aligned to match `pyproject.toml` dependency minimum versions

#### `ODMSchemaValidator` requires an explicit schema choice
- `odmlib/odm_parser.py`: `ODMSchemaValidator.__init__` no longer silently
  defaults to `standard="odm"`, `version="1.3.2"`. The signature is now
  `(xsd_file=None, standard: Optional[str] = None, version: Optional[str] = None)`.
  Callers must provide either an `xsd_file` path, or both `standard` and
  `version`; otherwise a `ValueError` is raised at construction time. The
  silent ODM 1.3.2 fallback was a footgun — for example, a Define-XML 2.1
  document could be validated against the ODM 1.3.2 schema without any
  warning. Existing call sites that already pass `standard=` and `version=`
  explicitly are unaffected. The `ValueError` hint explicitly points users
  with custom or local schemas (anything not in
  `schema_manager._MAIN_SCHEMA`) at the `xsd_file=<path>` escape hatch, so
  they don't accidentally fall back to a packaged schema lookup that
  doesn't apply to them.
- `tests/test_odm_validator.py`: new `TestODMValidatorConstructorContract`
  class with 8 tests locking in the new error contract (no-args raises,
  hint mentions `xsd_file=`, partial-args raises, both-args works, xsd_file
  works, xsd_file precedence, custom out-of-tree xsd works).

#### Schema-Ordered Child Serialization in `to_xml()`
- `odmlib/odm_element.py`: `ODMElement.to_xml()` now emits child elements
  in model declaration order (driven by `_elems`) instead of attribute
  insertion order (`self.__dict__`). Previously, when a user assigned
  child attributes in an order that diverged from the schema declaration
  — for example mutating `igd.Description.TranslatedText` after the
  list-typed `ItemRef` had already been pre-populated by `__init__`, or
  assigning `igd.Class` last — the saved XML put `<Description>` after
  the `<ItemRef>` block and `<def:Class>` after `<ItemRef>` but before
  `<def:leaf>` only by coincidence of the `__dict__` ordering. Define-XML
  2.1 XSD validation rejected such files.
- The fix matches what `verify_order()` and `reorder_object()` already
  trusted: declaration order from the class body, captured by `ODMMeta`
  into `_elems`. Users no longer need to call `reorder_object()` before
  serializing — assignment order is fully decoupled from emission order.
- `tests/test_schema_ordered_serialization.py` — 7 tests pinning the new
  behaviour: ItemDef/ItemGroupDef children come out in schema order
  regardless of assignment order; the Define-XML 2.1 ItemGroupDef pattern
  from `notebooks/first_define.ipynb` (`Description` → `ItemRef*` →
  `def:Class` → `def:leaf`) is locked in; unset optional children are
  silently skipped; attribute serialization and `_content` emission are
  unchanged.

### Fixed

#### XML Loader Namespace Handling
- `XMLDefineLoader` namespace mismatch: the default
  `ns_uri` was set to a Define-XML 2.0 default regardless of `model_package`,
  causing `def:`-namespaced child of `MetaDataVersion`
  (`Standard`, `CommentDef`, `ValueListDef`, `WhereClauseDef`, `leaf`,
  …) to be dropped when loading Define-XML 2.1 documents (when no ns_uri was provided). 
  The `ns_uri` argument is now `Optional[str]` and, when omitted, derived
  from `model_package` (`define_2_0` → `…/v2.0`, `define_2_1` → `…/v2.1`).
  Explicit values still override the derived default.
- `XMLODMLoader` `ns_uri` parameter was dead code: the constructor
  accepted an `ns_uri` argument but `_set_namespace` used the
  default ODM 1.3 URI. The parameter is now stored on the loader and used by
  `_set_namespace`; default is derived from `model_package` (`odm_1_3_2`
  → `…/v1.3`, `odm_2_0` → `…/v2.0`).
- `XMLArmLoader._set_registry` documented in-place: ARM 1.0 is
  intentionally paired with ODM 1.3 and Define-XML 2.1, no behavior
  change.
- New regression suite: `tests/test_loader_ns_defaults.py` — 12 tests
  covering Define 2.0/2.1 derivation, ODM 1.3.2/2.0 derivation, explicit
  override behavior, fallback for unknown `model_package`, and the
  end-to-end Define-XML 2.1 OID-index regression that reproduced the
  original bug report.
- `XMLODMLoader.__init__` no longer mutates the global
  `NamespaceRegistry` Borg singleton at construction time. Pre-fix,
  `__init__` unconditionally called `_set_namespace(None)`, which
  registered `odm → self.nos_uri` immediately. When users passed a
  non-canonical wrapper URI (e.g. `library-xml/v1.0` for the CDISC
  Library CDASH endpoint), the canonical `odm → http://www.cdisc.org/ns/odm/v1.3`
  mapping was silently overwritten in the global Borg, breaking any code
  in the same process that depended on it. `XMLODMLoader.__init__` now
  mirrors `XMLDefineLoader.__init__`: it stores `self.ns_uri` but assigns
  an empty `NamespaceRegistry()` view to `self.nsr` and defers the actual
  prefix registration to `create_document` /
  `create_document_from_string`. `create_document` was also updated to
  call `_set_namespace(namespace_registry)` unconditionally so that the
  deferred registration still happens when no caller-supplied registry
  is provided. The `nsr=` constructor argument continues to be honored
  immediately.
- `tests/test_loader_ns_defaults.py`: added
  `TestODMLoaderConstructionDoesNotMutateBorg` (4 tests) covering the
  no-mutation contract, the canonical-URI symmetry case, the explicit
  `nsr=` constructor argument, and deferred-registration-at-parse-time;
  updated `test_odm_explicit_ns_uri_now_takes_effect` to trigger the
  deferred registration before asserting on `loader.nsr`.

#### Trailing Spaces Removed
- Trailing space bugs in `odmlib/odm_1_3_2/rules/oid_ref.py` `_init_def_ref()`:
  `"SignatureOID "` corrected to `"SignatureOID"` and `"ItemOID "` corrected to `"ItemOID"`;
  these would have caused silent failures in `check_unreferenced_oids()`

#### Packaging
- `MANIFEST.in` typo: `test/data` corrected to `tests/data`
- Version inconsistency: was 0.1.4 (`setup.py`), 0.1.2 (`__init__.py`), 0.1.0 (`docs/`)
- Missing `odmlib.odm_2_0` package in build configuration (now auto-discovered via `packages.find`)

### Deprecation Notice

In v0.2.x, odmlib validation and type exceptions dual-inherit from `ValueError`/`TypeError` so that
all existing `except ValueError` and `except TypeError` clauses continue to work unchanged.

**v0.3.0 breaking change:** The `ValueError`/`TypeError` base classes will be removed. Update any
`except ValueError` → `except OdmlibValidationError` and `except TypeError` → `except OdmlibTypeError`
before upgrading to v0.3.0.

The manual `OIDRef` classes in `odmlib/odm_1_3_2/rules/oid_ref.py`,
`odmlib/define_2_0/rules/oid_ref.py`, and `odmlib/define_2_1/rules/oid_ref.py` are deprecated
in v0.2.0 and will be removed in v0.3.0.  Migrate to `create_oid_checker()`:

```python
# Before (deprecated):
from odmlib.odm_1_3_2.rules.oid_ref import OIDRef
checker = OIDRef()

# After:
from odmlib.oid_generator import create_oid_checker
checker = create_oid_checker("odm_1_3_2")
```

## [0.1.4] - Previous Release

- Last release using legacy `setup.py` packaging
- See git history for details

[Unreleased]: https://github.com/swhume/odmlib/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/swhume/odmlib/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/swhume/odmlib/releases/tag/v0.1.4
