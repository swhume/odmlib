---
name: odmlib
description: >-
  Build reliable Python applications that read, write, create, validate, convert, or
  transform CDISC ODM, Define-XML, Dataset-JSON, and Analysis Results Metadata (ARM)
  using the odmlib library. Use this skill whenever a developer works with ODM-family
  content in Python — parsing or generating study metadata, ItemGroupDef / ItemDef /
  CodeList / MethodDef, MetaDataVersion structures, Define-XML documents (define.xml),
  Dataset-JSON datasets, ARM analysis results, or extensions of these models. Trigger it
  when a task mentions odmlib, an .xml/.json ODM / Define-XML /
  Dataset-JSON document, CDISC study metadata, or clinical-trial data definitions — and
  ALSO when odmlib is not named but the user is clearly creating, loading, modifying,
  validating, merging, serializing, or round-tripping CDISC ODM-family metadata in Python.
  Hand-rolling XML or JSON for these standards is error-prone; odmlib is the canonical,
  schema-aware way to do it right, so prefer this skill over building the markup by hand.
---

# odmlib: working with CDISC ODM, Define-XML, Dataset-JSON, and ARM

`odmlib` is a Python library that turns the CDISC ODM family of standards into a typed,
object-oriented model. You work with Python objects (`ODM`, `Study`, `MetaDataVersion`,
`ItemGroupDef`, `ItemDef`, `CodeList`, …) and let odmlib handle the parts that are
tedious and easy to get wrong by hand: schema-mandated element order, namespace prefixes
and URIs, OID definition/reference integrity, controlled-terminology value sets, and the
differences between the XML and JSON serializations.

## The core principle: don't hand-build the markup

When a task involves ODM, Define-XML, Dataset-JSON, or ARM, **model it with odmlib
objects rather than assembling XML strings or JSON dicts directly.** This is the whole
point of the library. Hand-written ODM markup almost always drifts from the standard —
children emitted in the wrong order, a missing `def:` namespace, an `ItemRef` pointing at
an `ItemOID` that no `ItemDef` defines, a `CodeListRef` with no matching `CodeList`. Those
documents may look fine and still fail schema validation or a regulatory load. odmlib
encodes the rules, so a correctly built object tree serializes to conformant output.

If you ever find yourself writing `ElementTree` calls, f-string XML, or raw JSON for one
of these standards, stop and use the model instead. This applies on the way *out* too:
`ET.tostring(obj.to_xml())` looks like the obvious way to get XML text from an odmlib
object and is broken — use `to_xml_string()`. See
*Serializing to a string, not a file* below for why.

## First steps for any odmlib task

1. Confirm odmlib is available and note the version: `python -c "import odmlib; print(odmlib.__version__)"`. If it is missing, `pip install odmlib`.

   > **This skill describes odmlib 0.2.1 and later.** It lives in the odmlib repository at
   > `.claude/skills/odmlib/` and is **not** part of the PyPI package — installing odmlib
   > does not install the skill. To install it, copy that directory into a project's
   > `.claude/skills/`, or into `~/.claude/skills/` to make it available everywhere.
   > 0.2.1 is the single floor for everything below, including all of *Serializing to a
   > string, not a file*.
   > On **0.2.0** `to_xml_string()` is merely `ET.tostring(self.to_xml())` and emits **no
   > `xmlns` at all** — Define-XML output will not re-parse (`ParseError: unbound prefix`)
   > and ODM output re-loads with `FileOID` intact and **every `Study` silently gone**. If
   > you are on 0.2.0, upgrade before writing serialization code.

   **Detect capabilities; do not compare version strings.** A version number is the wrong
   gate here: under PEP 440 a pre-release sorts *below* its release (`0.2.1.dev0 < 0.2.1`),
   the same `.dev` string names a different tree on different days, and a skill copied into
   `~/.claude/skills/` outlives any venv up- or downgrade. Two lines settle it:

   ```python
   import inspect
   from odmlib.odm_element import ODMElement

   has_xml_decl  = "xml_declaration" in inspect.signature(ODMElement.to_xml_string).parameters
   has_to_element = hasattr(ODMElement, "to_element")
   ```

   Where a comparison is genuinely unavoidable, parse — never compare strings with `>=`:

   ```python
   from packaging.version import Version
   Version(odmlib.__version__) >= Version("0.2.1.dev0")   # admits pre-releases of the floor
   ```

