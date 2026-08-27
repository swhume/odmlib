# ODM v2.0 Model / XSD Alignment

## Context

v0.2.1 closed the five structural ODM 2.0 gaps that `WHATS_LEFT_v021.md` §A tracked
(`ConditionDef/MethodSignature`, element-based `FormalExpression`, `Protocol`,
`Protocol/StudyTimings`, `StudyEventGroupDef`), plus five follow-ons found while verifying
them (`CommentDef` and `Leaf` on `MetaDataVersion`, `DocumentRef/@LeafID`, and the
`SourceItem`/`Resource`/`Selection` content model). Each was found the same way: build a
document, validate it against the bundled XSD, fix what it rejects.

That method kept finding more. A mechanical comparison of `odmlib/schemas/odm/2.0/*.xsd`
against `odmlib/odm_2_0/model.py` shows the divergence is far wider than the ten items
fixed so far — and, critically, it is invisible: nothing in CI compares the model to the
schema, so every gap has to be rediscovered by hand.

No document in the repository claims `odm_2_0` output is schema-valid. `README.md:609-613`,
`docs/source/guides/model_reference.rst:90-96` and `CHANGELOG.md:397-398` all say the
opposite, and `ROADMAP.md:193` makes the Draft→Stable promise conditional on round-trip
tests passing.

**Intended outcome:** every ODM 2.0 *metadata* document odmlib can construct validates
against the bundled ODM 2.0 XSD, the remaining approximations are deliberate and written
down, and a test makes new drift impossible to introduce silently.

## Scope decisions

| Decision | Choice |
|---|---|
| Depth | **Metadata layer only.** `ClinicalData`/`ReferenceData` (24 classes) stay booked for v0.3.0 — `ROADMAP.md:186-196` already commits to them. |
| Non-XSD members | **Removed outright**, documented in `CHANGELOG.md` as breaking-within-draft-ODM-2.0 — the treatment `ItemDef`, `FormalExpression` and `SourceItem` already received. |
| Constructs odmlib cannot express | **Documented as waivers.** No changes to `typed.py` / `odm_element.py`, which are shared with ODM 1.3.2, Define-XML, ARM, CT and Dataset-JSON. *Correction since that decision was taken:* `xhtml:div` turns out to be expressible with no core change — see Phase 5, item 3. |

## Measured starting point

| | Count |
|---|---|
| Elements declared in the ODM 2.0 XSD | 149 |
| Modelled in `odm_2_0` | 94 |
| Modelled classes that differ from their XSD type | **36** |
| XSD elements with no class — ClinicalData/ReferenceData subtree | 24 *(out of scope, v0.3.0)* |
| XSD elements with no class — Protocol study-design subtree | 24 |
| XSD elements with no class — AdminData | 4 |
| XSD elements with no class — metadata (`Class`, `SubClass`, `ValueListRef`) | 3 |
| Model classes not declared anywhere in the XSD | 8 |

---

## Phase 0 — the guard (do this first)

New `tests/test_odm_2_0_xsd_alignment.py`. It parses the bundled XSD, introspects
`odmlib.odm_2_0.model`, and asserts the divergence set **equals** a declared allowlist —
not merely that it is a subset. Every later phase deletes entries from that allowlist; a
newly introduced divergence fails as an unexpected extra, and a fixed one fails as a stale
entry, so the file can never overstate or understate the truth.

Build it from the comparison already prototyped during research:

- Walk every `xs:complexType` named `ODMcomplexTypeDefinition-<Element>`, resolving
  `xs:attributeGroup` refs and expanding `xs:group` refs (`StudyEventDefGroup` is the one
  that matters) to produce, per element: attributes with `use="required"`, and children in
  document order with `minOccurs`/`maxOccurs`.
- Compare against `cls._attrs` / `cls._elems`, `descriptor.required`, and
  `isinstance(descriptor, T.ODMListObject)`.
