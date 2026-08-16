# Changelog

All notable changes to odmlib will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-08-16

### Added — `to_element()`

- **`ODMElement.to_element()` returns a standard, namespace-resolved ElementTree Element.**
  Getting a tree out of odmlib previously meant `to_xml()`, which builds the library's
  internal serialization buffer: prefix-literal tags (`def:leaf`, not Clark notation) and
  **no** `xmlns` declarations. That tree cannot be re-parsed on its own for Define-XML
  (`ParseError: unbound prefix`), lands in no namespace for ODM, fails
  `ET.canonicalize()`, and does not support namespace-aware `find()`. `to_element()`
  returns a tree parsed from `to_xml_string()`, so all of those work:

  ```python
  elem = define.Study.MetaDataVersion.ItemGroupDef[0].to_element()
  elem.find("{http://www.cdisc.org/ns/def/v2.1}leaf")   # namespace-aware find
  host = ET.Element("SubmissionPackage"); host.append(elem)   # embeds correctly
  ET.indent(ET.ElementTree(elem))                       # pretty-prints and re-parses
  ```

  It costs one serialize + reparse — about 8 ms for a 166 KB Define-XML document.
  `DatasetJSONElement.to_element()` raises `NotImplementedError`, matching its sibling
  `to_xml` / `to_xml_string` / `write_xml` overrides. Pinned by
  `tests/test_xml_string_serialization.py::TestToElement`.

  **`to_xml()` is unchanged and is not deprecated** — it remains the shared tree builder
  behind `to_xml_string()` and `write_xml()`, and existing callers keep working. It has
  been demoted in the documentation from the head of the serialization list to a
  trailing "internal tree builder" entry; prefer `to_element()` when you want a tree.

  One caveat: re-serializing a `to_element()` tree with `ET.tostring()` picks prefixes
  from ElementTree's process-global `register_namespace()` map, so the prefix spelling
  may differ from the source (`odm:ODM` rather than a default `xmlns`). The namespaces
  are identical. Use `to_xml_string()` or `write_xml()` when exact output matters.

### Added — `to_xml_string(xml_declaration=True)`

- **`ODMElement.to_xml_string()` accepts a keyword-only `xml_declaration` flag.**
  The string path previously had no way to emit an XML declaration, so callers
  handing a string to a consumer that requires one had to prepend it by hand —
  and comparing a string against a `write_xml()` file silently disagreed on the
  first 39 bytes. The two paths now line up exactly:

  ```python
  odm.to_xml_string()                        # bytes write_xml() writes AFTER <?xml ...?>
  odm.to_xml_string(xml_declaration=True)    # exactly what write_xml() writes
  ```

  **The default stays `False`** — this string is the documented input to
  `ODMLoader.load_odm_string()` and 0.2.1 shipped it declaration-free, so
  flipping it would silently change output for every existing caller. The
  parameter is keyword-only. `dataset_json_1_1.model.DatasetJSON.to_xml_string()`
  accepts the same keyword so it still raises the intended `NotImplementedError`
  rather than a `TypeError`. Pinned by
  `tests/test_xml_string_serialization.py::TestXmlDeclarationOption`.

### Fixed — nested elements serialized with the wrong namespace

- **A nested element reached by walking a loaded tree now serializes with the
  namespaces its document was loaded under.** The per-document namespace
  snapshot was bound only to the objects the loader returns directly
  (`root()`, `Study()`, `MetaDataVersion()`, `create_odmlib()`). Anything
  reached by walking — `define.Study.MetaDataVersion` — had no snapshot and fell
  back to current global registry state, so merely importing a second Define
  model package changed its output:

  ```python
  import odmlib.define_2_0.model            # re-registers def: -> v2.0 globally
  define.to_xml_string()                    # root:   xmlns:def=".../def/v2.1"  (right)
  define.Study.MetaDataVersion.to_xml_string()   # nested: ".../def/v2.0"  (WRONG)
  ```

  `ns_registry.bind_document_namespaces()` takes a new `recursive=False`
  parameter, and `loader.ODMLoader._bind_namespaces()` passes `recursive=True`,
  which covers all four loader entry points and the `open_odm`/`open_define`
  context managers. `write_xml()` on a nested element is fixed by the same
  change. Measured cost: 1.4 ms to bind all 2 086 elements of a 136 KB
  Define-XML file, sharing one snapshot dict. Pinned by
  `tests/test_xml_string_serialization.py::TestNestedElementNamespaceBinding`.

  **Residual limitation:** an element *constructed after* the load and grafted
  in still carries no snapshot and uses global state. Bind it explicitly:

  ```python
  import odmlib.ns_registry as NS
  NS.bind_document_namespaces(new_elem, NS.get_document_namespaces(root))
  ```