2. Identify the **standard and version** in play, which picks the *model package*:

   | Standard | Model package | Notes |
   |---|---|---|
   | ODM 1.3.2 | `odm_1_3_2` | Default; uses `GlobalVariables` (StudyName/Description/ProtocolName) |
   | ODM 2.0 (draft) | `odm_2_0` | No `GlobalVariables`; StudyName/ProtocolName are scalar attributes, Description is an object |
   | Define-XML 2.1 | `define_2_1` | Adds the `def:` namespace and Define-specific elements |
   | Dataset-JSON 1.1 | `dataset_json_1_1` | One dataset per file; column metadata + row arrays |
   | ARM 1.0 | `arm_1_0` | Analysis Results Metadata, layered on Define-XML |

   ODM 1.3.2 and ODM 2.0 differ structurally — see `references/models.md` before mixing
   them up. Define-XML 2.1 is itself an ODM extension, so it is loaded as Define, not ODM.
3. Decide which API altitude fits the task (next section).
4. **Validate** anything you create or modify before treating it as done (see Validation).

## Choosing your approach

odmlib offers two equally valid entry points for loading/saving and two for creating.
Pick by the situation, not by habit — they interoperate freely (every approach yields the
same `ODMElement` objects).

**Loading and saving an existing file**

- **Context-manager facade** — `open_odm()` / `open_define()` from `odmlib.context`. Best
  for the common load → modify → save (or read-only) workflow. It auto-detects XML vs JSON
  from the extension and derives the namespace from the model package. **Writing is
  opt-in** (since 0.2.1): a bare `open_odm("study.xml")` loads read-only and writes nothing
  on exit. Enable writing one of two ways — pass `output_file=` to write the result
  somewhere else, or `write_on_exit=True` to update the input file in place. Least code,
  hardest to misuse.
- **Explicit loader** — `LD.ODMLoader(OL.XMLODMLoader(...))` / `DL.XMLDefineLoader(...)` /
  `AL.XMLArmLoader(...)`. Reach for this when you need to override the namespace URI
  (`ns_uri=`), pull a specific `MetaDataVersion(idx)` or `Study(idx)` without loading the
  rest, load from a string, use a custom/local model, or work with ARM or CT-XML. This is
  the idiom in the odmlib docs and examples, and the facade is a thin wrapper over it.

See `examples/read_modify_write.py` (facade) and `examples/load_with_loader.py` (explicit).

**Creating a document from scratch**

- **Fluent builder** — `ODMBuilder` from `odmlib`. A guided, chainable API
  (`.add_study(...).add_metadata_version(...).add_item_group_def(...)`) that constructs the
  right study shape for the active model and keeps children in order. Best default for
  generating a new document, especially when the structure is regular. Add CodeLists inline
  with `add_code_list(OID, Name, DataType, items=[...])` — `{"CodedValue": "M", "Decode":
  "Male"}` makes a CodeListItem, `{"CodedValue": "SYSBP"}` (no Decode) makes an
  EnumeratedItem. For elements with no dedicated `add_*`/`with_*` method (Include,
  ArchiveLayout, ExternalCodeList, element-level Description/Alias, …), use the escape hatch:
  `builder.attach(parent, element)` or `attach_to_current(element)`, reaching the active
  parents via `builder.current["mdv" | "item_def" | "form_def" | "study_event_def"]`. The
  builder targets ODM (1.3.2 and 2.0); build Define-XML with direct model construction.
- **Direct model construction** — instantiate model classes (`ODM.ODM(...)`,
  `ODM.Study(OID=...)`, …) and assign/append children yourself. Use when you need full
  control, are building Define-XML or an unusual structure, or are creating a proprietary
  extension. You own element order here — serialization emits children in model order, but
  call `verify_order()` / `reorder_object()` if you build via `to_dict`/`to_json` paths.