- Report four kinds of finding: missing/extra member, required mismatch, list-vs-single
  mismatch, and **child declaration order** (load-bearing — odmlib serializes in
  declaration order).
- Treat `mixed="true"` types and `xs:simpleContent` extensions as contributing `_content`,
  or the comparison produces false positives on `TranslatedText`, `Title` and `Code`.

**`verify_order()` cannot serve as this guard.** The XML loader populates children by
iterating `_elems` and issuing `find`/`findall` per descriptor
(`odm_loader.py:255-267`) — it never follows document order. A loaded object's `__dict__`
is therefore always in model order, so `verify_order()` passes on *every* XML-loaded
document, including schema-invalid ones, which odmlib silently normalizes on re-serialization.
Only a direct declaration-order-vs-XSD comparison catches an ordering bug like `Origin`.

The allowlist starts at the 36 + 55 + 8 findings below and is expected to end at the
Phase 5 waivers plus the ClinicalData/ReferenceData block.

---

## Phase 1 — members that make current output invalid (breaking)

All in `odmlib/odm_2_0/model.py`.

| Class | Change |
|---|---|
| `Telecom` | `value` → `Value`. Case-only spelling bug, exactly like the `leafID`→`LeafID` fix already shipped. |
| `WorkflowEnd` | Add `_content` — the XSD type is `xs:simpleContent` over `text`, and the model has no text member at all. |
| `ODM` | Remove `Archival`; it is not in `ODMAttributeDefinition`. |
| `Origin` | Reorder children to `Description`, `SourceItems`, `DocumentRef`; the model declares `DocumentRef` first, which serializes out of sequence order. |
| `RelativeTimingConstraint` | Remove `PredecessorStudyEventGroupOID`, `PredecessorStudyEventOID`, `SuccessorStudyEventGroupOID`, `SuccessorStudyEventOID`; add `PredecessorOID`, `SuccessorOID`. |
| `TransitionTimingConstraint` | Remove `TimepointRelativeTarget`; add `TimepointTarget` (required) and `Type`. |
| `User` | `Prefix`/`Suffix` are **elements** in the XSD, not attributes — convert, and add the two new classes. Remove `DisplayName` (not in the ODM 2.0 XSD). |
| `Organization` | Replace the orphaned text-only class (defined at `model.py:1364`, referenced by nothing) with the XSD's AdminData element: `OID`/`Name`/`Type` required, `Role`, `LocationOID`, `PartOfOrganizationOID`, children `Description`, `Address*`, `Telecom*`. Add `Organization` to `AdminData`. |
| `TranslatedText` | No model change — see Phase 5 — but confirm the guard's mixed-content handling matches. |
| `User` docstring | `model.py:1556` documents an `Organization` child that is not declared. Correct it alongside the `Organization` rewrite. |

**Migration note for every rename in this phase.** There is no alias layer: the descriptor
name *is* the XML attribute name (`odm_loader.py:250-254` → `odm_element.py:271-286`). In
strict mode an old-spelling document now raises `OdmlibTypeError` on load; in permissive
mode the value is silently dropped. That is the correct outcome — the old spellings were
never XSD-valid — but say so explicitly in the CHANGELOG entry, as the `leafID`→`LeafID`
entry already does.

**Restore ID-based ref/def checking for `DocumentRef/@LeafID`.** `odm_element.py:681`
sniffs reference attributes with a hardcoded `attr in ("leafID", "ArchiveLocationID")`,
and `oid_generator.py:_ID_REF_DEF_PAIRS` maps `"leafID" → "leaf"` (lower-case, the
Define-XML class name). Neither has ever matched `odm_2_0`, whose class is `Leaf`, so
`DocumentRef` has never been ref-checked here; after the v0.2.1 rename to `LeafID` it is
not even collected. Now that `Leaf` is reachable from `MetaDataVersion`, wire
`LeafID → Leaf` so a dangling document reference is caught like any other.

