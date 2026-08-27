# Validation in odmlib

Validation is where odmlib earns its keep: a document that *looks* right can still be
non-conformant. Treat validation as part of producing a document, not an optional extra.
There are four independent checks, and they catch different classes of problem.

## The one entry point: `validate()`

`ODMElement.validate(collect_errors=False, oid_checker=None, conformance_checker=None,
max_errors=None)` orchestrates the in-memory checks. Call it on the root to cover the whole
document.

```python
from odmlib import create_oid_checker
from odmlib.odm_1_3_2.rules.metadata_schema import MetadataSchema

errors = odm.validate(
    collect_errors=True,                            # every problem, not just the first
    oid_checker=create_oid_checker("odm_1_3_2"),
    conformance_checker=MetadataSchema(),
    max_errors=100,                                 # optional cap; None (default) = all
)
if errors:
    for e in errors:
        print(e)        # str(e) includes element_path and a fix hint when known
    raise SystemExit(1)
```

- `collect_errors=False` (default): fail-fast. Runs `verify_order`, then (if supplied)
  `verify_oids` and `verify_conformance`. Returns `True` or raises the first error.
- `collect_errors=True`: returns a `list` of `OdmlibError` (empty list == valid), holding
  **every** defect all three layers can find.

The three layers `validate()` can run:

| Layer | Triggered by | Catches | Errors contributed |
|---|---|---|---|
| Element order | always | children declared out of schema order (`OdmlibElementOrderError`) | one per misordered element |
| OID integrity | `oid_checker=` | duplicate OIDs; refs (`ItemOID`, `CodeListOID`, …) with no matching def (`OdmlibOIDError`) | one per duplicate and per bad reference |
| Conformance | `conformance_checker=` | missing required attrs, invalid value-set values, wrong types (`OdmlibConformanceError`) | one per failing field |

So the list length tracks the number of *defects*, not the number of failing layers. A
document with five dangling OID references yields five `OdmlibOIDError`s. Because the count
is unbounded, **filter by exception type — never by list index**:

```python
from odmlib import OdmlibOIDError, OdmlibElementOrderError, OdmlibConformanceError
oid_problems = [e for e in errors if isinstance(e, OdmlibOIDError)]
```

Details worth knowing:

- **The order walk recurses into misordered elements.** A misordered parent no longer stops
  the traversal, so one pass lists every element `reorder_object()` must be called on
  (`reorder_object()` is itself non-recursive).
- **A duplicate OID no longer aborts the OID traversal.** Previously the first duplicate
  stopped the tree walk before the reference checks ran at all, hiding every dangling
  reference until the duplicate was fixed. Both sub-checks now complete. On a duplicate the
  **first** definition is kept.
- **Conformance errors are expanded.** Cerberus finds every violation, and odmlib now splits
  the bundle into one `OdmlibConformanceError` per failing field. Each carries a dotted
  `field_path` (`"ItemGroupDef.0.Name"`), `attribute` (`"Name"`), `element_path`
  (`"ItemGroupDef.0"`), and the **complete** raw dict still on `.cerberus_errors`, shared
  by reference across the siblings. In fail-fast mode the single bundled error is raised
  unchanged (`field_path is None`).
- **Error ordering is deterministic.** The OID checker sorts its reference sets, so repeated
  runs report problems in the same order regardless of `PYTHONHASHSEED`.
- **Only `OdmlibError` subclasses are collected.** A `TypeError` from a mis-signatured custom
  checker or an `AttributeError` from a corrupt tree propagates in both modes — those are
  bugs, not document defects.

### Capping the list with `max_errors`

A badly broken document (typically one just loaded permissively) can produce thousands of
errors. `max_errors=N` stops collection at the cap and appends a final
`OdmlibErrorLimitError`, so the list holds at most `N + 1` entries:

```python
from odmlib import OdmlibErrorLimitError

errors = odm.validate(collect_errors=True, oid_checker=checker, max_errors=100)
if errors and isinstance(errors[-1], OdmlibErrorLimitError):
    print("more problems remain — fix these and re-run")
```

