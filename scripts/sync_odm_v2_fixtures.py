#!/usr/bin/env python3
"""Vendor a curated set of odm-v2 skill examples as odmlib test fixtures.

The odm-v2 Claude Code skill (its own repository; see ``V030_DEV_PLAN.md`` D7)
publishes ODM v2.0 examples that all validate against the official XSD: the
spec's examples, the cdisc-org/DataExchange-ODM GitHub examples, and
hand-written templates, each as an XML + JSON pair. odmlib copies a curated
subset into ``tests/data/odm_v2/`` so its tests do not depend on a sibling
checkout. This script is the only thing that should write there.

It writes, under ``tests/data/odm_v2/``:

* the selected example files, at the same relative paths as in the odm-v2
  ``examples/`` directory (``templates/``, ``spec/``, ``github/<dir>/``);
* ``ref_targets.json``, a snapshot of every element's ``ref_targets`` from the
  skill's ``model/odm-v2.0.json`` -- an oracle for
  ``create_oid_checker("odm_2_0")`` that was derived independently of odmlib;
* ``MANIFEST.json``: per fixture, its source path, sha256, status
  (verbatim/corrected, with the corrections), the tool that produced the
  JSON, the licence, and the odm-v2 commit it was synced from.

``PROVENANCE.md`` sits beside them and is maintained by hand.

Usage::

    python scripts/sync_odm_v2_fixtures.py --source <odm-v2>/.claude/skills/odm-v2/examples
    python scripts/sync_odm_v2_fixtures.py --check --source <same path>

``--check`` writes nothing and exits 1 if the vendored copies, the manifest or
the oracle no longer match the source, or if the source's ODM v2.0 XSDs differ
from ``odmlib/schemas/odm/2.0/``. The odm-v2 commit alone is not compared:
moving the source forward without touching a vendored file is not drift.

``tests/test_vendored_fixtures.py`` checks the vendored side (hashes, XSD
validity, the oracle) without needing the source checkout.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST_DIR = os.path.join(REPO_ROOT, "tests", "data", "odm_v2")
BUNDLED_XSD_DIR = os.path.join(REPO_ROOT, "odmlib", "schemas", "odm", "2.0")
MANIFEST_NAME = "MANIFEST.json"
REF_TARGETS_NAME = "ref_targets.json"
HAND_MAINTAINED = {"PROVENANCE.md"}

#: The curated selection, by ``index.json`` section and example id. Every id
#: must resolve to an entry with status ``verbatim`` or ``corrected``.
SELECTION = {
    # All four hand-written document templates.
    "templates": [
        "clinical-data-snapshot",
        "clinical-data-transactional",
        "study-design",
        "study-metadata",
    ],
    # The spec's full documents: three with ClinicalData, two metadata-only.
    "examples": [
        "multiple-selection-using-nested-itemgroupdef",
        "clinical-data-query-examples-opening-a-query",
        "clinical-data-query-examples-transaction-history",
        "hl7-fhir-integration",
        "file-conformity-xml-file-conformity",
    ],
    # Every DataExchange-ODM example that validates (16 of 19; odm-v2
    # excludes the two ODM 1.3.2 files and one that fails the XSD).
    "github": [
        "atlas-rs-atlas-qs-odmv2",
        "chronic-low-back-pain-chronic-low-back-pain-example",
        "columbia-suicidal-scale-columbia-suicide-severity-scale-odmv2",
        "conditional-repeats-conditional-repeats",
        "crossover-studydesign-crossover-studydesign",
        "data-collection-repeatingig-uc-d-example",
        "demographics-race-demographics-race-check-all-that-apply",
        "fhir-fhir-example",
        "inclusion-exclusion-criteria-workflow-inclusion-exclusion-simple-workflow",
        "matrix-crf-from-taug-dyslipidemia-1-0-hypercholesterolemia-cv-risk-"
        "factors-fh-crf-alternative-valuelists",
        "physio-underwater-therapy-workflow-physio-underwater-therapy-bpmn-to-"
        "odmv2-workflow-2019-10-18-result",
        "physio-underwater-therapy-workflow-physio-underwater-therapy-bpmn-to-"
        "odmv2-workflow-result",
        "protocol-to-workflow-result-odmv2",
        "repeating-itemgroup-cdash-1-1-stroke-lungdisease-ibd-cancerhistory-crf-"
        "cdash-1-1-mh-example-stroke-lungdisease-ibd-cancerhistory",
        "simpletimingconstraints-simpletimingconstraints",
        "timing-lzzt-timing-lzzt-example-odm",
    ],
}

#: Licence by origin; the full notices are in tests/data/odm_v2/PROVENANCE.md.
LICENCES = {
    "templates": "MIT (odm-v2, Copyright (c) 2022-2026 Sam Hume)",
    "examples": "CDISC ODM v2.0 specification example, used with attribution "
                "(see PROVENANCE.md); corrections and JSON are MIT (odm-v2)",
    "github": "MIT (cdisc-org/DataExchange-ODM, Copyright (c) 2022 cdisc); "
              "JSON is MIT (odm-v2)",
}

#: index.json's ``json_source`` -> the tool that produced the JSON.
JSON_PRODUCERS = {"odmlib": "odmlib", "odm_json converter": "odm_json.py"}

ODM_NS = "{http://www.cdisc.org/ns/odm/v2.0}"


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git_commit(source):
    """Return ``(commit, dirty)`` for the repository containing *source*."""
    try:
        commit = subprocess.run(
            ["git", "-C", source, "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True).stdout.strip()
        status = subprocess.run(
            ["git", "-C", source, "status", "--porcelain", "--", "."],
            check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None, None
    return commit, bool(status)


def _xml_facts(path):
    """Return ``(root_local_name, has_clinical_data)`` for an XML file."""
    root = ET.parse(path).getroot()
    has_cd = root.find(f".//{ODM_NS}ClinicalData") is not None or \
        root.tag == f"{ODM_NS}ClinicalData"
    return root.tag.split("}")[-1], has_cd


def plan_fixtures(source):
    """Resolve SELECTION against ``<source>/index.json``.

    Returns ``(label, fixtures)``: ``fixtures`` is the manifest's list, each
    file carrying its ``source_path`` (relative to *source*) and ``sha256``.
    """
    with open(os.path.join(source, "index.json"), encoding="utf-8") as handle:
        index = json.load(handle)

    fixtures = []
    for section, ids in SELECTION.items():
        by_id = {entry["id"]: entry for entry in index[section]}
        for example_id in ids:
            entry = by_id.get(example_id)
            if entry is None:
                raise SystemExit(f"{section}/{example_id}: not in index.json")
            if entry.get("status") not in ("verbatim", "corrected"):
                raise SystemExit(f"{section}/{example_id}: status "
                                 f"{entry.get('status')!r} cannot be vendored")
            paths = entry.get("files") or []
            xml_paths = [p for p in paths if p.endswith(".xml")]
            json_paths = [p for p in paths if p.endswith(".json")]
            if len(xml_paths) != 1 or len(json_paths) != 1:
                raise SystemExit(f"{section}/{example_id}: expected one XML and "
                                 f"one JSON file, got {paths}")
            xml_source = os.path.join(source, xml_paths[0])
            root, has_cd = _xml_facts(xml_source)
            fixture = {
                "id": example_id,
                "origin": section,
                "title": entry.get("title"),
                "root": root,
                "has_clinical_data": has_cd,
                "status": entry["status"],
                "fixes": entry.get("fixes") or [],
                "json_produced_by": JSON_PRODUCERS[entry["json_source"]],
                "licence": LICENCES[section],
                "files": [
                    {"path": rel, "source_path": rel,
                     "sha256": sha256_file(os.path.join(source, rel))}
                    for rel in (xml_paths[0], json_paths[0])
                ],
            }
            if section == "github":
                fixture["upstream"] = ("cdisc-org/DataExchange-ODM: examples/"
                                       + entry["source_file"])
            elif section == "examples":
                fixture["appears_in"] = [
                    f"{s['doc']} › {s['heading']} ({s['caption']})"
                    for s in entry.get("sources") or []]
            fixtures.append(fixture)
    return index.get("label"), fixtures


def build_ref_targets(source):
    """Return the oracle snapshot built from ``<source>/../model/odm-v2.0.json``."""
    model_path = os.path.join(os.path.dirname(source), "model", "odm-v2.0.json")
    with open(model_path, encoding="utf-8") as handle:
        model = json.load(handle)
    elements = {
        name: {attr: sorted(targets)
               for attr, targets in sorted(element["ref_targets"].items())}
        for name, element in sorted(model["elements"].items())
        if element.get("ref_targets")
    }
    return {
        "label": model.get("label"),
        "namespace": model.get("namespace"),
        "source_path": "../model/odm-v2.0.json",
        "note": "Per element, each OID-reference attribute and the element types "
                "the ODM v2.0 spec lets it point at. An empty list means the "
                "attribute names no element in the document (FileOID, "
                "PriorFileOID).",
        "elements": elements,
    }


def dumps(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def build_manifest(source, label, fixtures, ref_targets_text):
    commit, dirty = git_commit(source)
    return {
        "generated_by": "scripts/sync_odm_v2_fixtures.py",
        "source": {
            "repository": "odm-v2 (Claude Code skill)",
            "path": ".claude/skills/odm-v2/examples",
            "commit": commit,
            "dirty": dirty,
            "label": label,
        },
        "ref_targets": {
            "path": REF_TARGETS_NAME,
            "source_path": "../model/odm-v2.0.json",
            "sha256": hashlib.sha256(ref_targets_text.encode("utf-8")).hexdigest(),
        },
        "fixtures": fixtures,
    }


def _comparable(manifest):
    """The manifest without the fields --check deliberately ignores."""
    clone = json.loads(json.dumps(manifest))
    clone.get("source", {}).pop("commit", None)
    clone.get("source", {}).pop("dirty", None)
    return clone


def vendored_files():
    """Relative paths (POSIX) of every file under DEST_DIR."""
    found = set()
    for current, dirnames, filenames in os.walk(DEST_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for filename in filenames:
            if filename in (".DS_Store", "Thumbs.db"):
                continue
            rel = os.path.relpath(os.path.join(current, filename), DEST_DIR)
            found.add(rel.replace(os.sep, "/"))
    return found


def xsd_drift(source):
    """Differences between the source's ODM v2.0 XSDs and the bundled ones."""
    schema_dir = os.path.join(os.path.dirname(source), "schema")
    if not os.path.isdir(schema_dir):
        return [f"source schema directory not found: {schema_dir}"]
    theirs = {f for f in os.listdir(schema_dir) if f.endswith(".xsd")}
    ours = {f for f in os.listdir(BUNDLED_XSD_DIR) if f.endswith(".xsd")}
    problems = [f"XSD only in odm-v2: {f}" for f in sorted(theirs - ours)]
    problems += [f"XSD only in odmlib: {f}" for f in sorted(ours - theirs)]
    problems += [f"XSD differs: {f}" for f in sorted(theirs & ours)
                 if sha256_file(os.path.join(schema_dir, f))
                 != sha256_file(os.path.join(BUNDLED_XSD_DIR, f))]
    return problems


