"""The vendored ODM v2.0 fixtures in ``tests/data/odm_v2/`` are intact and valid.

``scripts/sync_odm_v2_fixtures.py`` copies a curated set of the odm-v2 skill's
examples into ``tests/data/odm_v2/`` and records each file in ``MANIFEST.json``
(see ``PROVENANCE.md`` there). Later phases build on them: the JSON round-trip
harness (P3) and the ClinicalData model (P4). So this module pins:

* **integrity** -- every vendored file is in the manifest and still has the
  hash it was copied with, so a fixture cannot be "fixed" in place;
* **validity** -- every XML file validates against the bundled ODM v2.0 XSD;
* **the OID oracle** -- ``ref_targets.json``, derived from the ODM v2.0 spec
  independently of odmlib, agrees with ``create_oid_checker("odm_2_0")`` apart
  from an allowlist that must shrink to empty (P4);
* **known OID findings** -- the dangling references, wrong-type references and
  duplicate OIDs that the upstream content really contains, counted per file.

Each allowlist is compared for equality, not containment, as in
``test_odm_2_0_xsd_alignment.py``: a new finding fails as *unexpected*, and an
entry that no longer occurs fails as *stale*.

When a hash or the manifest check fails, do not edit the fixture. Fix it in
odm-v2 and run::

    python scripts/sync_odm_v2_fixtures.py --source <odm-v2>/.claude/skills/odm-v2/examples
"""
import collections
import hashlib
import json
import os
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.loader as LD
import odmlib.odm_loader as OL
from odmlib import create_oid_checker
from odmlib.exceptions import OdmlibOIDError
from odmlib.odm_parser import ODMSchemaValidator

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "odm_v2")
MANIFEST_PATH = os.path.join(FIXTURE_DIR, "MANIFEST.json")
REF_TARGETS_PATH = os.path.join(FIXTURE_DIR, "ref_targets.json")
NOT_IN_MANIFEST = {"MANIFEST.json", "PROVENANCE.md"}
ODM_V2_NS = "http://www.cdisc.org/ns/odm/v2.0"

#: Attributes the ODM v2.0 spec defines as OID references that the odm_2_0
#: checker does not know yet, because only ClinicalData uses them (UserRef,
#: InvestigatorRef, SignatureRef). P4 adds those classes and empties this set.
CHECKER_GAPS: set[str] = {
    "SignatureOID",
    "UserOID",
}

#: OID findings per vendored XML file, as ``"<kind>:<attribute>": count``.
#: ``unresolved`` is a reference to an OID the document does not define,
#: ``wrong-type`` a reference to an element of a type the attribute may not
#: point at, and ``duplicate`` an OID defined twice. These are the upstream
#: content as published, not odmlib bugs. Until P4 models ClinicalData, loading
#: drops it, so the counts cover metadata references only. The two ClinicalData
#: templates reference a study defined in another file (the data-only case P4b
#: covers with ``ODM_20_DATA_ONLY_SKIP_ATTRS``).
KNOWN_OID_FINDINGS: dict[str, dict[str, int]] = {
    "github/Columbia_Suicidal_Scale/Columbia-Suicide_Severity_Scale_ODMv2.xml": {
        "duplicate:OID": 1,
        "unresolved:CollectionExceptionConditionOID": 3,
        "unresolved:ConditionOID": 6,
        "unresolved:ItemOID": 1,
        "unresolved:SourceOID": 1,
    },
    "github/Conditional_Repeats/Conditional_Repeats.xml": {
        "unresolved:ConditionOID": 1,
    },
    "github/FHIR/fhir-example.xml": {
        "unresolved:ItemOID": 9,
    },
    "github/Inclusion_Exclusion_Criteria_Workflow/Inclusion_Exclusion_Simple_Workflow.xml": {
        "duplicate:OID": 1,
        "unresolved:EndOID": 1,
        "wrong-type:TargetTransitionOID": 1,
    },
    "github/Timing_LZZT/Timing_LZZT_Example_ODM.xml": {
        "unresolved:EndOID": 1,
    },
    "spec/hl7-fhir-integration.xml": {
        "unresolved:ItemOID": 9,
    },
    "spec/multiple-selection-using-nested-itemgroupdef.xml": {
        "unresolved:CodeListOID": 1,
        "unresolved:ItemOID": 5,
    },
    "templates/clinical-data-snapshot.xml": {
        "unresolved:MetaDataVersionOID": 1,
        "unresolved:StudyOID": 1,
    },
    "templates/clinical-data-transactional.xml": {
        "unresolved:MetaDataVersionOID": 1,
        "unresolved:StudyOID": 1,
    },
}

