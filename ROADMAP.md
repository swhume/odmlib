# odmlib Roadmap: v0.2.0 → v1.0

**Author:** Sam Hume  
**Last Updated:** May 2026

---

## 1. What v1.0 Means for odmlib

A v1.0 release signals to the clinical research community that odmlib is **production-ready**: the API is stable, the core standards are fully covered, documentation is comprehensive, the project is the preferred library for AI-assisted clinical data development, and the governance and community infrastructure exist to sustain it long-term.

### 1.1 v1.0 Readiness Criteria

odmlib is ready for 1.0 when **all** of the following are true:

1. **API stability contract.** The public API (model classes, loaders, builders, converters, validators) has been stable across at least two minor releases following v0.3.0, with no breaking changes beyond those announced in deprecation notices.

2. **Core standards completeness.** ODM 1.3.2, Define-XML 2.0/2.1 (including ARM 1.0), Dataset-XML 1.0.1, Dataset-JSON 1.1, and CT-XML 1.1.1 models are fully implemented and round-trip tested. The ODM v2.0 model covers Study metadata, AdminData, ClinicalData, and ReferenceData.

3. **Test coverage ≥ 90%** as a CI-enforced floor, with no critical code paths untested. Property-based tests cover serialization round-trips for every model.

4. **Documentation completeness.** API reference, user guides, runnable example programs, and AI-oriented reference documentation (`CLAUDE.md` + Claude Code skill) are published and current. Every supported model package has a Sphinx API reference page and a how-to guide.

5. **AI readiness validated.** A published, reproducible benchmark demonstrates that Claude (and other LLMs that consume the skill) produce schema-valid, working code for ODM/Define-XML/Dataset-JSON tasks when guided by the odmlib skill, materially outperforming unaided generation.

6. **Community infrastructure.** Code of Conduct, finalized `CONTRIBUTING.md`, finalized `GOVERNANCE.md`, finalized `CONTRIBUTORS.md`, `SECURITY.md`, `CITATION.cff`, public discussion forum, and a project logo are in place.

7. **CI/CD maturity.** Automated testing, linting (ruff), type checking (mypy strict on core modules), documentation builds, and PyPI publishing all run via GitHub Actions with no manual steps.

8. **Zero deprecated APIs remaining.** All items deprecated in v0.2.0 (manual `OIDRef` classes, `ValueError`/`TypeError` dual-inheritance) have been removed.

---

## 2. Current State: v0.2.0 Assessment

v0.2.0 is a substantial release that ships much more than incremental feature work. It establishes the foundation on which v1.0 is built.

### What v0.2.0 Delivers