Also in `odmlib/typed.py`: `_DURATION_PAT` (line 470) is `^[+-]?P\d+W$`, but the XSD's
`durationDatetime` is `union(emptyTag, xs:duration, tDuration)`. odmlib rejects
XSD-valid values such as `P3D`, `P1Y2M`, `PT1H` and the empty tag. Widen the pattern to
the union. **This descriptor is used only by the four ODM 2.0 timing-constraint classes**
— verify that with a grep before changing it, so the blast radius stays inside `odm_2_0`.

`odmlib/oid_generator_config.py` — `ODM_20_SKIP_ATTRS` lists the four
`Predecessor*`/`Successor*` names being removed. Replace them with `PredecessorOID` /
`SuccessorOID`, which need the same skip treatment (they can reference several element
types).

---

## Phase 2 — required / cardinality mismatches

Declarative only — no constructor behaviour changes, since `required` on an `ODMObject`
is not enforced at construction (`odm_element.py:289` excludes it).

**Model stricter than the XSD** (relax to optional): `FormalExpression.Context`,
`MethodDef.Type`, `TargetTransition.ConditionOID`, and the pre/post window attributes on
`AbsoluteTimingConstraint`, `RelativeTimingConstraint`, `DurationTimingConstraint`,
`TransitionTimingConstraint`.

**Model looser than the XSD** (tighten to required): `MethodDef.MethodSignature`,
`Leaf.Title`, `Study.MetaDataVersion`, `Standard.Status`.

**Single vs list**: make lists — `AnnotatedCRF.DocumentRef`, `SupplementalDoc.DocumentRef`,
`StudyTiming.TransitionTimingConstraint`. Make single — `MetaDataVersion.Standards`,
`Address.StreetName`, and `WorkflowRef` on `ItemGroupDef`, `StudyEventDef`,
`StudyStructure`.

---

## Phase 3 — missing members on existing classes, and the small new classes

**Attributes**: `ItemGroupDef` — `Structure`, `ArchiveLocationID`; `ItemGroupRef` —
`MethodOID`; `CodeListItem` — `ExtendedValue`; `Include` — `href`; `PDFPageRef` — `Title`;
`RangeCheck` — `ItemOID`; `Location` — `OrganizationOID`.

**Children**: `MetaDataVersion` — `AnnotatedCRF`, `SupplementalDoc`, `ValueListDef*`,
`WhereClauseDef*` (all four classes already exist; they are simply not wired in, the
same shape of fix as `CommentDef`/`Leaf`); `ItemDef` — `ValueListRef`; `ItemGroupDef` —
`Class`, `Leaf`; `MethodDef` — `DocumentRef*`; `RangeCheck` — `MethodSignature`;
`Origin`, `SourceItems`, `StudyEventDef` — `Coding*`; `Location` — `Description`,
`Address*`, `Telecom*` (`Query*` belongs to the v0.3.0 data layer); `Address` —
`HouseNumber`, `GeoPosition`.

**New classes**: `Class` (with `SubClass*`), `SubClass`, `ValueListRef`, `HouseNumber`,
`GeoPosition`, `Prefix`, `Suffix`.

Note `ItemGroupDef.Class` is an *element* in ODM 2.0, not the Define-XML-style attribute —
see the valuesets finding below.

**Hazard for Phases 3 and 4:** inserting a descriptor mid-class changes `_elems` order,
which is exactly the intent, but `verify_order()` reads each class's *own* class body
(`odm_element.py:709-713`). Any downstream subclass of an `odm_2_0` model class that does
not opt into `merge_fields=True` must redeclare base children in the new order. No shipped
model uses `merge_fields`, so the risk is confined to third-party extensions — call it out
in the CHANGELOG.

---

## Phase 4 — Protocol study-design subtree (24 new classes)