RESYNC_HINT = ("do not edit vendored fixtures; fix them in odm-v2 and run "
               "scripts/sync_odm_v2_fixtures.py --source <odm-v2 examples dir>")


def _load_manifest():
    with open(MANIFEST_PATH, encoding="utf-8") as handle:
        return json.load(handle)


MANIFEST = _load_manifest()
FIXTURES = MANIFEST["fixtures"]


def _sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _files_on_disk():
    found = set()
    for current, _dirs, filenames in os.walk(FIXTURE_DIR):
        for filename in filenames:
            rel = os.path.relpath(os.path.join(current, filename), FIXTURE_DIR)
            found.add(rel.replace(os.sep, "/"))
    return found - NOT_IN_MANIFEST


def _manifest_files():
    """``{relative_path: sha256}`` for everything the manifest vouches for."""
    files = {f["path"]: f["sha256"] for fx in FIXTURES for f in fx["files"]}
    files[MANIFEST["ref_targets"]["path"]] = MANIFEST["ref_targets"]["sha256"]
    return files


def _xml_path(fixture):
    return next(f["path"] for f in fixture["files"] if f["path"].endswith(".xml"))


def _json_path(fixture):
    return next(f["path"] for f in fixture["files"] if f["path"].endswith(".json"))


def oracle_mapping():
    """``{attribute: {element types}}`` from ``ref_targets.json``.

    The checker is keyed by attribute name alone, so the per-element entries are
    merged. An attribute with no targets (FileOID, PriorFileOID) maps to an
    empty set.
    """
    with open(REF_TARGETS_PATH, encoding="utf-8") as handle:
        elements = json.load(handle)["elements"]
    merged = {}
    for attrs in elements.values():
        for attr, targets in attrs.items():
            merged.setdefault(attr, set()).update(targets)
    return merged


def checker_mapping(checker):
    """The same shape, from a ``DynamicOIDRef``: any-of wins, as it does at runtime."""
    mapping = {attr: {target} for attr, target in checker.ref_def.items()}
    mapping.update({attr: set(targets) for attr, targets in checker.ref_def_any_of.items()})
    for attr in checker.skip_attr:
        mapping.setdefault(attr, set())
    return mapping


def oracle_disagreements():
    """``{attribute: description}`` wherever the oracle and the checker differ."""
    oracle = oracle_mapping()
    checker = checker_mapping(create_oid_checker("odm_2_0"))
    out = {}
    for attr in sorted(set(oracle) | set(checker)):
        if oracle.get(attr) != checker.get(attr):
            out[attr] = (f"oracle={sorted(oracle[attr]) if attr in oracle else 'absent'} "
                         f"checker={sorted(checker[attr]) if attr in checker else 'absent'}")
    return out


def _finding_kind(error):
    message = str(error)
    if "is not unique" in message:
        return "duplicate"
    if "is not found" in message:
        return "unresolved"
    if "do not match" in message or "must point at one of" in message:
        return "wrong-type"
    return "other"


def oid_findings(fixture):
    """Load *fixture* strictly and count its OID findings by kind and attribute."""
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
    root = loader.open_odm_document(os.path.join(FIXTURE_DIR, _xml_path(fixture)))
    element = loader.create_odmlib(root, fixture["root"])
    errors = element.validate(collect_errors=True,
                              oid_checker=create_oid_checker("odm_2_0"))
    unexpected_types = [e for e in errors if not isinstance(e, OdmlibOIDError)]
    if unexpected_types:
        raise AssertionError(f"{_xml_path(fixture)}: non-OID validation errors "
                             f"{[str(e) for e in unexpected_types]}")
    return dict(collections.Counter(
        f"{_finding_kind(e)}:{e.attribute}" for e in errors))


