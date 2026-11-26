"""``scripts/mypy_baseline.py``: the CI mypy check fails only on new errors.

These tests feed the script synthetic mypy output, so they never run mypy. What
matters most is that a broken or unparseable run can never pass as a clean one:
if the parser silently matched nothing, every new error would slip through.
"""
import collections
import importlib.util
import os
import re
import tempfile
from unittest import TestCase

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "mypy_baseline.py")

_spec = importlib.util.spec_from_file_location("mypy_baseline", SCRIPT)
MB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(MB)

OUTPUT = """\
odmlib/odm_loader.py:378: error: Returning Any from function declared to return "Element[str]"  [no-any-return]
odmlib/odm_loader.py:394: error: Returning Any from function declared to return "Element[str]"  [no-any-return]
odmlib/odm_loader.py:68: error: Signature of "load_document" incompatible with supertype "DocumentLoader"  [override]
odmlib/odm_loader.py:68: note:      Superclass:
odmlib/odm_loader.py:68: note:          def load_document(self, doc: Any) -> Any
odmlib/context.py:132: error: "bool" is invalid as return type for "__exit__" that always returns False  [exit-return]
Found 4 errors in 2 files (checked 49 source files)
"""


class TestParse(TestCase):

    def test_line_numbers_are_dropped_and_notes_ignored(self):
        errors = MB.parse(OUTPUT, 1)
        self.assertEqual(len(errors), 4)
        key, location = errors[2]
        self.assertEqual(key, 'odmlib/odm_loader.py: error: Signature of "load_document" '
                              'incompatible with supertype "DocumentLoader"  [override]')
        self.assertEqual(location, "odmlib/odm_loader.py:68")

    def test_repeated_errors_count_separately(self):
        counts = collections.Counter(key for key, _ in MB.parse(OUTPUT, 1))
        self.assertEqual(counts['odmlib/odm_loader.py: error: Returning Any from function '
                                'declared to return "Element[str]"  [no-any-return]'], 2)

    def test_column_numbers_are_dropped_too(self):
        errors = MB.parse("odmlib/a.py:3:7: error: boom  [misc]\n"
                          "Found 1 error in 1 file (checked 1 source file)\n", 1)
        self.assertEqual(errors, [("odmlib/a.py: error: boom  [misc]", "odmlib/a.py:3")])

    def test_success_means_zero(self):
        self.assertEqual(MB.parse("Success: no issues found in 49 source files\n", 0), [])

    def test_fatal_exit_code_is_rejected(self):
        with self.assertRaises(MB.MypyRunError):
            MB.parse("odmlib/schemas/arm/1.0 contains __init__.py but is not a valid "
                     "Python package name\n", 2)

    def test_missing_summary_is_rejected(self):
        with self.assertRaises(MB.MypyRunError):
            MB.parse("odmlib/a.py:3: error: boom  [misc]\n", 1)

    def test_count_disagreeing_with_summary_is_rejected(self):
        """Guards against a format change that the parser silently stops matching."""
        with self.assertRaises(MB.MypyRunError):
            MB.parse("odmlib/a.py(3): error: boom\nFound 1 error in 1 file\n", 1)

    def test_exit_code_disagreeing_with_summary_is_rejected(self):
        with self.assertRaises(MB.MypyRunError):
            MB.parse("Success: no issues found in 1 source file\n", 1)


class TestCompare(TestCase):

    def test_new_and_stale_are_separated(self):
        new, stale = MB.compare(["a", "a", "b", "c"], ["a", "b", "b", "d"])
        self.assertEqual(new, collections.Counter({"a": 1, "c": 1}))
        self.assertEqual(stale, collections.Counter({"b": 1, "d": 1}))

    def test_identical_sets_have_nothing_new_or_stale(self):
        new, stale = MB.compare(["a", "b"], ["b", "a"])
        self.assertEqual((new, stale), (collections.Counter(), collections.Counter()))


class TestBaselineFile(TestCase):

    LINE = re.compile(r"^odmlib/\S+\.pyi?: error: .+  \[[a-z-]+\]$")

    def test_round_trip_keeps_duplicates(self):
        keys = ["odmlib/b.py: error: x  [misc]", "odmlib/a.py: error: y  [misc]",
                "odmlib/b.py: error: x  [misc]"]
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "baseline.txt")
            MB.write_baseline(path, keys)
            self.assertEqual(MB.read_baseline(path), sorted(keys))

    def test_committed_baseline_is_sorted_and_well_formed(self):
        entries = MB.read_baseline(MB.BASELINE_PATH)
        self.assertGreater(len(entries), 0)
        self.assertEqual(entries, sorted(entries))
        for entry in entries:
            with self.subTest(entry=entry):
                self.assertRegex(entry, self.LINE)