| Area | Status | Notes |
|------|--------|-------|
| Structured exceptions + `ErrorCollector` | ✅ | Full hierarchy, fail-fast and collect-all-errors modes |
| Permissive loading mode | ✅ | `ValidationMode` flag enum, `permissive()` context manager, graduated control (SKIP_REQUIRED, SKIP_TYPE, SKIP_FORMAT, SKIP_VALUESET); 70 dedicated tests |
| `ODMBuilder` fluent API | ✅ | `add_study()`, `add_metadata_version()`, `add_item_group_def()`, `add_item_def()`, `add_code_list()`, `build()` |
| Element search methods | ✅ | `find_all()`, `find_by(**kwargs)` |
| Dataset-JSON v1.1 (ODMElement model) | ✅ | Read, write, JSON, NDJSON, converter, DefineFlattener |
| Dynamic OID ref/def checking | ✅ | Model introspection replaces manual OIDRef; ODM v2.0 supported |
| ARM 1.0 model | ✅ | 48 classes, full docstring coverage, integrated with Define-XML 2.1 |
| Valueset regex validation | ✅ | `ValueSet.validate()`, `ValueSet.describe()` |
| Pandas DataFrame integration | ✅ | Metadata export, clinical data flatten, DataFrame↔DatasetJSON |
| Modern packaging (`pyproject.toml`) | ✅ | Semantic versioning, optional dependency groups |
| GitHub Actions CI/CD | ✅ | Testing (Py 3.10–3.13), docs build, PyPI publish on tag |
| Type stubs (.pyi) | 🟡 | Exist for `odm_1_3_2`, `define_2_0`, `define_2_1`, `odm_2_0`; inline type hints still pending |
| ODM v2.0 model | 🟡 | Study metadata + AdminData; ClinicalData/ReferenceData pending. Model/XSD safe subset landed (TranslatedText `Type` required + builder default, `Arm`/`CheckValue` de-dup, 12 valueset keys, permissive valueset bypass); five structural model/XSD gaps deferred to v0.2.1 — see `ODM20-MODEL-XSD-DIFFERENCES_PLAN.md` |
| Example programs | ✅ | All `odmlib_examples` run against v0.2.0; new examples highlight v0.2.0 features; cleanup planned for v0.3.0 |
| `CLAUDE.md` (AI reference docs) | ✅ | Ships with v0.2.0 |
| `GOVERNANCE.md`, `CONTRIBUTING.md`, `CONTRIBUTORS.md` | ✅ | Ship with v0.2.0; 8 contributors recognized; refined in subsequent releases, final versions targeted for v0.5.0 |
| GitHub Discussions | ✅ | Enabled as primary community forum with v0.2.0 |
| Project logo | ✅ | Ships with v0.2.0 |
| Removal of legacy `dataset_json` (plain classes) | ✅ | Package removed entirely; never released to PyPI |
| Define-XML v2.1 `SubClass` nesting | ❌ | Currently flat `ParentClass` attribute; spec allows recursive `SubClass` children |
| Claude Code skill | ❌ | Drafted concurrently with v0.2.0; released in v0.2.1 after testing |

### Test Suite

- **1,243 tests** passing, 23 subtests passing, 24 warnings
- **94% line coverage** measured locally
- CI threshold currently configured at a conservative floor; raising to 90% as a CI-enforced floor is a small task for v0.3.0
- Property-based tests (Hypothesis) cover typed descriptors and serialization

### Contributors

The CONTRIBUTORS.md file shipping with v0.2.0 recognizes 8 contributors to the project to date, the majority through manually merged contributions. This is a meaningful adoption signal for a specialized library and a useful baseline against which v0.5.0 community-growth work can be measured.

---

## 3. Release Plan

### 3.1 Versioning Strategy

The path to v1.0 runs through three minor releases beyond v0.2.0, plus a patch release for the Claude Code skill.

```
v0.2.0   May 2026             — Foundation (current)
v0.2.1   Mid-2026             — Claude Code skill
v0.3.0   October 2026         — ODM v2.0 ClinicalData, deprecation removals, AI maturation
v0.4.0   Q1 2027              — Type safety, conversions, builder expansion
v0.5.0   Q2–Q3 2027           — Community and governance finalization
v1.0.0   Q4 2027              — Stable release
```

### 3.2 Release Details

---

#### v0.2.1 — Claude Code Skill + ODM v2.0 Model/XSD Alignment (Mid-2026)

**Theme:** Ship the Claude Code skill into the ecosystem early so it accumulates real-world feedback rather than waiting until v0.3.0; and close the remaining structural gaps between the odmlib ODM v2.0 model and the published ODM 2.0 XSD that v0.2.0 deferred.

##### Why a Dedicated Patch Release

The skill carries the value proposition that odmlib is the preferred library for AI-assisted clinical data work, but it requires careful testing before exposure to users. Shipping it in a patch release decouples that careful testing from the v0.2.0 timeline while still getting it into the wild months before v0.3.0. Each subsequent release matures and improves the skill in lockstep with the library.

##### Deliverables

- **Claude Code skill file** published in the repository at `.claude/skills/odmlib/SKILL.md` (or the convention current at release time). The skill includes:
  - Triggering description for ODM, Define-XML, Dataset-XML, Dataset-JSON, CT-XML, ARM, and CRF metadata tasks.
  - Standards-to-package mapping table with the correct loader for each document type.
  - Namespace registration patterns for each standard (the single largest source of errors in hand-written odmlib code).
  - Conservative coverage of the 5–10 most-common operations with verified, working code templates.
  - Validation patterns covering strict mode, permissive mode, and `ErrorCollector` usage.
  - Known pitfalls (element ordering, required attributes, ARM vs. base Define-XML loader, deprecated APIs to avoid).