See `examples/create_odm.py` (both styles) and `examples/define_roundtrip.py`.

**Converting and Dataset-JSON**

- Dataset-JSON documents use the `DatasetJSON` / `Column` model classes (importable from the
  top-level `odmlib` namespace). The v1.1 wire format is **NDJSON** — write with
  `ds.write_ndjson(path)` and read with `DatasetJSON.read_ndjson(path)` (`write_json` /
  `from_dict` handle plain JSON too). To turn a Define-XML document into tabular datasets,
  `DefineFlattener(odm).flatten_all()` returns named `DatasetJSON` datasets and
  `.write_all(dir)` writes them. See `references/dataset-json.md` and
  `examples/dataset_json_roundtrip.py`.

## The two load idioms, side by side

```python
# Facade — three write modes; writing is OPT-IN
from odmlib.context import open_odm

# 1. Default: READ-ONLY. Nothing is written on exit, edits inside are discarded.
with open_odm("study.xml") as odm:
    mdv = odm.Study[0].MetaDataVersion[0]           # ODM: Study/MDV are LISTS
    print(len(mdv.ItemGroupDef))

# 2. output_file= : load one file, write the modified document to another.
with open_odm("study.xml", output_file="study_v2.xml") as odm:
    odm.FileOID = "ODM.STUDY.V2"                    # -> study_v2.xml, input untouched

# 3. write_on_exit=True : update the input file IN PLACE.
with open_odm("study.xml", write_on_exit=True) as odm:
    odm.FileOID = "ODM.STUDY.V2"                    # -> overwrites study.xml

# Explicit loader — namespace control, partial loads, strings, ARM/CT
import odmlib.odm_loader as OL
import odmlib.loader as LD
loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
loader.open_odm_document("study.xml")
odm = loader.root()                  # whole document
mdv = loader.MetaDataVersion()       # just the first MetaDataVersion (NOT a list)
```

For Define-XML 2.1 via the explicit loader, pass the model package explicitly — the
Define loader's own default is `define_2_0`. **Also note the shape difference:** in the
Define-XML (and ARM) models, `Study` and `MetaDataVersion` are *single objects*, not lists:

```python
import odmlib.define_loader as DL
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
loader.open_odm_document("define.xml")
define = loader.root()
mdv = define.Study.MetaDataVersion        # Define/ARM: SINGLE objects — no [0]
print(len(mdv.ItemGroupDef), len(mdv.ItemDef))
```

## Validation discipline — make it the default, not an afterthought

Treat a generated or modified document as unfinished until it validates. odmlib gives one
unified entry point, `ODMElement.validate()`, that runs up to three independent checks.
`collect_errors=True` returns **every** problem all three layers can find, in one pass:

```python
from odmlib import create_oid_checker
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema

errors = odm.validate(
    collect_errors=True,
    oid_checker=create_oid_checker("odm_1_3_2"),   # OID uniqueness + def/ref integrity
    conformance_checker=MetadataSchema(),          # required attrs, value sets, types
    max_errors=100,                                # optional cap; None (default) = all
)
if errors:
    for e in errors:
        print(e)            # rich messages carry element_path + a fix hint
```

What the three layers catch, and what each contributes to the list:

- **Element order** (`verify_order`, always run) — children declared in the wrong sequence.
  One error per misordered element; the walk recurses into a misordered element's children,
  so a single pass lists everything `reorder_object()` needs to fix.
- **OID integrity** (`oid_checker`) — duplicate OIDs, and `*Ref` attributes (`ItemOID`,
  `CodeListOID`, …) that point at OIDs no element defines. This is the single most common
  defect in hand-built documents. One error per duplicate and per bad reference.
- **Conformance** (`conformance_checker`) — missing required attributes, invalid value-set
  values, wrong types, against a Cerberus schema generated from the model. One error per
  failing field, each carrying a dotted `field_path` like `"ItemGroupDef.0.Name"`.