The nine optional `Protocol` children deliberately left unmodelled in v0.2.1, plus their
descendants: `StudySummary`/`StudyParameter`/`ParameterValue`, `TrialPhase`,
`StudyIndications`/`StudyIndication`,
`StudyInterventions`/`StudyIntervention`/`StudyInterventionRef`,
`StudyObjectives`/`StudyObjective`, `StudyEndPoints`/`StudyEndPoint`/`StudyEndPointRef`,
`StudyTargetPopulation`/`StudyTargetPopulationRef`,
`StudyEstimands`/`StudyEstimand`/`IntercurrentEvent`/`SummaryMeasure`,
`InclusionExclusionCriteria`/`InclusionCriteria`/`ExclusionCriteria`/`Criterion`.

Declare them in `Protocol` at the XSD sequence positions the existing docstring already
reserves (`model.py`, `Protocol` — the `.. note::` naming all nine). The `Protocol`
declaration order is already correct; these slot in without disturbing it.

`odmlib/data/valuesets.json` already carries `StudyEndPoint.Type`, `StudyEstimand.Level`
and `StudyObjective.Leve` (note the truncated key) for classes that do not yet exist —
land them together with the classes.

---

## Phase 5 — waivers and documentation

Two XSD constructs stay approximations outright, and a third is narrower than expected.
Each gets a `.. note::` in its class docstring saying what the XSD requires, what odmlib
does instead, and that XSD validation is the backstop — the pattern already used on
`FormalExpression` and `StudyEventGroupDef`:

1. **`xs:choice`** — `FormalExpression`'s `Code | ExternalCodeLib`. Both optional; "exactly
   one" is left to `ODMSchemaValidator`. `odm_2_0` has no `rules/` package, so there is no
   Cerberus schema to enforce it in.
2. **Repeating groups** — `StudyEventGroupDef`'s `(StudyEventGroupRef?, StudyEventRef?)+`
   modelled as two parallel lists; cannot reproduce an interleaved ordering.
3. **`TranslatedText` mixed content and `xhtml:div`** — narrower than it first appears.

   **Tried and withdrawn.** An opaque `_content`-only `div` was added and then removed:
   odmlib XML-escapes element text on write, so the div could not carry markup either,
   and as the model's first foreign-namespace *child* it made `NamespaceRegistry` state
   load-bearing for every ODM 2.0 load — 16 `xhtml` registrations across 9 test files,
   and order-dependent failures until each was found. It was paying a real cost to model
   a wrapper that could not hold anything.

   **What real support would take**, if formatted CRF text is wanted later:
   - **Raw-subtree passthrough — feasible, ~75-90 lines.** A `RawXML` descriptor holding a
     parsed subtree, a third `_raw` bucket in `ODMMeta.__new__`, and an append in
     `to_xml()`; `to_dict` emits a markup *string*, which makes the JSON loader work
     unchanged. Every edit is an exclusion guarded by an empty `_raw` bucket, so the other
     six model packages see no behaviour change. Normalize to prefix-literal `xhtml:` tags
     for byte-identical output, and wrap user markup in
     `<div xmlns="http://www.w3.org/1999/xhtml">` — `ODM-xhtml.xsd` sets
     `elementFormDefault="qualified"`, so unqualified markup is schema-invalid.
   - **Tail support — ~6 core lines, and worth doing either way.** odmlib never reads
     `ElementTree.tail`. Provably a no-op for ODM 1.3.2 / Define-XML: `mixed="true"`
     appears nowhere they model, so every tail there is pretty-printing whitespace that
     the existing `isspace()` guard already discards.
   - **Modelling the xhtml element set — not feasible.** `ODM-xhtml.xsd` has 38 active
     elements, 26 of them mixed. A minimal subset does not exist: seeding with
     `{p, br, b, i, em, strong, span, ul, ol, li}` closes over all 38, and so does the
     inline-only subset, via `map` → `block`. The deeper blocker is that `to_xml()` emits
     children in `_elems` order with a single `_content` slot, so interleaved mixed
     content is inexpressible without a new order-preserving serializer.

   odmlib *does* support both mixed content and foreign-namespace children: `_content`
   serializes as element text before the children (`odm_element.py:380-390`) and loads
   back (`odm_loader.py:250-254`), and a foreign-namespace child works through the
   two-place pattern Define-XML already uses (`define_2_1/model.py:160-182`) — a class-level
   `namespace = "xhtml"` driving serialization plus `namespace="xhtml"` on the descriptor
   driving lookup, with the prefix registered in `NamespaceRegistry` at import.
   So `xhtml:div` **can** be added as an opaque `_content`-only leaf with **no core
   change**, and is worth doing if real documents need it. What stays waived:
   - **internal xhtml markup** — the loader resolves children by local tag name against
     the model module, so accepting `<p>`, `<b>`, `<table>`… means a model class per xhtml
     element; `ODM-xhtml.xsd` is deeply recursive and mixed, so an opaque leaf loses any
     markup inside the `div`;
   - **tail text** — odmlib never reads `.tail`, so text *after* the `div` is dropped
     silently on load. Text-only `TranslatedText`, and text-then-`div`, both round-trip.

   If `xhtml:div` is added, register the `xhtml` prefix in `odm_2_0/model.py`. Omitting it
   fails badly in both directions: serialization emits `<xhtml:div>` with no `xmlns:xhtml`
   (unparseable output, no warning) and loading raises a bare `SyntaxError` from
   ElementTree, outside the `OdmlibError` hierarchy.