class TestManifest(TestCase):
    """Every vendored file is accounted for and unchanged since it was synced."""

    def test_manifest_covers_every_vendored_file(self):
        on_disk, listed = _files_on_disk(), set(_manifest_files())
        self.assertEqual(
            (on_disk - listed, listed - on_disk), (set(), set()),
            f"(not in MANIFEST.json, listed but missing); {RESYNC_HINT}")

    def test_hashes_match_manifest(self):
        for rel, expected in sorted(_manifest_files().items()):
            with self.subTest(file=rel):
                self.assertEqual(_sha256(os.path.join(FIXTURE_DIR, rel)), expected,
                                 RESYNC_HINT)

    def test_every_fixture_records_its_provenance(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture["id"]):
                self.assertIn(fixture["status"], ("verbatim", "corrected"))
                self.assertEqual(bool(fixture["fixes"]), fixture["status"] == "corrected")
                self.assertIn(fixture["json_produced_by"], ("odmlib", "odm_json.py"))
                self.assertTrue(fixture["licence"])
                self.assertEqual(len(fixture["files"]), 2)
                for entry in fixture["files"]:
                    self.assertTrue(entry["source_path"])

    def test_manifest_records_the_source_commit(self):
        source = MANIFEST["source"]
        self.assertRegex(source["commit"] or "", r"^[0-9a-f]{40}$")
        self.assertFalse(source["dirty"], "fixtures were synced from uncommitted files")

    def test_selection_covers_clinical_data_and_both_roots(self):
        """P3 and P4 rely on these shapes being present."""
        self.assertEqual(len(FIXTURES), 25)
        self.assertEqual(sum(f["has_clinical_data"] for f in FIXTURES), 12)
        self.assertEqual({f["root"] for f in FIXTURES}, {"ODM", "MetaDataVersion"})


class TestFixturesAreValid(TestCase):
    """The fixtures are what they claim to be."""

    @classmethod
    def setUpClass(cls):
        cls.validator = ODMSchemaValidator(standard="odm", version="2.0")

    def test_every_xml_validates_against_bundled_xsd(self):
        for fixture in FIXTURES:
            with self.subTest(file=_xml_path(fixture)):
                path = os.path.join(FIXTURE_DIR, _xml_path(fixture))
                errors = [str(e).splitlines()[0] for e in self.validator.xsd.iter_errors(path)]
                self.assertEqual(errors, [])

    def test_every_json_describes_the_same_document_as_its_xml(self):
        """Same identifying attribute on the root: FileOID, or OID for a MetaDataVersion.

        An ``ODM`` document's JSON is the root object itself. A fixture rooted
        at another element is wrapped as ``{"<root>": {...}}``.
        """
        for fixture in FIXTURES:
            with self.subTest(file=_json_path(fixture)):
                with open(os.path.join(FIXTURE_DIR, _json_path(fixture)),
                          encoding="utf-8") as handle:
                    data = json.load(handle)
                xml_root = ET.parse(os.path.join(FIXTURE_DIR, _xml_path(fixture))).getroot()
                self.assertEqual(xml_root.tag, f"{{{ODM_V2_NS}}}{fixture['root']}")
                if fixture["root"] == "ODM":
                    key = "FileOID"
                else:
                    self.assertEqual(list(data), [fixture["root"]])
                    data, key = data[fixture["root"]], "OID"
                self.assertEqual(data.get(key), xml_root.get(key))


class TestRefTargetsOracle(TestCase):
    """``create_oid_checker("odm_2_0")`` agrees with the spec-derived oracle."""

    def test_oracle_matches_oid_checker(self):
        disagreements = oracle_disagreements()
        unexpected = {f"{a}: {d}" for a, d in disagreements.items() if a not in CHECKER_GAPS}
        stale = CHECKER_GAPS - set(disagreements)
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            "(new disagreements, stale CHECKER_GAPS entries)")

    def test_gaps_are_attributes_the_checker_lacks(self):
        """An allowlisted attribute is missing from the checker, not mis-targeted."""
        checker = checker_mapping(create_oid_checker("odm_2_0"))
        oracle = oracle_mapping()
        for attr in sorted(CHECKER_GAPS):
            with self.subTest(attribute=attr):
                self.assertNotIn(attr, checker)
                self.assertTrue(oracle[attr])

    def test_oracle_is_not_trivially_small(self):
        self.assertGreaterEqual(len(oracle_mapping()), 40)


class TestKnownOIDFindings(TestCase):
    """The upstream content's real OID problems, pinned per file."""

    def _check(self, directories):
        actual = {}
        for fixture in FIXTURES:
            path = _xml_path(fixture)
            if path.split("/")[0] in directories:
                findings = oid_findings(fixture)
                if findings:
                    actual[path] = findings
        expected = {path: counts for path, counts in KNOWN_OID_FINDINGS.items()
                    if path.split("/")[0] in directories}
        self.assertEqual(actual, expected)

    def test_vendored_github_examples_report_known_dangling_refs(self):
        self._check({"github"})

    def test_vendored_spec_and_template_documents_report_known_oid_findings(self):
        self._check({"spec", "templates"})