So `validate(collect_errors=True)` is both a gate *and* a report: a document with five
dangling OID references returns five `OdmlibOIDError`s. Because the count is unbounded,
**filter by exception type rather than by list position** — errors are no longer at
predictable indices:

```python
from odmlib import OdmlibOIDError
oid_problems = [e for e in errors if isinstance(e, OdmlibOIDError)]
```

Two things to know when relying on this:

- **`max_errors=N` caps the list.** Collection stops as soon as the cap is hit — enforced
  inside each layer, not by truncating afterwards — and a final `OdmlibErrorLimitError` is
  appended, so the list holds at most `N + 1` entries. Useful on badly broken documents.
- **The deprecated `rules/oid_ref.py` `OIDRef` classes do not enumerate.** They contribute
  at most one error for the whole OID layer. Use `create_oid_checker(...)` to get full
  reporting; `is_collecting_checker(checker)` tells you which kind you have.

`collect_errors=False` (the default) is unchanged: fail-fast, returns `True` or raises the
first error. Only `OdmlibError` subclasses are collected — a bug in a custom checker or an
`AttributeError` from a malformed tree still propagates rather than being reported as a
document defect.

For full **XSD/schema validation**, odmlib *bundles* the official ODM, Define-XML, and ARM
schemas, so you don't download anything: `ODMSchemaValidator(standard="define",
version="2.1")` (valid pairs: `("odm","1.3.2")`, `("odm","2.0")`, `("define","2.0")`,
`("define","2.1")`, `("arm","1.0")`, `("arm","1.0-define2.1")`). Use
`validator.xsd.iter_errors(file)` to collect every schema error with its `.reason` and
`.path` — note that it accepts a *string* of XML as readily as a path, but that it **raises
`xmlschema.exceptions.XMLResourceParseError` on input that is not well-formed XML** instead of
yielding, so parse with `ET.fromstring()` first if a crash is not the outcome you want. Pass
`xsd_file=` only for a custom/local schema. For ARM (ADaM), pick the pairing
matching the document's Define-XML version — `("arm","1.0-define2.1")` is what `arm_1_0`
models; the two are not interchangeable. Conformance and XSD validation are complementary —
see `references/validation.md`.

### Loading non-conformant files: permissive mode, then repair

Strict loading (the default) rejects files that violate the standard. To load a broken or
legacy file *in order to inspect or fix it*, wrap the load in permissive mode, then return
to strict and validate once repaired:

```python
from odmlib import permissive, ValidationMode
from odmlib.context import open_define

# write_on_exit=False is belt-and-braces here — the default is already read-only
with open_define("broken.xml", permissive=True, write_on_exit=False) as define:
    ...  # inspect; relaxed checks while inside the block

# or target just one category of check:
with permissive(ValidationMode.SKIP_REQUIRED):
    ...