Also record the eight model classes with no ODM 2.0 XSD element — `ArchiveLayout`,
`DisplayName`, `Email`, `ExceptionEvent`, `Fax`, `Pager`, `Phone`, `Picture` — as ODM
1.3.2 carry-over. `DisplayName` goes in Phase 1; decide per class whether the rest are
removed or kept as unreachable, and write the decision down either way.

---

## Resolved: `odmlib/data/valuesets.json`

The `odm_2_0` block was wrong in both directions. Fixed, and the Phase 0 guard extended so
it cannot drift again.

**A correction first, because an earlier draft of this section had it backwards.** The two
directions are not symmetric:

| | Behaviour |
|---|---|
| Key with no matching descriptor | **Inert.** Unused data. |
| `ValueSetString` descriptor with no key | **Raises.** `value_set` returns the unknown sentinel, `validate` maps it to `False`, and `ValidValues.__set__` raises for *every* value — the attribute cannot be set at all. |

What was wrong:

- **Over-restrictive — odmlib rejected schema-valid values.** `ItemGroupDef.Type` and
  `TrialPhase.Value` have XSD types that union an enumeration with bare `xs:string` (an
  extensible vocabulary) but were enforced as closed lists; `ODM.ODMVersion` is a pattern
  admitting `2.0.1` but was stored as the literal list `["2.0"]`.
- **Under-restrictive — closed enumerations never checked.** `Standard.Name`, `.Type` and
  `.PublishingSet` were plain `T.String`, so `Standard(Type="Nonsense")` built.
  (`Standard.Status` is an extensible union and is now an open entry, not a closed one.)
- **Wrong values.** `MethodDef.Type` accepted the invalid `Other` and rejected the valid
  `Preload`; `User.UserType` rejected five of ODM 2.0's nine values. Both lists had been
  copied from the `odm_1_3_2` block, which is **correct for ODM 1.3.2** — ODM 2.0 changed
  both enumerations and the copy never caught up.
- **Nine inert keys**, four of them misspellings of v0.3.0 attribute names. All removed
  rather than corrected-and-staged: a key for a class that does not exist cannot be
  verified, which is exactly how the misspellings survived.

`odmlib/valueset.py` gained a third entry form for the extensible unions —
`{"_values": [...], "_open": true}` — so the CT terms remain documentation while extension
values are accepted, alongside the existing list and `_regex` forms.