def check(source):
    label, fixtures = plan_fixtures(source)
    ref_targets_text = dumps(build_ref_targets(source))
    expected_manifest = build_manifest(source, label, fixtures, ref_targets_text)
    expected = {f["path"]: f["sha256"] for fx in fixtures for f in fx["files"]}

    problems = []
    on_disk = vendored_files() - HAND_MAINTAINED - {MANIFEST_NAME, REF_TARGETS_NAME}
    problems += [f"missing: {p}" for p in sorted(set(expected) - on_disk)]
    problems += [f"not in the selection: {p}" for p in sorted(on_disk - set(expected))]
    for rel in sorted(set(expected) & on_disk):
        if sha256_file(os.path.join(DEST_DIR, rel)) != expected[rel]:
            problems.append(f"content differs from source: {rel}")

    ref_path = os.path.join(DEST_DIR, REF_TARGETS_NAME)
    if not os.path.isfile(ref_path):
        problems.append(f"missing: {REF_TARGETS_NAME}")
    else:
        with open(ref_path, encoding="utf-8") as handle:
            if handle.read() != ref_targets_text:
                problems.append(f"{REF_TARGETS_NAME} differs from the source model")

    manifest_path = os.path.join(DEST_DIR, MANIFEST_NAME)
    if not os.path.isfile(manifest_path):
        problems.append(f"missing: {MANIFEST_NAME}")
    else:
        with open(manifest_path, encoding="utf-8") as handle:
            current = json.load(handle)
        if _comparable(current) != _comparable(expected_manifest):
            problems.append(f"{MANIFEST_NAME} is stale")
        commit = expected_manifest["source"]["commit"]
        if commit and current.get("source", {}).get("commit") != commit:
            print(f"note: synced from {current.get('source', {}).get('commit')}, "
                  f"source is now at {commit} (vendored content unaffected)")

    problems += xsd_drift(source)

    if not problems:
        print(f"vendored fixtures are up to date ({len(expected)} files, "
              f"{len(fixtures)} fixtures)")
        return 0
    for problem in problems:
        print(f"  {problem}")
    print("\nrun: python scripts/sync_odm_v2_fixtures.py --source " + source)
    return 1