The cap is enforced *inside* each layer, so validation genuinely stops early rather than
collecting everything and slicing. `max_errors=0` therefore checks nothing and returns just
the marker. It is ignored when `collect_errors=False`.

### Not every checker can enumerate

Full OID enumeration requires a checker implementing the *collecting protocol*. The modern
`DynamicOIDRef` from `create_oid_checker()` does; the deprecated `rules/oid_ref.py` `OIDRef`
classes (removed in 0.3.0) do not, and contribute at most **one** error for the whole OID
layer. Custom duck-typed checkers likewise degrade gracefully rather than breaking.

```python
from odmlib import is_collecting_checker
is_collecting_checker(create_oid_checker("odm_1_3_2"))   # True
```

The protocol is a mixin (`odmlib.exceptions.ErrorReporting`) providing `report(error)` —
which raises when no sink is installed and accumulates when one is — plus a `collecting()`
context manager. That also lets you collect from `verify_oids()` on its own:

```python
from odmlib import ErrorCollector

collector = ErrorCollector()
with checker.collecting(collector):
    odm.verify_oids(checker)          # returns True; problems land in collector.errors
```

For a full picture of a bad document, still pair this with XSD validation — `iter_errors`
catches structural issues the in-memory model cannot see.

## OID integrity in depth

OID def/ref errors are the most common defect in generated documents, and a `validate()`
with a conformance checker alone will not catch them — supply an `oid_checker` too.

```python
checker = create_oid_checker("odm_1_3_2")     # or "define_2_1", "odm_2_0", ...
odm.verify_oids(checker)                       # raises OdmlibOIDError on the FIRST problem
```

**`verify_oids()` on its own is fail-fast** — it raises on the first duplicate OID, then on
the first dangling reference. To enumerate, either call
`validate(collect_errors=True, oid_checker=checker)`, or install a sink around it:

```python
collector = ErrorCollector()
with checker.collecting(collector):
    odm.verify_oids(checker)                   # collector.errors holds every OID defect
```

Duplicates are still checked before references, but a duplicate no longer aborts the
traversal, so a document with both now reports the duplicates *and* the dangling refs in
the same pass.

`create_oid_checker(model_package, extra_skip_attrs=None, extra_skip_elems=None)` builds a
`DynamicOIDRef` from the model's known def/ref attributes. For a custom extension that adds
an OID-shaped attribute which is *not* a real reference, pass it in `extra_skip_attrs` so it
is not treated as a dangling ref.

**`def:ArchiveLocationID` *is* checked (since 0.2.1).** Reference discovery keys off the `OID`
*suffix*, which in `define_2_1` covers `ItemOID`, `CodeListOID`, `MethodOID`, `CommentOID`,
`WhereClauseOID`, `ValueListOID`, `StandardOID`, and `RoleCodeListOID`. Define-XML's
`def:leaf/@ID` ↔ `ItemGroupDef/@def:ArchiveLocationID` pair does not fit that suffix rule, so
`ArchiveLocationID` (and `leafID`, which also points at a `leaf`) is special-cased alongside the
`*OID` attributes. Dangling one reports

```
OdmlibOIDError: OID LF.DOES.NOT.EXIST referenced in attribute ArchiveLocationID is not found.
```

Before 0.2.1 this link was unchecked and passed `verify_oids()` silently — if you are pinned to
an older odmlib, verify it yourself or rely on XSD, which enforces `IDREF`.

Genuinely uncovered links are those that are neither `*OID`-suffixed nor explicitly wired: check
those yourself or via XSD.

### `unreferenced_oids()` returns a dict