**The guard now compares values, not just names.** `compare_valuesets_to_model` classifies
each attribute's XSD type as closed enum / open union / pattern / free and reports
`valueset-missing`, `valueset-values`, `valueset-too-narrow` and `valueset-too-wide` for
every attribute on a modelled class. All three value-set allowlists are empty. The eleven
ClinicalData-layer enumerations are not listed anywhere: the comparison only walks modelled
classes, so they will surface on their own when v0.3.0 adds them.

---

## Cross-cutting work, every phase

- **`odmlib/odm_2_0/model.pyi`** — mirror each change. The stub is *already* stale beyond
  the v0.2.1 work: 10 shared classes disagree with the model, 15 model classes are absent,
  and 8 stub classes no longer exist. Nothing type-checks it, so fold a stub check into the
  Phase 0 guard rather than trusting review.
- **`odmlib/data/valuesets.json`** — new enumerated attributes and the drift above.
- **`odmlib/oid_generator_config.py`** — new/renamed OID-bearing attributes.
- **`odmlib/builder.py`** — only if a helper's output shape changes; `add_condition_def`,
  `add_method_def` and `add_study_event_ref` are already ODM-2.0-aware.
- **Tests** — extend `tests/test_odm_2_0_model.py` (round-trip + XSD-order per class) and
  `tests/test_odm_2_0_known_gaps.py` (shape guards).
- **Docs** — `README.md`, `docs/source/guides/model_reference.rst`, `ROADMAP.md` and
  `CHANGELOG.md`. All four were brought into line as the phases landed. This document
  supersedes `ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`, which is not in the repository; the
  remaining citations of that file are in the historical `[0.2.0]` section of the
  CHANGELOG, where they record what was true at the time.

  *An earlier draft of this line claimed `ROADMAP.md:18` contradicts `:54` on ClinicalData
  coverage. It does not — `:18` is a criterion under "odmlib is ready for 1.0 when all of
  the following are true", not a statement about today. Its present-tense phrasing invited
  the misreading and has been reworded.*
- **Skill** — `.claude/skills/odmlib/` asserts ODM 2.0 model shape in `SKILL.md:83`,
  `references/models.md:62-76` and `references/api-reference.md:173-174`. Re-run
  `python scripts/build_skill_bundle.py --check` after any signature change.

---

## Verification

```bash
# 1. The guard: divergences equal the declared allowlist, no more, no less.
python -m pytest tests/test_odm_2_0_xsd_alignment.py -v

# 2. Per-phase: build a document exercising the phase's classes, then validate.
python - <<'EOF'
from odmlib.odm_parser import ODMSchemaValidator
ODMSchemaValidator(standard="odm", version="2.0").validate_file("odm20_phase.xml")
EOF

# 3. Round-trip and OID integrity for ODM 2.0.
python -m pytest tests/test_odm_2_0_model.py tests/test_odm_2_0_known_gaps.py -v
python -c "from odmlib import create_oid_checker; print(create_oid_checker('odm_2_0').ref_def)"

# 4. No cross-model regression — the blast radius must stay inside odm_2_0.
python -m pytest tests/ -q

# 5. Skill still consistent.
python -m pytest tests/test_skill_contract.py tests/test_skill_examples.py -v
python scripts/build_skill_bundle.py --check
```

The acceptance gate for the whole effort: a single document that exercises every modelled
metadata element validates against the bundled XSD, round-trips through `XMLODMLoader`
unchanged, and passes `verify_oids`. Add it as a fixture so it runs on every commit.

Suggested order: **0 → 1 → 2 → 3 → 4 → 5**. Phase 1 is the only breaking phase; Phases 2–4
are additive-shaped. Phases 3 and 4 can be split across releases if needed — the Phase 0
allowlist makes partial progress honest rather than invisible.

## Out of scope

- `ClinicalData` / `ReferenceData` and their 24 elements — `ROADMAP.md:186-196`, v0.3.0.
  This is also where the repeating-group problem actually bites: `ItemGroupDataGroup`
  (`ODM-clinicaldata.xsd:78-92`, referenced `maxOccurs="unbounded"`) interleaves
  `ItemGroupData` and `ItemData`, and odmlib can neither emit nor recover that ordering.
  It is the one construct in ODM 2.0 that genuinely needs new core machinery, and it can
  be decided when v0.3.0 is planned.