### Deprecated — `NamespaceRegistry.set_odm_namespace_attributes_string()`

- **Emits `OdmlibDeprecationWarning`; will be removed in 0.3.0.** Since 0.2.1
  `to_xml_string()` declares its own namespaces, which makes this string-patching
  helper a no-op on any string it would normally be given. It has no callers in
  odmlib. Remove the call; no replacement is needed.

### Changed — a misnamed serialization test

- **`test_schema_ordered_serialization.py::test_to_xml_string_round_trip_unchanged`
  never called `to_xml_string()`** — it used raw `ET.tostring()`, which is false
  coverage of exactly the path that went untested. Renamed to
  `test_to_xml_element_order_survives_reparse` (its body is a valid element-order
  test) and a real `to_xml_string()` round-trip added beside it as
  `test_to_xml_string_round_trip_preserves_order`.

### Added — ARM 1.0 XSD schema validation

- **ARM documents can now be schema-validated against a bundled CDISC XSD.**
  Previously odmlib shipped no ARM schema, so validating Analysis Results
  Metadata meant supplying your own via `xsd_file=`. Two schema sets are now
  bundled under `odmlib/schemas/arm/`, registered in
  `schema_manager._MAIN_SCHEMA` and reachable through the existing
  `ODMSchemaValidator` API:

  ```python
  from odmlib.odm_parser import ODMSchemaValidator
  validator = ODMSchemaValidator(standard="arm", version="1.0-define2.1")
  validator.validate_file("define-adam.xml")
  ```

  | `(standard, version)` | Validates |
  |---|---|
  | `("arm", "1.0")` | ARM 1.0 in a Define-XML 2.0 document (CDISC original) |
  | `("arm", "1.0-define2.1")` | ARM 1.0 in a Define-XML 2.1 document |

  Two sets are required because ARM layers onto Define-XML, and Define-XML 2.0
  and 2.1 use different `def:` namespace URIs — the pairings are not
  interchangeable. Use `"1.0-define2.1"` with `odmlib.arm_1_0`, which extends
  `odmlib.define_2_1`. The `1.0-define2.1` schema set is derived by odmlib from
  the CDISC ARM 1.0 schema by retargeting the Define-XML dependency; element and
  type declarations are unchanged from the original.

  Both ARM schemas are supersets of their base Define-XML schema, so either also
  validates an ARM-free Define-XML document of the matching version.

### Fixed — ARM `AnalysisResult` serialized in a schema-invalid element order

- **`arm_1_0.model.AnalysisResult` declared its child elements in the wrong
  order,** so every ARM document odmlib wrote failed XSD validation. Descriptor
  declaration order is serialization order, and the ARM schema requires the
  sequence `Description, AnalysisDatasets, Documentation, ProgrammingCode`;
  the model declared `AnalysisDatasets` last. `AnalysisDatasets` has been moved
  ahead of `Documentation`. Reading ARM documents was unaffected — only output
  was wrong, which went unnoticed while no ARM XSD was bundled to check it.

### Fixed — `collect_errors=True` now collects every error

- **`validate(collect_errors=True)` returned at most three errors.** It wrapped
  each of its three validation layers in a single `try/except`, and every layer
  was itself fail-fast, so the returned list held at most one error per layer
  no matter how broken the document was. A document with 50 misordered elements
  reported 1. Each layer now enumerates every problem it finds
  (`odm_element.py`, `oid_generator.py`, `exceptions.py`):
  - **Order**: one error per misordered element; the walk now recurses into the
    children of a misordered element instead of aborting.
  - **OID**: one error per duplicate OID and per bad reference. A duplicate no
    longer aborts the traversal, so the reference checks — which previously
    never ran at all once a duplicate was found — now execute. On a duplicate
    the *first* definition is kept.
  - **Conformance**: the bundled Cerberus result is expanded into one
    `OdmlibConformanceError` per failing field, each with a dotted `field_path`
    and the complete raw dict still on `cerberus_errors`.

  **Behaviour change:** `len(errors)` may now be larger than before for the
  same document, and errors are no longer at predictable list positions —
  filter by exception type rather than by index. Fail-fast mode
  (`collect_errors=False`, the default) is unchanged.

