"""The packed skill bundle must match its source tree.

``.claude/skills/odmlib.skill`` is a zip of ``.claude/skills/odmlib/``.  It is
rebuilt by hand, so an edit to SKILL.md, a reference, or an example that is not
followed by a repack ships a bundle whose content no longer matches the
repository -- and the two then drift silently, because nothing else compares
them.

When one of these fails the fix is a single documented command::

    python scripts/build_skill_bundle.py

Stdlib only: ``zipfile`` plus ``hashlib``.
"""
import hashlib
import os
import zipfile
from unittest import TestCase, skipIf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib")
BUNDLE_PATH = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib.skill")
ROOT_PREFIX = "odmlib"

REBUILD_HINT = "run: python scripts/build_skill_bundle.py"

# An sdist checkout ships neither; skip rather than fail there.
NO_BUNDLE = not (os.path.isdir(SOURCE_DIR) and os.path.isfile(BUNDLE_PATH))
SKIP_REASON = "skill source directory or .skill bundle not present"

EXCLUDED_DIRS = {"__pycache__", ".git", ".pytest_cache", ".ipynb_checkpoints"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".swp", ".orig", ".rej")
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _source_digests():
    """``{bundle_relative_path: sha256}`` for the skill source tree."""
    digests = {}
    for current_root, dirnames, filenames in os.walk(SOURCE_DIR):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            if filename in EXCLUDED_NAMES or filename.endswith(EXCLUDED_SUFFIXES):
                continue
            absolute = os.path.join(current_root, filename)
            relative = os.path.relpath(absolute, SOURCE_DIR).replace(os.sep, "/")
            with open(absolute, "rb") as handle:
                digests[relative] = _sha256(handle.read())
    return digests


def _bundle_digests():
    """``{bundle_relative_path: sha256}`` for the packed bundle."""
    digests = {}
    with zipfile.ZipFile(BUNDLE_PATH) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename
            assert name.startswith(ROOT_PREFIX + "/"), \
                f"bundle member {name!r} is not rooted at {ROOT_PREFIX}/"
            digests[name[len(ROOT_PREFIX) + 1:]] = _sha256(archive.read(info))
    return digests


@skipIf(NO_BUNDLE, SKIP_REASON)
class TestSkillBundleMatchesSource(TestCase):
    """Member set and per-file checksums must agree with the source tree."""

    @classmethod
    def setUpClass(cls):
        cls.source = _source_digests()
        cls.bundle = _bundle_digests()

    def test_bundle_is_a_valid_zip(self):
        with zipfile.ZipFile(BUNDLE_PATH) as archive:
            self.assertIsNone(archive.testzip(), "bundle contains a corrupt member")

    def test_source_tree_is_not_empty(self):
        """Guard against an empty walk making every other assertion vacuous."""
        self.assertGreaterEqual(
            len(self.source), 10,
            f"expected the skill source tree to hold at least 10 files, "
            f"found {len(self.source)}")

    def test_no_source_file_missing_from_bundle(self):
        missing = sorted(set(self.source) - set(self.bundle))
        self.assertFalse(
            missing, f"files present in source but absent from the bundle: "
                     f"{missing}\n{REBUILD_HINT}")

    def test_no_stale_member_in_bundle(self):
        extra = sorted(set(self.bundle) - set(self.source))
        self.assertFalse(
            extra, f"files present in the bundle but absent from source: "
                   f"{extra}\n{REBUILD_HINT}")

    def test_member_sets_are_identical(self):
        self.assertEqual(
            sorted(self.bundle), sorted(self.source),
            f"bundle and source file sets differ\n{REBUILD_HINT}")

    def test_every_member_matches_by_sha256(self):
        mismatched = sorted(
            path for path in set(self.source) & set(self.bundle)
            if self.source[path] != self.bundle[path]
        )
        self.assertFalse(
            mismatched,
            f"{len(mismatched)} bundled file(s) differ from source: "
            f"{mismatched}\n{REBUILD_HINT}")

    def test_bundle_contains_the_expected_entry_points(self):
        """A bundle without SKILL.md would not load as a skill at all."""
        for required in ("SKILL.md", "references/api-reference.md"):
            with self.subTest(path=required):
                self.assertIn(required, self.bundle)


@skipIf(NO_BUNDLE, SKIP_REASON)
class TestSkillBundleShape(TestCase):
    """Structural properties the bundle is expected to keep."""

    def test_all_members_rooted_at_odmlib(self):
        with zipfile.ZipFile(BUNDLE_PATH) as archive:
            for info in archive.infolist():
                with self.subTest(member=info.filename):
                    self.assertTrue(info.filename.startswith(ROOT_PREFIX + "/"))

    def test_members_are_stored_uncompressed(self):
        with zipfile.ZipFile(BUNDLE_PATH) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                with self.subTest(member=info.filename):
                    self.assertEqual(info.compress_type, zipfile.ZIP_STORED)

    def test_no_junk_members(self):
        with zipfile.ZipFile(BUNDLE_PATH) as archive:
            names = [i.filename for i in archive.infolist()]
        junk = [n for n in names
                if "__pycache__" in n
                or n.endswith(EXCLUDED_SUFFIXES)
                or os.path.basename(n) in EXCLUDED_NAMES]
        self.assertFalse(junk, f"bundle contains files that should be excluded: {junk}")

    def test_no_absolute_or_parent_paths(self):
        """A zip member escaping its root would write outside the skill dir."""
        with zipfile.ZipFile(BUNDLE_PATH) as archive:
            for name in (i.filename for i in archive.infolist()):
                with self.subTest(member=name):
                    self.assertFalse(name.startswith("/"))
                    self.assertNotIn("..", name.split("/"))


@skipIf(NO_BUNDLE, SKIP_REASON)
class TestBuildScriptAgrees(TestCase):
    """The repack script and this test must judge freshness identically.

    If they disagree, running the documented fix would not clear the failure.
    """

    def test_build_script_exists(self):
        self.assertTrue(os.path.isfile(
            os.path.join(REPO_ROOT, "scripts", "build_skill_bundle.py")))

    def test_script_and_test_see_the_same_files(self):
        import importlib.util
        script = os.path.join(REPO_ROOT, "scripts", "build_skill_bundle.py")
        spec = importlib.util.spec_from_file_location("build_skill_bundle", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(sorted(module.source_digests()), sorted(_source_digests()))
        self.assertEqual(sorted(module.bundle_digests()), sorted(_bundle_digests()))