- **Installation instructions** in `CLAUDE.md` and `README.md` showing how to add the skill to a Claude Code configuration.
- **Baseline empirical benchmark** at `docs/benchmarks/claude-skill-comparison.md`. Methodology, fixed prompt set, evaluation criteria, raw outputs, and reproduction instructions for the first run of Claude with vs. without the skill. This is the v1.0 of the benchmark; v0.3.0 re-runs it with a richer skill and richer docstrings.
- **GitHub issue template** for skill feedback ("Claude generated incorrect odmlib code") to capture real failure modes.

##### Scope Discipline

Initial skill scope is intentionally conservative. It is better to ship a 5-operation skill that always works than a 15-operation skill that fails on 3 of them. Coverage expands with each subsequent release as failure modes are observed and addressed.

##### ODM v2.0 Model/XSD Alignment

Building the ODM 2.0 `ODMBuilder` example surfaced ten differences between
the odmlib ODM v2.0 model and the bundled ODM 2.0 XSD (recorded in
`ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`). v0.2.0 shipped the safe,
non-structural subset (TranslatedText `Type` now required with a builder
default; duplicate `Arm`/`CheckValue` de-duplicated; 12 missing odm_2_0
valueset keys added; permissive mode can now bypass an unregistered
valueset). The remaining five are **content-model / class-shape changes**
deferred here because each has a high regression surface and no safe
additive form. They are pinned by strict-`xfail` markers in
`tests/test_odm_2_0_known_gaps.py` (CI fails loudly if a gap is silently
fixed or regressed, forcing the marker's removal when the fix lands):

- **ConditionDef** — add the XSD-required `MethodSignature` child and make
  `Description` required (plan §3.1). Today every odmlib `ConditionDef` (and
  any `CollectionExceptionConditionOID` targeting it) is schema-invalid.
- **FormalExpression** — redesign from text-based to the XSD's
  `choice(Code | ExternalCodeLib)` element form; add the `Code` and
  `ExternalCodeLib` classes (plan §3.2). Text formal expressions are
  schema-invalid in ODM 2.0.
- **Protocol** — remove/redirect `StudyEventRef` (removed from the ODM 2.0
  schema) to `StudyEventGroupRef*` plus the study-design children (plan §3.3).
- **MetaDataVersion / Protocol timing** — remove `MetaDataVersion.StudyTiming`
  and add the XSD `Protocol/StudyTimings` plural container (plan §3.4).
- **StudyEventGroupDef** — add the XSD-required `StudyEventDefGroup`
  `(StudyEventGroupRef?, StudyEventRef?)` child group (plan §3.5).

The **ItemDef** attribute-set alignment (former plan §3.7 — drop
`FractionDigits` / `DatasetVarName` / `SDSVarName`, add `DisplayFormat` /
`VariableSet`) has since landed in v0.2.1; see CHANGELOG and
`ODM20-MODEL-XSD-DIFFERENCES_PLAN.md` §3.7. Its XSD `ItemDef/ValueListRef`
child element remains deferred (no `ValueListRef` class in `odm_2_0` yet) —
see `ODM20-MODEL-XSD-DIFFERENCES_PLAN.md` §10.

Workaround until then: the `v0-2-snippets/odm20-odm-builder.py` example
documents the schema-valid safe subset (route around the five above). See
`ODM20-MODEL-XSD-DIFFERENCES_PLAN.md` §6 for full detail. ODM v2.0
ClinicalData/ReferenceData breadth remains separately scoped under v0.3.0.

---

#### v0.3.0 — ODM v2.0 ClinicalData, Deprecation Removals, AI Maturation (October 2026)

**Theme:** Close out the deprecations announced in v0.2.0. Complete the ODM v2.0 data hierarchy. Ship the Define-XML v2.1 SubClass nesting fix. Mature the Claude Code skill based on v0.2.1 feedback, expand docstring depth where Claude needs it, and re-run the benchmark.

##### Breaking Changes (Pre-announced in v0.2.0)

These removals are non-negotiable and locked to v0.3.0:

- Remove manual `OIDRef` classes from `odm_1_3_2/rules/`, `define_2_0/rules/`, `define_2_1/rules/`; users migrate to `create_oid_checker()`.
- Remove `ValueError`/`TypeError` dual-inheritance from odmlib exceptions; catching code must use `OdmlibValidationError`, `OdmlibTypeError`, etc.

##### ODM v2.0: ClinicalData and ReferenceData

The CDISC ODM v2.0 specification is stable. v0.3.0 commits to a complete data-layer implementation:

- `ClinicalData`, `SubjectData`, `StudyEventData`, `FormData`, `ItemGroupData`, `ItemData` and any ODM v2.0-specific variants.
- `ReferenceData` and its child hierarchy.
- `AuditRecord`, `Signature`, `Annotation`, `Query` (new in ODM v2.0), and `Association`.
- Loader support and round-trip tests for ODM v2.0 documents containing clinical data.
- All new elements ship with docstrings and round-trip tests.

The ODM v2.0 implementation transitions from "Draft" to "Stable" in the supported-standards table once round-trip tests pass.

##### Define-XML v2.1 SubClass Nesting

The current `SubClass` model uses a flat `ParentClass` string attribute. The Define-XML v2.1 specification allows `SubClass` elements to be nested within other `SubClass` elements (e.g., SDTM > Findings > Findings About > Pharmacogenomics Findings About). v0.3.0:

```python
class SubClass(OE.ODMElement):
    """Defines a subclass within a dataset class hierarchy.
    Supports recursive nesting per the Define-XML 2.1 specification.
    """
    namespace = "def"
    Name = T.Name(required=True)
    ParentClass = T.String()
    SubClass = T.ODMListObject(element_class=None, namespace="def")

# Resolve forward reference
SubClass.SubClass = T.ODMListObject(element_class=SubClass, namespace="def")
```

Tests cover 2-level and 3-level deep SubClass hierarchies with XML↔JSON round-trip serialization.

##### AI Maturation

The Claude Code skill shipped in v0.2.1 has 3–4 months of real-world use by the time v0.3.0 ships. The v0.3.0 AI work uses that feedback:

- **Skill update** — incorporate operations and pitfalls surfaced by user feedback; add coverage of ODM v2.0 ClinicalData and SubClass nesting; remove any mentions of APIs the v0.3.0 deprecation removals eliminated.
- **Comprehensive docstring pass on high-priority packages** — `odm_1_3_2`, `define_2_1`, `dataset_json_1_1`. Each class docstring describes what the element represents in the CDISC standard, what attributes it takes with types and required/optional status, and at least one short usage example. Docstrings on lower-priority packages (`define_2_0`, `dataset_1_0_1`, `ct_1_1_1`) follow in v0.4.0. (`arm_1_0` and `odm_2_0` already have full coverage.)
- **Benchmark re-run** — update `docs/benchmarks/claude-skill-comparison.md` with v0.3.0 results. Show measurable improvement over the v0.2.1 baseline. This establishes the artifact as a regression target for future releases.

##### Builder Testing and Expansion (Phase 1)

The `ODMBuilder` is a popular feature based on early signals. v0.3.0 begins a multi-release effort to test and expand it:

- Expand unit test coverage for the existing `ODMBuilder` ODM 1.3.2 surface (current coverage is functional but light relative to its visibility).
- Add edge-case tests for the fluent API (chained calls, error paths, OID collision handling).
- Add a how-to guide for the builder in `docs/source/guides/`.
- Define the v0.4.0 expansion scope based on user requests received against the v0.3.0 builder.

##### Example Programs Cleanup

All `odmlib_examples` programs run against v0.2.0. v0.3.0 work is cleanup and polish rather than a refresh:

- Update examples to use the v0.3.0 API surface (no deprecated calls).
- Add examples for v0.3.0 features (ODM v2.0 ClinicalData, nested SubClass, permissive load-fix-validate workflow).
- Standardize header comments, input file conventions, and expected-output sections across examples.
- Verify every example is referenced from at least one Sphinx guide page.

##### ARM 1.0 Gap Closure (Phase 1)

ARM 1.0 has the model (48 classes, full docstrings) and 30 tests but lags other major model packages in supporting infrastructure. v0.3.0 closes the highest-priority gaps:

- ~~Add Sphinx API reference page (`docs/source/odmlib.arm_1_0.rst`); list it in `index.rst`.~~ Done.
- Add an ARM how-to guide in `docs/source/guides/`.
- ~~Register ARM in `oid_generator_config.py` so `create_oid_checker("arm_1_0")` works.~~ Done.
- ~~Bundle the ARM 1.0 XSD and register it in `schema_manager._MAIN_SCHEMA` so ARM documents
  can be schema-validated through `ODMSchemaValidator`.~~ Done (not originally on the roadmap).
- Expand ARM test coverage to better match other major models.

Remaining ARM items (Cerberus rules, type stubs) target v0.4.0 alongside the broader type-hint work.

##### Quality and Process

- Raise CI coverage threshold to 90% (current local measurement is 94%).
- Run mypy as a non-blocking CI step to begin surfacing type issues.
- Add round-trip integration tests for any model package still missing them.

---

#### v0.4.0 — Type Safety, Conversions, Builder Expansion (Q1 2027)

**Theme:** Tighten Python type guarantees. Expand the builder. Add the ODM-to-Dataset-JSON converter. Close out remaining ARM and docstring gaps.

##### Inline Type Hints and mypy

The existing `.pyi` stubs cover four model packages but are not exhaustive and require dual maintenance. v0.4.0:

- Adds inline type hints to core modules: `odm_element.py`, `loader.py`, `builder.py`, `dataframe.py`, `context.py`, `descriptor.py`, `typed.py`, `oid_generator.py`, `exceptions.py`, `mode.py`.
- Adds inline type hints to the most-used model classes, prioritizing `define_2_1`.
- Promotes `mypy` to a blocking CI step on core modules. Strict-mode promotion targets v0.5.0.

##### ODM-to-Dataset-JSON Converter

Add a converter that takes an ODM document containing `ClinicalData` and transforms it to one or more Dataset-JSON v1.1 files:

- `odm_clinical_to_dataset_json(odm_obj, define_mdv=None)` → `dict[str, DatasetJSON]`
- Operates on hierarchical ODM clinical data (SubjectData → StudyEventData → FormData → ItemGroupData → ItemData), flattening to tabular form.
- Optional Define-XML MetaDataVersion enriches column metadata (labels, types, lengths).
- Supports both ODM 1.3.2 and ODM v2.0 source documents (the latter now possible thanks to the v0.3.0 ClinicalData model).

##### Builder Testing and Expansion (Phase 2)

Based on feedback against the v0.3.0 builder:

- Define-XML builder — fluent API for constructing Define-XML 2.1 documents.
- Dataset-JSON builder — fluent API for constructing Dataset-JSON v1.1 documents.
- Additional `ODMBuilder` operations identified through user feedback.
- Example programs demonstrating each builder.

##### ARM 1.0 Gap Closure (Phase 2)

- Add Cerberus conformance rules for ARM (`odmlib/arm_1_0/rules/metadata_schema.py`).
- Add ARM type stub (`odmlib/arm_1_0/model.pyi`) — or convert to inline type hints, whichever direction the broader type-hint effort takes.

##### Docstring Completion (Remaining Packages)

Complete docstrings on `define_2_0`, `dataset_1_0_1`, `ct_1_1_1`, and any remaining holes from v0.3.0.

##### CI/CD

- Add `ruff` linting to CI.
- Add a packaging smoke-test job (installs from the built wheel and runs a minimal import + round-trip test).
- Add scheduled weekly CI runs against latest dependency versions.
- Add Codecov integration for coverage badge and PR annotations.

---

#### v0.5.0 — Community and Governance Finalization (Q2–Q3 2027)

**Theme:** Take the governance, contributing, and contributor documents through their final iteration based on community feedback accumulated since v0.2.0. Complete the remaining community infrastructure.

##### Governance Document Finalization

`GOVERNANCE.md`, `CONTRIBUTING.md`, and `CONTRIBUTORS.md` shipped in v0.2.0 and accumulated feedback through v0.3.0 and v0.4.0. v0.5.0 takes them through their final pre-1.0 iteration:

- Incorporate suggestions from contributors and users surfaced in GitHub Discussions and issues.
- Reconcile any drift between the documents (e.g., contribution process described differently in CONTRIBUTING.md vs. GOVERNANCE.md).
- Lock the documents as the v1.0 governance contract.

##### Code of Conduct

Adopt the Contributor Covenant v2.1 (or similar). Place at `CODE_OF_CONDUCT.md`. Designate a contact for CoC concerns.

##### Additional Documents

- `SECURITY.md` with a vulnerability reporting process.
- `CITATION.cff` for academic citation.

##### Quality Gates

- Promote `mypy` to strict-mode blocking on core modules.
- Maintain CI coverage threshold at 90% (or raise to 95% if it can be sustained without becoming brittle).
- Publish Sphinx documentation to GitHub Pages automatically on every merge to `master`.

##### AI Skill Maturity

By v0.5.0 the Claude Code skill has been in the wild for roughly a year and through three update cycles. v0.5.0 work:

- Final pre-1.0 skill update aligned with the v0.5.0 API surface.
- Benchmark re-run; results published as the third data point in the longitudinal series.
- Documented stability commitment for the skill in `CLAUDE.md` so users can rely on it across the v1.0 line.

---

#### v1.0.0 — Stable Release (Q4 2027)

**Theme:** Finalize the API, comprehensive testing, and formal stability commitment.

##### Pre-release Checklist

- [ ] All v0.2.0 deprecations removed (completed in v0.3.0).
- [ ] No new deprecations pending at release.
- [ ] Public API stable across v0.4.0 and v0.5.0 (no breaking changes).
- [ ] Test coverage ≥ 90% as a CI-enforced floor.
- [ ] All model packages have round-trip integration tests (XML↔object↔XML, JSON↔object↔JSON).
- [ ] Property-based tests cover all model serialization paths.
- [ ] Sphinx documentation is complete, published, and version-tagged.
- [ ] Every model package has both a Sphinx API page and a how-to guide.
- [ ] All example programs run successfully against v1.0.0.
- [ ] `CLAUDE.md` and Claude Code skill are current with the v1.0 API.
- [ ] Empirical AI benchmark re-run against v1.0 and results updated.
- [ ] Logo, CoC, finalized governance docs, SECURITY.md, CITATION.cff in place.
- [ ] GitHub Discussions active and monitored.
- [ ] mypy strict blocking in CI on core modules.
- [ ] `pyproject.toml` classifier updated: `Development Status :: 5 - Production/Stable`.
- [ ] CHANGELOG.md complete for all changes since v0.2.0.

##### v1.0 API Stability Promise

After v1.0, odmlib follows semantic versioning strictly:

- **Patch releases (1.0.x):** Bug fixes only, no API changes.
- **Minor releases (1.x.0):** New features, new model elements, new standards support. Existing APIs remain backward compatible. Deprecations announced but not removed.
- **Major releases (2.0.0):** Breaking changes permitted. Deprecated APIs removed.

---

## 4. Feature Details

### 4.1 AI-Readiness: Why It Is a v1.0 Criterion

A pharma developer asking Claude Code to "write a Python program that generates a Define-XML 2.1 document for an SDTM submission" today gets code that reaches for `lxml.etree` and hand-constructs XML. The output is typically plausible but often fails schema validation, misses namespace requirements, omits required attributes, or violates element ordering. The developer then debugs against the CDISC specification until it works.

With the odmlib skill loaded, the same prompt produces code that uses `odmlib.define_2_1.model`, registers namespaces correctly, builds the document with validated descriptors, and serializes it with `write_xml()`. The output validates on first try.

Achieving and maintaining this difference is a multi-release effort:

- **v0.2.1** ships the initial skill (conservative scope, well-tested) and establishes a baseline benchmark.
- **v0.3.0** updates the skill based on real-world feedback, completes high-priority docstrings (so Claude has rich material to draw on when looking up an API on the fly), and re-runs the benchmark to show progressive improvement.
- **v0.4.0–v0.5.0** continue to refine the skill, complete docstrings on remaining packages, and re-run the benchmark.
- **v1.0** locks in the skill against a stable API and publishes the final benchmark.

The benchmark is structured for reproducibility. It includes a fixed prompt set committed to the repository, fixed evaluation criteria (schema validity via `xmlschema`, programmatic LOC counting, manual-correction counting against generated output), recorded model and skill versions, multiple runs per task per condition to capture variance, and public test fixtures.

### 4.2 ODM v2.0 ClinicalData Scope (v0.3.0)

| Element | Notes |
|---------|-------|
| `ClinicalData` | Root container for subject-level data |
| `SubjectData` | Per-subject data container |
| `StudyEventData` | Visit/event-level container |
| `FormData` | Form-level container |
| `ItemGroupData` | Group-level container |
| `ItemData` | Atomic data point (string/numeric/date variants per ODM v2.0 typing) |
| `ReferenceData` | Codelist values and other reference data |
| `Query` | New in ODM v2.0; data clarification queries |
| `AuditRecord` | Audit trail |
| `Signature` | Electronic signatures (model only; `ds:Signature` digital sigs out of scope) |
| `Annotation` | Annotations on data |
| `Association` | Cross-references between data elements |

All new elements ship with docstrings and round-trip tests.

### 4.3 ARM 1.0 Closure Path

ARM 1.0 has a complete model with full docstring coverage but lags other major packages on supporting infrastructure. The full closure path:

| Item | Status | Target |
|------|--------|--------|
| Model classes (48) | ✅ Complete | — |
| Docstrings on all classes | ✅ Complete | — |
| Tests (47 currently) | 🟡 Light coverage | Expand in v0.3.0 |
| Bundled XSD + schema validation | ✅ Complete | — |
| Sphinx API reference page | ✅ Complete | — |
| How-to guide | ❌ Missing | v0.3.0 |
| OID checker registration | ✅ Complete | — |
| Cerberus conformance rules | ❌ Missing | v0.4.0 |
| Type stubs / inline type hints | ❌ Missing | v0.4.0 |

By v0.5.0 ARM is at parity with the other major model packages, satisfying the v1.0 "documentation completeness" criterion.

### 4.4 Builder Expansion Path

The `ODMBuilder` shipped in v0.2.0 is a popular feature based on early signals. Expansion happens in two phases:

- **v0.3.0 — Harden the existing builder.** Expand unit test coverage, add edge-case tests, add a how-to guide, gather user feedback against the v0.3.0 surface.
- **v0.4.0 — Add Define-XML and Dataset-JSON builders.** Apply the same fluent pattern to the two formats users most commonly construct programmatically. Add a comparison example showing builder vs. direct construction.

Post-1.0, a builder for Dataset-XML and a guided builder for ODM v2.0 documents are candidates depending on demand.

### 4.5 SubClass Nesting Implementation Notes

The Define-XML v2.1 specification permits a `SubClass` element to contain child `SubClass` elements, allowing arbitrary depth in dataset classification hierarchies. The current odmlib model approximates this with a flat `ParentClass` string attribute, which is structurally incorrect. v0.3.0 implements recursive nesting via a forward-resolved `ODMListObject` descriptor as shown in §3.2 (v0.3.0).

### 4.6 CI/CD Evolution

| Capability | v0.2.0 | v0.3.0 | v0.4.0 | v0.5.0 |
|-----------|--------|--------|--------|--------|
| Test matrix (Py 3.10–3.13) | ✅ | ✅ | ✅ | ✅ |
| Coverage floor | 70% (loose) | 90% | 90% | 90% (or 95%) |
| Docs build | ✅ | ✅ | ✅ | ✅ |
| PyPI publish on release | ✅ | ✅ | ✅ | ✅ |
| mypy | ❌ | Non-blocking | Blocking, core modules | Strict, core modules |
| ruff linting | ❌ | ❌ | ✅ | ✅ |
| Packaging smoke test | ❌ | ❌ | ✅ | ✅ |
| Weekly dependency CI | ❌ | ❌ | ✅ | ✅ |
| Codecov integration | ❌ | ❌ | ✅ | ✅ |
| Docs auto-publish | ❌ | ❌ | ❌ | ✅ |

---

## 5. Milestone Summary

| Milestone | Key Deliverables | Target |
|-----------|-----------------|--------|
| **v0.2.0** | Foundation: permissive loading, structured exceptions, ODMBuilder, Dataset-JSON v1.1, dynamic OID checking, ARM 1.0, valueset regex, pandas integration, CLAUDE.md, GOVERNANCE/CONTRIBUTING/CONTRIBUTORS, logo, GitHub Discussions, 94% coverage | May 2026 |
| **v0.2.1** | Claude Code skill (conservative initial scope); baseline benchmark; skill feedback issue template | Mid-2026 |
| **v0.3.0** | ODM v2.0 ClinicalData/ReferenceData; SubClass nesting; remove remaining deprecations; skill update + comprehensive docstrings on high-priority packages + benchmark re-run; ARM doc/test/OID-checker gaps; builder hardening; examples cleanup; coverage floor → 90% | October 2026 |
| **v0.4.0** | Inline type hints + mypy blocking; ODM→Dataset-JSON converter; Define-XML and Dataset-JSON builders; ARM Cerberus + type hints; remaining docstring completion; ruff + smoke test + weekly CI + Codecov | Q1 2027 |
| **v0.5.0** | Final iteration of governance docs; CoC; SECURITY.md; CITATION.cff; mypy strict; docs auto-publish; final pre-1.0 skill update + benchmark | Q2–Q3 2027 |
| **v1.0.0** | API freeze; benchmark re-run; classifier update to Production/Stable; release announcement | Q4 2027 |

---

## 6. Post-v1.0 Considerations

Explicitly out of scope for v1.0 but planned for subsequent releases:

- **ODM v2.0 errata and revisions.** As CDISC publishes errata or revisions, track and update.
- **Define-JSON.** When new versions of Define-XML are published, add corresponding model packages.
- **FHIR bridge.** Explore bidirectional conversion between odmlib ODM objects and HL7 FHIR resources (ResearchStudy, ResearchSubject, Observation).
- **Cerberus revisit.** Re-evaluate whether to extract conformance validation into a separate package given how the codebase has evolved.
- **Plugin architecture.** Allow third-party packages to register custom model extensions, loaders, and converters.
- **Performance optimization.** For very large ODM documents (100K+ ItemData elements), consider streaming parsers and lazy loading.
- **Additional builder coverage.** Evaluate expansion of builders to new models.
- **Additional language ports.** Evaluate community demand for odmlib in R and consider reticulate or an R wrapper.

---

## Appendix A: Decision Log

| Decision | Rationale |
|----------|-----------|
| AI readiness is a v1.0 criterion, not a v2.0-and-later concern | A large fraction of clinical data code is now AI-generated; odmlib must shape that code to be the default library for the space |
| Ship the Claude Code skill in v0.2.1 rather than v0.2.0 | Skill quality requires careful testing; a dedicated patch release decouples that testing from the v0.2.0 timeline while still getting the skill into the wild months before v0.3.0 |
| Empirical AI benchmark is a published in-repo artifact | Backs positioning claims with verifiable evidence; gives users reason to adopt the skill; becomes a regression target for future releases |
| Initial skill scope is intentionally conservative | A 5-operation skill that always works is more valuable than a 15-operation skill that fails on 3; trust is earned through reliability |
| Cerberus stays in core (not extracted) | Cerberus is a small library; extraction would add packaging complexity without proportionate benefit; revisit post-v1.0 |
| Governance documents ship in v0.2.0 in draft form, finalized in v0.5.0 | Lets the documents accumulate community feedback during v0.3.0 and v0.4.0 before being locked as the v1.0 governance contract |
| Builder expansion staged across v0.3.0 (harden ODM builder) and v0.4.0 (add Define-XML and Dataset-JSON builders) | Feedback against the hardened v0.3.0 surface informs the v0.4.0 expansion scope rather than building blind |
| Pre-release cadence for v0.3.0 (alpha → rc1 → final) | De-risks the October deadline; allows users to test the deprecation removals and ODM v2.0 ClinicalData before final |