- Core changes to `typed.py` / `odm_element.py` (the sole exception is the `_DURATION_PAT`
  widening in Phase 1, confined to ODM 2.0 usage).
- ODM 1.3.2, Define-XML 2.0/2.1, ARM 1.0, CT 1.1.1, Dataset-XML, Dataset-JSON.

### Core defects found while scoping this, not addressed here

Each sits in machinery shared by all seven model packages, so each deserves its own change
rather than riding along with an ODM 2.0 model edit:

**Namespace registration is the big one, and it is live today — not latent.** Each model
package registers its prefixes at module import; `NamespaceRegistry.reset()`
(`ns_registry.py:114-122`, which just clears two class dicts) discards them, and a cached
module never re-runs, so they are gone for the life of the process. Four distinct
symptoms, verified:

- **Serialization silently emits an undeclared prefix** (`ns_registry.py:298-306` — the
  loop iterates the *registry*, not the prefixes actually used, so anything used-but-absent
  is dropped without a word). This is not hypothetical: the Define-XML creation recipe in
  `README.md:547-554` and `docs/source/guides/creating_documents.rst:112-119`, run
  verbatim, emits `xlink:href` with no `xmlns:xlink` and the result **cannot be reparsed**
  (`ParseError: unbound prefix`). `write_xml` goes through the same call, so files are
  affected identically. `tests/test_define_builder.py:438-447` writes such a file and
  asserts only that its size is non-zero, so nothing catches it.
- **Load with an unregistered prefix raises a bare `SyntaxError`** from ElementTree
  (`odm_loader.py:258-259`), outside the `OdmlibError` hierarchy, so `except OdmlibError`
  does not catch it. `XMLDefineLoader` and `XMLArmLoader` re-register their prefixes at
  `create_document` and are safe; `XMLODMLoader` registers only `odm`, so **CT 1.1.1 is
  exposed today**, as is Define-XML when loaded through the ODM loader.
- **Interleaved loads silently drop foreign-namespace children.** Loading a Define-XML 2.1
  document, then a 2.0 one, rebinds the global `def` prefix; the first document's
  `MetaDataVersion` then yields 0 `leaf` and 0 `ValueListDef` where it had 3 and 8. The
  per-document snapshot (`loader.py:102`) protects serialization but not deferred loading,
  which reads current global state. No `reset()` involved.
- **`Borg.reset()` rebinds on the subclass** rather than the base (`ns_registry.py:114-122`
  is a `classmethod`, so `cls` is `NamespaceRegistry`), leaving `Borg.namespaces` stale.
  Latent while `NamespaceRegistry` is the only subclass.

The recommended sequence is: emit an `OdmlibInteroperabilityWarning` when serialization
would omit a used prefix (~8 lines in one file, no behaviour change, catches all of the
above at the exit point); then give each model module a re-runnable
`register_namespaces()` covering *auxiliary* prefixes only — never the default, which
`XMLODMLoader._set_namespace` owns — called by the three loaders; then make the child
lookup raise `OdmlibParsingError` instead of `SyntaxError`. Do **not** make `reset()`
restore a baseline: that defeats the isolation `tests/conftest.py:16-36` and
`tests/test_namespace_leak.py` exist to enforce.
- `odm_element.py:271-286` — a foreign-namespace attribute is reduced to its local name,
  so `{some-uri}Context` silently overwrites an element's own `Context`.
- `odm_element.py:667-683` — OID reference detection is hardcoded string sniffing
  (`"OID" in attr`, plus a literal `("leafID", "ArchiveLocationID")` tuple), so any rename
  of a reference attribute silently disables its checking. Phase 1 patches the one case it
  needs; the general fragility remains.