def sync(source):
    label, fixtures = plan_fixtures(source)
    ref_targets_text = dumps(build_ref_targets(source))
    manifest = build_manifest(source, label, fixtures, ref_targets_text)
    expected = {f["path"] for fx in fixtures for f in fx["files"]}

    # Remove files an earlier sync vendored that are no longer selected.
    # Anything else unexpected is reported, never deleted.
    manifest_path = os.path.join(DEST_DIR, MANIFEST_NAME)
    previously = set()
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as handle:
            previously = {f["path"] for fx in json.load(handle).get("fixtures", [])
                          for f in fx["files"]}
    for rel in sorted(previously - expected):
        path = os.path.join(DEST_DIR, rel)
        if os.path.isfile(path):
            os.remove(path)
            print(f"removed (deselected): {rel}")

    for rel in sorted(expected):
        target = os.path.join(DEST_DIR, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(os.path.join(source, rel), "rb") as src:
            payload = src.read()
        with open(target, "wb") as dst:
            dst.write(payload)

    with open(os.path.join(DEST_DIR, REF_TARGETS_NAME), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write(ref_targets_text)
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(dumps(manifest))

    strays = vendored_files() - expected - HAND_MAINTAINED - {
        MANIFEST_NAME, REF_TARGETS_NAME}
    for rel in sorted(strays):
        print(f"warning: not in the selection, left in place: {rel}")
    for problem in xsd_drift(source):
        print(f"warning: {problem} (the bundled XSD is never modified here)")
    if manifest["source"]["dirty"]:
        print("warning: the source has uncommitted changes; the recorded "
              "commit does not fully describe what was copied")
    print(f"wrote {len(expected)} files ({len(fixtures)} fixtures), "
          f"{REF_TARGETS_NAME} and {MANIFEST_NAME} to {DEST_DIR}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", required=True,
                        help="the odm-v2 skill's examples/ directory")
    parser.add_argument("--check", action="store_true",
                        help="report drift and exit 1 if stale; write nothing")
    args = parser.parse_args(argv)
    source = os.path.abspath(args.source)
    if not os.path.isfile(os.path.join(source, "index.json")):
        raise SystemExit(f"not an odm-v2 examples directory (no index.json): {source}")
    return check(source) if args.check else sync(source)


if __name__ == "__main__":
    sys.exit(main())