It returns `check_unreferenced_oids()`, which is `dict[str, str]` mapping each orphan OID to
the *reference attribute* that would have pointed at it (falling back to the defining
element's class name when no ref attribute targets that class). `if orphans:` behaves the
same for a dict or a list, so iterate the items to get anything useful out of it.

```python
orphans = odm.unreferenced_oids(checker)   # dict: orphan OID -> expected ref attribute
for oid, expected_ref_attr in orphans.items():
    print(f"{oid} is defined but never referenced (expected via {expected_ref_attr})")
```

Treat the result as a quality signal, not a defect list, and **note it is much noisier in
`odm_*` than in `define_*`**: the checker's `skip_elem` set decides which definitions are
exempt from the orphan report, and it differs sharply by model.

| Model package | `skip_elem` | Consequence |
|---|---|---|
| `odm_1_3_2` | `ODM` | `Study`, `MetaDataVersion`, and unreferenced `ItemGroupDef` OIDs **all show up as orphans** in a metadata-only document |
| `define_2_1` | `ODM`, `Study`, `MetaDataVersion`, `ItemGroupDef` | structural OIDs are already excluded; results are close to actionable |

For ODM, filter the structural roots out yourself (or pass `extra_skip_elems=["Study",
"MetaDataVersion"]` to `create_oid_checker`) before showing the list to a user.

### Reporting beyond duplicates and dangling refs

`validate(collect_errors=True, oid_checker=...)` covers duplicates and bad references. For
the rest of an integrity report — which OIDs are defined but never used, where a given OID
appears, an inventory of every OID by defining element — drive the checker's own mappings.
After `verify_oids()` (or a collect-mode `validate()`) the checker is populated:

| Attribute | Type | Meaning |
|---|---|---|
| `checker.oid_defs` | `list[str]` | element classes that **define** an OID (always via their `OID` attribute) |
| `checker.ref_def` | `dict[str, str]` | reference attribute → the element class it must resolve to |
| `checker.def_ref` | `dict[str, list[str]]` | def class → the reference attributes that may point at it |
| `checker.ref_attrs` | `dict[str, list[str]]` | reference attribute → element classes that carry it |
| `checker.oid` | `dict[str, str]` | OID value → defining element class (**populated during** `verify_oids`) |
| `checker.oid_ref` | `dict[str, set]` | reference attribute → set of OID values used (populated during `verify_oids`) |
| `checker.skip_attr` | `list[str]` | OID-shaped attributes that are *not* references (`FileOID`, …) |
| `checker.skip_elem` | `list[str]` | element classes exempt from the orphan report |

The first four are ready at construction; `oid` and `oid_ref` fill in only while
`verify_oids()` runs. Note `oid_defs` is a **list of class names**, not a mapping — the
defining attribute is always `OID`.

To build an OID inventory yourself, walk the tree the way odmlib does internally: iterate
`instance.__dict__`, skip keys starting with `_`, and recurse into `ODMElement` values and
lists of them. Never touch the descriptors — that is what keeps the walk safe on a
permissively-loaded document. See `examples/report_oid_integrity.py` for a complete,
runnable version.

### An OID checker is single-use per document

`verify_oids()` *accumulates* into `checker.oid`. Running it twice with the same checker
reports a spurious duplicate for every OID in the document:

```python
checker = create_oid_checker("odm_1_3_2")
odm.verify_oids(checker)     # OK
odm.verify_oids(checker)     # OdmlibOIDError: OID ST.1 is not unique - element Study  (FALSE)
```

Two ways out: **build a fresh checker for every verification pass** (each iteration of a
fix-and-re-run loop, each document in a batch), or **call `checker.reset()`** between runs —
it clears `oid`, `unique_oids`, every `oid_ref` set, and `is_verified`.

```python
checker.reset()
errors = other_odm.validate(collect_errors=True, oid_checker=checker)
```

In collect mode `validate()` emits an `OdmlibWarning` when handed a checker that still holds
state, so the mistake surfaces as a warning instead of a wall of bogus duplicates.

There is a second-order effect on `unreferenced_oids()`, which re-runs `verify_oids()`
whenever `is_oids_verified()` is False:

- After a **collect-mode `validate()`**, the reference pass always completes and the checker
  is marked verified, so `unreferenced_oids()` works normally — the simplest way to get a
  trustworthy orphan list.
- After a **fail-fast** failure on a **dangling reference**, the checker *is* marked
  verified, so `unreferenced_oids()` also works.
- After a **fail-fast** failure on a **duplicate OID**, the checker is left un-verified *and*
  half-populated, so `unreferenced_oids()` re-runs the check and raises an `OdmlibOIDError`
  **naming an OID that is not actually duplicated**. Do not report that error to a user —
  reset the checker, pass a fresh one, or validate in collect mode first.

`build_oid_index()` complements this: it returns an `OIDIndex` whose `find_all(oid)` gives
every object carrying that OID — the quickest way to turn a reported OID back into the
elements involved.

## Conformance vs XSD — they are complementary

- **Conformance** (`MetadataSchema` → Cerberus) checks the rules odmlib encodes from the
  model: required attributes, controlled value sets, types. It needs no external file and
  runs in memory. Import it from `odmlib.<package>.rules.metadata_schema`. On failure,
  `OdmlibConformanceError.cerberus_errors` holds a field-by-field dict.
- **XSD** (`odmlib.odm_parser.ODMSchemaValidator`) validates the serialized file against the
  official CDISC `.xsd`. It catches structural/schema issues conformance does not. odmlib
  **bundles** the ODM, Define-XML, and ARM schemas, so resolve them by `(standard, version)` —
  no download required:

```python
from odmlib.odm_parser import ODMSchemaValidator
# bundled-schema pairs: ("odm","1.3.2"), ("odm","2.0"), ("define","2.0"), ("define","2.1"),
#                       ("arm","1.0"), ("arm","1.0-define2.1")
validator = ODMSchemaValidator(standard="define", version="2.1")
validator.validate_file("define.xml")            # raises OdmlibSchemaValidationError on failure
validator.validate_tree(tree)                    # -> bool, for an already-parsed ElementTree

# collect EVERY schema error (best for reporting), each with .reason and .path:
for err in validator.xsd.iter_errors("define.xml"):
    print(err.reason, "@", err.path)
```

For an ARM (ADaM) document pick the pairing that matches its Define-XML version —
`("arm","1.0-define2.1")` for `def:` v2.1 (what `arm_1_0` models), `("arm","1.0")` for v2.0.
They are not interchangeable; the wrong one rejects the document on its first `def:`
attribute. Both also validate ARM-free Define-XML, being supersets of the base schema.

Pass `xsd_file="/path/to/schema.xsd"` only for a custom or local schema not bundled with
odmlib. For submission-grade output, run both: conformance during construction, XSD on the
written file.

## Order: usually automatic, sometimes not

`to_xml`/`write_xml` already emit children in model order, so `verify_order()` is **not**
required before XML serialization. It matters before `to_dict`/`to_json` (which walk
instance `__dict__` and reflect assignment order) and after hand-editing a tree. If order is
wrong:

```python
try:
    odm.verify_order()
except OdmlibElementOrderError as e:
    print(e)                 # tells you the expected order
    element.reorder_object() # fix in place on the offending element (emits OdmlibWarning)
```

`reorder_object()` is not recursive — call `verify_order()` first to find which elements
need it, or reorder the specific elements involved.

## Permissive loading: read/repair non-conformant files

Strict mode (default) refuses to load files that break the rules. To load a broken or legacy
file so you can inspect and fix it, switch to permissive mode for the load only, then return
to strict and validate the repaired result.

```python
from odmlib import permissive, ValidationMode
from odmlib.context import open_define

# whole-document relaxation during load, read-only.
# write_on_exit=False is belt-and-braces here — the default is already read-only:
with open_define("legacy.xml", permissive=True, write_on_exit=False) as define:
    ...   # inspect

# or relax just one category, around any odmlib call:
with permissive(ValidationMode.SKIP_REQUIRED):
    define = loader.root()
```

`ValidationMode` flags combine with `|`: `SKIP_REQUIRED`, `SKIP_VALUESET`, `SKIP_TYPE`,
`SKIP_FORMAT`, and the composite `PERMISSIVE`. Permissive mode is for ingestion and repair,
never for emitting output — fix the problems, drop back to strict, and `validate()` before
writing.

**One subtlety when reading repaired-but-missing attributes.** `SKIP_VALUESET`/`SKIP_TYPE`/
`SKIP_FORMAT` store the bad value on the instance, so it reads back normally outside the
`with` block. `SKIP_REQUIRED` has *nothing* stored for an unset required attribute, so the
read-time check consults the live mode — reading a possibly-missing required attribute
(e.g. checking `if item.Name is None`) must itself be wrapped in `with permissive():`, even
when the document was already loaded permissively. Once you assign the attribute, later
reads work in strict mode.

### A real-world pattern: validate a non-conformant template

A common task (e.g. a Define-XML template seeded with `__PLACEHOLDER__` values that violate
the data types and value lists) is to find out *everything* wrong with a file at once.
`validate(collect_errors=True, ...)` is the tool for that: with both checkers supplied it
enumerates every order, OID, and conformance defect in one pass. XSD validation is the
complementary layer — it catches what the model does not encode (element content models,
xs:pattern facets, wrong namespaces), so run both and merge the two reports.

```python
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib import create_oid_checker, permissive, OdmlibOIDError
from odmlib.define_2_1.rules.metadata_schema import MetadataSchema
from odmlib.odm_parser import ODMSchemaValidator

# 1. schema-validate the file and list every XSD error
validator = ODMSchemaValidator(standard="define", version="2.1")
schema_errors = list(validator.xsd.iter_errors("define-template.xml"))
print(f"{len(schema_errors)} schema errors")

# 2. permissively load (strict would refuse it) ...
loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
with permissive():
    loader.open_odm_document("define-template.xml")
    odm = loader.root()

# 3. ... then enumerate EVERY odmlib-visible defect in one collect-mode pass
checker = create_oid_checker("define_2_1")
errors = odm.validate(
    collect_errors=True,
    oid_checker=checker,
    conformance_checker=MetadataSchema(),
    max_errors=200,                 # cap the noise on a badly broken template
)
print(f"{len(errors)} odmlib defects")
for e in errors:
    print(" ", e)

oid_problems = [e for e in errors if isinstance(e, OdmlibOIDError)]
print(f"{len(oid_problems)} of them are OID defects")

# 4. quality signal, not an error — so validate() stays silent about it.
#    Safe here because `checker` has been through a COLLECT-mode pass, which
#    populates it fully; after a fail-fast verify_oids() it would be half-built.
print("unreferenced:", odm.unreferenced_oids(checker))   # dict, may be empty
```

Loading a file you did not produce can fail in ways that are **not** `OdmlibError` — see
*Loading files you do not control* in `references/api-reference.md` before wrapping step 2
in `except OdmlibError`.

## `ErrorCollector`

`validate(collect_errors=True)` uses an `ErrorCollector` internally and hands back its
`errors` list. You can also use it directly to accumulate issues across several checks and
then raise once, or as the sink for a checker's `collecting()` block:

```python
from odmlib import ErrorCollector
collector = ErrorCollector()
# ... add_error(...) / add_warning(...) as you run checks ...
collector.raise_if_errors()    # raises the single error, or a summary of all
```

`ErrorCollector(max_errors=N)` caps the collection: `is_full` reports whether the cap is
reached and `truncated` whether collection actually stopped short. An uncapped collector —
`ErrorCollector()`, the default — never raises from `add_error()`, so hand-built usage is
unaffected by the cap machinery.

## Validating extensions

A proprietary extension validates the same way: `verify_order()` requires that subclasses
redeclare inherited children in schema order; conformance needs a registered schema for the
extension's elements (or call `validate()` without a `conformance_checker` for that model);
and OID checking accepts `extra_skip_*` for extension-specific attributes. Build the
extension correctly and the same `validate()` call covers it.