```

Permissive mode is for *reading and repairing*, not for emitting output — fix the issues,
drop back to strict, and validate before you write.

## Analyzing a document you did not build

Auditing or reporting on an existing file is a different job from gating one you just
created, and the API rewards it differently:

1. **Load permissively.** A file worth auditing is often a file strict mode refuses.
2. **Expect non-`OdmlibError` failures at the load boundary.** Malformed XML and an
   unrecognized root raise `OdmlibParsingError`, but a bad path raises
   `FileNotFoundError`/`IsADirectoryError`, which are *not* `OdmlibError`. Catch broadly
   around the loader calls only. See `references/api-reference.md` → *Loading files you do
   not control*.
3. **`validate(collect_errors=True)` is the right enumeration tool.** It lists every
   misordered element, every duplicate OID, every dangling reference, and every failing
   conformance field. Pass `max_errors=` to keep the output manageable on a badly broken
   file. Reach past it only for the things it genuinely does not cover (next two items).
4. **What `validate()` still won't tell you:** which OIDs are *defined but never referenced*
   (`unreferenced_oids(checker)`), and *where* a given OID is used
   (`build_oid_index().find_all(oid)`). `create_oid_checker(pkg)` also exposes `ref_def`,
   `def_ref`, `oid`, `oid_ref`, `oid_defs`, `skip_attr`, and `skip_elem` if you want to
   build an OID inventory. Full example: `examples/report_oid_integrity.py`.
5. **`unreferenced_oids(checker)` returns a `dict`** (orphan OID → expected ref attribute).
   It is noisier under `odm_*` than `define_*`, which
   already skips the structural elements. Call it on a checker that has already been through
   a **collect-mode** `validate()` — after a *fail-fast* duplicate failure the checker is
   left half-populated and `unreferenced_oids()` raises a misleading duplicate error naming
   an OID that is not actually duplicated.
6. **`build_oid_index()` → `.find_all(oid)`** turns any OID back into the objects that carry
   it — better than hand-rolled loops for "where is this used?".

## Common gotchas (and why they matter)

- **Text in the element body uses `_content`.** `ODM.StudyName(_content="My Study")`, not a
  positional string — odmlib distinguishes attributes from element body text.
- **`Study` and `MetaDataVersion` are lists in ODM but single objects in Define-XML/ARM.**
  This is the single most common mistake. In `odm_1_3_2`/`odm_2_0` they are lists, so index
  them: `odm.Study[0].MetaDataVersion[0]`. In `define_2_1`/`arm_1_0` they are single objects,
  so do *not* index: `define.Study.MetaDataVersion`, `define.Study.OID`. Writing
  `define.Study[0]` raises. (Repeating children inside an MDV — `ItemGroupDef`, `ItemDef`,
  `CodeList` — are lists in every model.)
- **Locate an element by OID with `find`.** `mdv.find("ItemDef", "OID", "IT.AGE")` returns the
  first match (or `find_by("ItemDef", OID="IT.AGE")`). Don't loop by hand.
- **`loader.MetaDataVersion()` returns one object, not a list** (the first by default; pass
  an index for others). This trips people who expect a collection.
- **ODM 1.3.2 ≠ ODM 2.0 study shape.** 1.3.2 wraps study identity in `GlobalVariables`; 2.0
  uses scalar `StudyName`/`ProtocolName` plus an object `Description`. The builder handles
  both; raw construction does not.
- **Define-XML is loaded as Define, not ODM**, with the `define_2_1` package, and the
  explicit Define loader defaults to `define_2_0` — set the version you mean.
- **An OID checker is single-use per document.** `verify_oids()` accumulates every OID into
  the checker, so reusing one reports a *false* "OID … is not unique" for every OID in the
  next document. Either build a fresh `create_oid_checker(...)` per pass — every loop
  iteration, every document in a batch — or call `checker.reset()` between runs. In collect
  mode `validate()` warns (`OdmlibWarning`) when handed a checker that still holds state,
  so you get a nudge rather than a wall of bogus duplicates.
- **Catch `odmlib` exceptions, not bare `ValueError`/`TypeError`.** Use `OdmlibError` (or a
  specific subclass like `OdmlibOIDError`, `OdmlibConformanceError`). In 0.2.x they still
  also inherit `ValueError`/`TypeError` for compatibility, but that dual inheritance is being
  removed in 0.3.0, so write `except OdmlibError` now to stay future-proof.

### Serializing to a string, not a file

> **Read `references/api-reference.md` → *Serialization details* before writing serialization
> code.** It carries the exact signatures, the `to_element()` re-serialization caveat, and the
> `ns_registry` binding helpers. Needs odmlib **0.2.1** — see the version floor in *First steps*.

`to_xml_string()` is the string path, and it is the *only* one that carries its own namespace
declarations. It works on **any** element, not just the document root, and it declares the
default namespace plus every prefix actually used in that subtree (the reserved `xml` prefix is
never declared). The result is namespace-well-formed and can be re-parsed or schema-validated on
its own:

```python
xml_str = odm.to_xml_string()                      # self-contained; no fixup needed
loader.load_odm_string(xml_str)                    # round-trips back into objects
ODMSchemaValidator(standard="define", version="2.1").xsd.iter_errors(xml_str)  # takes a STRING
```

Two things that catch people out here:

- **`iter_errors()` raises on malformed XML rather than yielding.** It reports *schema* errors,
  but a string that is not well-formed XML at all raises `xmlschema.exceptions.XMLResourceParseError`
  out of the generator instead of appearing in the results. If you are validating a string that
  might be broken (a fixture, something you mutated, output from another tool), parse it with
  `ET.fromstring()` first — a `ParseError` there is a diagnosis; the raise from `iter_errors()`
  is a crash.
- **XSD validation of a string does not replace `validate()`.** A schema pass says the markup is
  structurally legal; it says nothing about duplicate OIDs, `*Ref` attributes pointing at OIDs no
  element defines, or missing required attributes the schema happens not to mandate. Run
  `validate(collect_errors=True, oid_checker=..., conformance_checker=...)` as well — step 5 of
  *A reliable working loop* below. This matters most for a document you **built** rather than
  loaded, which is exactly when the string path is in play.

**Never `ET.tostring(obj.to_xml())`.** `to_xml()` builds a *serialization buffer*, not a
document: it emits prefix-literal tags (`def:leaf`, not Clark notation) and adds **no** `xmlns`
at all — declarations are attached by `to_xml_string()` and by `ODMWriter.write_odm`, never by
`to_xml()`. The two failure modes are asymmetric, and the quiet one is the dangerous one:

- **Define-XML fails loudly** — `ET.fromstring(ET.tostring(define.to_xml()))` raises
  `ParseError: unbound prefix`.
- **ODM 1.3.2 fails silently** — it parses fine, *into no namespace*. odmlib will re-load that
  string, `FileOID` reads back correctly, and **every `Study` is gone** (`len(odm.Study) == 0`),
  with no exception raised. A smoke test passes; the data is lost.

**When you want a tree, use `to_element()`.** It parses `to_xml_string()`, so you get Clark
notation (`{http://www.cdisc.org/ns/def/v2.1}leaf`) and namespace-aware `find()`,
`ET.canonicalize()`, `ET.indent()` pretty-printing and grafting into a host document all work:

```python
elem = define.Study.MetaDataVersion.ItemGroupDef[0].to_element()
elem.find("{http://www.cdisc.org/ns/def/v2.1}leaf")          # resolves
ET.Element("SubmissionPackage").append(elem)                 # embeds correctly
```

It costs one serialize + reparse (~8 ms for a 166 KB Define document). `to_xml()` is the
internal tree builder behind `to_xml_string()` and `ODMWriter` — not something to call.

**String vs file.** `write_xml()` writes the XML declaration and then exactly the bytes
`to_xml_string()` returns. The keyword that closes the 39-byte gap lives on
**`to_xml_string()`** — not on `write_xml()`:

```python
.to_xml_string(*, xml_declaration: bool = False) -> str     # keyword-only

# both of these hold exactly, for ODM and Define alike:
file_bytes == b"<?xml version='1.0' encoding='UTF-8'?>\n" + obj.to_xml_string().encode("utf-8")
file_bytes == obj.to_xml_string(xml_declaration=True).encode("utf-8")
```

Reach for `to_xml_string(xml_declaration=True)` when a consumer needs the declaration — a file
you write yourself, a byte-for-byte comparison against `write_xml()` output. The default stays
`False`, which is what `load_odm_string()` expects. Do not compare a string to a file without
accounting for that difference.

**Namespaces on nested elements.** Loading captures a per-document namespace snapshot, and the
loader binds it *recursively*, so a child reached by walking the tree serializes exactly like its
root even after another model package changes the global registry:

```python
mdv = define.Study.MetaDataVersion       # bound recursively at load time
import odmlib.define_2_0.model           # re-registers def: -> v2.0 globally
define.to_xml_string()                   # root:   xmlns:def=".../def/v2.1"
mdv.to_xml_string()                      # nested: xmlns:def=".../def/v2.1"  (same)
```

**The one case still not covered:** an element you *construct after the load* and graft in has no
snapshot and falls back to current global state. Bind it explicitly:

```python
import odmlib.ns_registry as NS
NS.bind_document_namespaces(new_elem, NS.get_document_namespaces(define))
```

### Testing odmlib code

Three traps specific to testing against this library, none of them obvious from a passing
first run:

- **A fresh OID checker per test, not per module.** `create_oid_checker(...)` accumulates
  every OID it sees, so a checker built in `setUpClass` (or shared across parametrized cases)
  reports a false *"OID … is not unique"* for everything in the second test onward. Build it
  inside the test, or `checker.reset()` in `setUp`.
- **The namespace registry is process-wide state, so reset it between tests.** odmlib's own
  suite does this with an `autouse` fixture (`tests/conftest.py`) that resets the Borg
  singleton to *ODM 1.3.2 only* before every test — which means a test that needs `def:`,
  `xlink:` or `xml:` must re-register them itself in `setUp` (see
  `tests/test_odm_loader_define_string.py`). A Define test that passes alone and fails in
  the suite is almost always this.
- **Probes must tolerate empty collections.** The failure modes worth testing for produce
  *structurally valid but empty* documents — a string that lost its namespaces re-loads with
  `FileOID` intact and `Study` empty. A test that asserts on `odm.Study[0]` then raises
  `IndexError` and takes the harness down instead of reporting the failure it was written to
  catch. Check `len(...)` first and report; save the indexing for after.

## A reliable working loop for odmlib tasks

1. Identify standard + version → model package.
2. Choose the altitude (facade vs loader; builder vs raw) for the task.
3. Build or load the object tree with odmlib — never raw markup.
4. Make the change against the objects.
5. `validate(collect_errors=True, oid_checker=..., conformance_checker=...)`; fix and
   **re-run until clean** — one pass now lists every defect, but fixing one can expose
   another, so a clean run is still the signal. Pass a **fresh** `create_oid_checker(...)`
   on every iteration (or `checker.reset()`).
6. Serialize with `write_xml(...)` / `write_json(...)` (or let the facade save on exit).
7. When it matters (submissions, handoffs), also run XSD validation.

## Reference material

Read these as needed — they hold the detail that does not belong in the workflow above.

- `references/api-reference.md` — the public API surface: imports, the facade, `ODMBuilder`
  methods, the loader classes, `ODMElement` methods (`find`/`find_by`/`write_*`/`verify_*`/
  `validate`), the serialization methods and the namespace-binding helpers, the exception
  hierarchy, and validation modes. Start here when you need an exact name or signature.
- `references/models.md` — the model packages and their key classes, the ODM 1.3.2 vs 2.0
  structural differences, namespace URIs, and version-specific notes.
- `references/validation.md` — the full validation story: conformance vs OID vs order vs XSD,
  the `ErrorCollector`, permissive `ValidationMode` flags, and how to validate extensions.
- `references/dataset-json.md` — Dataset-JSON 1.1 specifics and the conversion helpers.

Runnable, self-contained examples live in `examples/` — each one executes against an
installed odmlib and writes any output under `./odmlib_skill_output/` in the **current
working directory**, never into the skill directory (which is read-only once installed).
Some write nothing at all: `report_oid_integrity.py` only prints, and
`validate_document.py` works inside a `tempfile.TemporaryDirectory()`.
Copy an example out or run it from a writable directory; nothing is written beside the
script. Read them for working idioms;
run them to confirm behavior in the current environment. They cover: creating ODM (builder
+ raw, with a CodeList and bundled-schema XSD check), read-modify-write via the facade, the
explicit loader (including `to_xml_string()` round-tripping, its byte relationship to
`write_xml()`, and the `ET.tostring(obj.to_xml())` anti-pattern), validation (a caught
dangling OID reference, and a demonstration that
`collect_errors=True` reports all three planted defects plus `max_errors` truncation), OID
reporting beyond what `validate()` covers — orphans, usage lookup, inventory
(`report_oid_integrity.py`) — permissive repair, a Dataset-JSON NDJSON round-trip, and a
Define-XML 2.1 round-trip (the singular `Study`/`MetaDataVersion` idiom plus bundled-schema
validation).