### Added
- **`validate(max_errors=N)`**: caps collection on a badly broken document.
  Validation stops the moment the cap is reached — enforced inside each layer,
  not by truncating afterwards — and a final `OdmlibErrorLimitError` is
  appended, so the list holds at most `N + 1` entries. Defaults to `None`
  (uncapped).
- **Collecting-checker protocol** (`odmlib.exceptions`): the `ErrorReporting`
  mixin (`report()` / `collecting()`) and the `is_collecting_checker()`
  capability check. `DynamicOIDRef` implements it; the deprecated manual
  `OIDRef` classes and duck-typed custom checkers do not and degrade gracefully
  to one error for the OID layer. `verify_oids()` also collects when a sink is
  installed via `with checker.collecting(collector):`.
- **`DynamicOIDRef.reset()`**: clears accumulated OID state so one checker can
  validate a second document. `validate()` now warns in collect mode when
  handed a checker that still holds state from a previous run.
- **`flatten_cerberus_errors()`** and `OdmlibConformanceError.expand()` /
  `.field_path` for per-field conformance reporting.
- `ErrorCollector` accepts `max_errors` and exposes `is_full` / `truncated`.
  Uncapped collectors never raise, so existing usage is unaffected.

### Changed
- `DynamicOIDRef.check_oid_refs` iterates its reference sets in sorted order.
  Previously *which* bad reference was reported first varied with
  `PYTHONHASHSEED`; error ordering is now deterministic in both modes.

### Fixed — validation correctness (code-review remediation)
- **Cerberus schema isolation**: each `MetadataSchema` now uses a private
  `SchemaRegistry` instead of the process-global `cerberus.schema_registry`.
  Previously, instantiating checkers for two model versions (e.g. ODM 1.3.2
  and Define-XML 2.1) silently corrupted each other's schemas — the last
  checker instantiated won for every shared schema name, rejecting valid
  documents and accepting invalid ones. (`*/rules/metadata_schema.py`)
- **Define-XML leaf references are now validated**: `leaf/@ID` definitions and
  `DocumentRef/@leafID` / `ItemGroupDef/@def:ArchiveLocationID` references are
  surfaced to the OID checkers. A dangling `leafID` previously passed
  `verify_oids()` silently. (`odm_element.py`, `oid_generator.py`)
- **Duplicate OIDs on skip-listed elements are now detected**:
  `DynamicOIDRef.add_oid` checks uniqueness before honouring `skip_elem`, so
  duplicate `ItemGroupDef` OIDs in Define-XML are caught (skip_elem now only
  exempts an element from reference-target checking).
- **Deprecated manual `OIDRef` crash guards**: `add_oid_ref` no longer raises
  `KeyError` on unregistered attributes (e.g. `SignatureOID`), and
  `check_unreferenced_oids` no longer raises `KeyError` for element types
  missing from `def_ref` (all three model packages).
- **Conformance schema drift**: `Presentation` added to the ODM 1.3.2
  `MetaDataVersion` cerberus schema (valid documents were rejected as
  "unknown field"); `Repeating` is now `required` for
  StudyEventDef/FormDef/ItemGroupDef, matching the model and the spec.
- **Valueset lookup follows inheritance**: `ValidValues` resolves the
  `ClassName.attr` valueset key via the MRO, so subclasses of model classes
  keep their parents' valueset validation.

### Fixed — namespaces and serialization
- **Per-document namespaces**: documents loaded via `ODMLoader` remember the
  namespace registry state they were loaded under; `write_xml()` and
  `to_xml_string()` use that snapshot, so loading a second document (e.g.
  ODM 2.0 after ODM 1.3.2) no longer changes the `xmlns` a previously loaded
  document serializes with. (`ns_registry.py`, `loader.py`, `odm_element.py`)
- **`to_xml_string()` output is namespace-well-formed**: it now includes
  `xmlns` declarations (previously prefixed tags like `def:ValueListDef`
  had no declaration anywhere, so the string could not be re-parsed).
  `set_odm_namespace_attributes_string()` is a no-op on such strings.
- **Only used prefixes are declared**: serialization emits `xmlns:` entries
  only for prefixes actually present in the tree, so importing an unrelated
  model package (arm/ct/dataset) no longer pollutes output; the redundant
  `xmlns:xml` declaration is gone (the `xml` prefix is reserved).
- **ARM namespace registration**: `arm_1_0` no longer registers itself as the
  *default* namespace (import-order dependent corruption); the registry now
  keeps a single default (a new default replaces the previous one), and an
  empty registry raises `OdmlibNamespaceError` instead of `IndexError`.

### Fixed — parsing and loading
- **Security — DOCTYPE rejection**: XML parsing rejects documents containing a
  DOCTYPE declaration (billion-laughs / entity-expansion DoS defense) via a
  cheap expat prolog pre-scan; ODM never requires DTDs. (`odm_parser.py`)
- **Clear parse errors**: malformed XML/JSON and unknown root elements now
  raise `OdmlibParsingError` (with hints) instead of raw `ParseError`,
  `JSONDecodeError`, or `AttributeError` (all six loaders + parser).
- **Encoding**: JSON reads use `utf-8-sig` (BOM tolerant) and JSON/XML writes
  use UTF-8 explicitly, instead of the platform default encoding.
- **ODM 2.0 clinical data parsing**: `ODMParser.AdminData/ClinicalData/
  ReferenceData` honour the configured namespace registry instead of a
  hardcoded ODM v1.3 URI (they silently returned `[]` for ODM 2.0 documents).

### Fixed — object model
- **Auto-created children no longer leak into output**: reading an unset
  optional child element still auto-creates it (the
  `rc.ErrorMessage.TranslatedText.append(...)` idiom is preserved) but
  serialization skips auto-created elements that were never populated —
  read-only inspection previously injected spurious empty elements (e.g.
  `<BasicDefinitions/>`) into XML/JSON output. Reading a child whose class
  has required attributes returns `None` instead of relying on the
  deprecated `ValueError` base of `OdmlibRequiredAttributeError`.
- **`find`/`find_all`/`find_by` guards**: searching an unset single child or
  a scalar attribute name returns `None`/`[]` instead of raising
  `AttributeError`.
- **Restricted subclasses are now consistent**: assigning a field that a
  subclass deliberately dropped (e.g. `Question` on a Define-XML `ItemDef`)
  raises `OdmlibTypeError` instead of silently storing a value that
  serialized inconsistently or not at all; constructor kwarg checking and
  the required-attribute check now use the class's effective field set.
- **Single-child type validation**: an `ODMObject` descriptor validates the
  items when a list is assigned (previously ANY list was accepted unchecked).
- **ODMBuilder scope pointers**: `add_study`/`add_metadata_version`/
  `add_item_group_def` clear stale current-element pointers, so
  `with_description()`/`with_alias()` no longer attach to a previous
  ItemDef/MetaDataVersion after a new scope opens.
- **Converter dataset-name collisions**: `dataset_xml_to_dataset_json` warns
  and keys a colliding dataset by its full `ItemGroupOID` instead of
  silently overwriting (e.g. `IG.AE` vs `SUPP.AE` both deriving "AE").
- **DataFrame row drops are visible**: `dataframe_to_items` warns (with row
  index and reason) for rows that fail element construction instead of
  silently returning fewer elements.

### Added
- **`merge_fields=True` class keyword** for model subclassing: a subclass
  declared as `class MyItemDef(ODM.ItemDef, merge_fields=True)` inherits all
  base-class fields/elements without redeclaring them (redeclaring a field
  moves it to the subclass position). The default remains the historical
  declare-from-scratch behaviour that the Define-XML models use to restrict
  inherited ODM fields. (`ODMMeta`)
- **Context managers are read-only by default** (breaking): `open_odm()` /
  `open_define()` without an `output_file` no longer rewrite the input file
  on exit. Writing requires an explicit `output_file`, or `write_on_exit=True`
  to opt in to an in-place update.

### Performance
- Format-validation regexes (datetime/partial/incomplete/SAS names) are
  compiled once at import instead of on every attribute assignment.
- Compiled XML schemas are cached by path (`ODMSchemaValidator` no longer
  recompiles the XSD per instance); cerberus `Validator` objects are cached
  per `MetadataSchema` instance.
- Removed no-op filter-dict allocations from the `to_dict`/OID/order
  traversals; Define manual checkers set `is_verified` so
  `unreferenced_oids()` no longer re-runs the full verification walk;
  `dataframe.py` avoids `iterrows`.

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

[Unreleased]: https://github.com/swhume/odmlib/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/swhume/odmlib/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/swhume/odmlib/compare/v0.1.4...v0.2.0
[0.1.4]: https://github.com/swhume/odmlib/releases/tag/v0.1.4
