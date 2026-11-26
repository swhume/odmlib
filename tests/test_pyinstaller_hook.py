"""odmlib ships a PyInstaller hook (P2.7, GitHub issue #37).

A frozen application needs odmlib's data files and the model modules the loaders
import by name, neither of which PyInstaller's analysis finds on its own. The hook is
registered through the ``pyinstaller40`` entry point, so no build flags are needed.

The checks that execute the hook need PyInstaller and are skipped without it. The CI
``pyinstaller`` job installs it, runs this module, and freezes and runs
``tests/pyinstaller/smoke.py``.
"""
import importlib.metadata
import importlib.util
import os
import re
import runpy
import unittest
from unittest import TestCase

import odmlib.schema_manager as SM
from odmlib.__pyinstaller import get_hook_dirs

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRY_POINT = "odmlib.__pyinstaller:get_hook_dirs"
HAS_PYINSTALLER = importlib.util.find_spec("PyInstaller") is not None


class TestHookRegistration(TestCase):

    def test_entry_point_is_declared_in_pyproject(self):
        with open(os.path.join(REPO_ROOT, "pyproject.toml"), encoding="utf-8") as handle:
            text = handle.read()
        section = re.search(r"^\[project\.entry-points\.pyinstaller40\]\n(.*?)(?=^\[|\Z)",
                            text, re.M | re.S)
        self.assertIsNotNone(section, "no [project.entry-points.pyinstaller40] table")
        self.assertRegex(section.group(1), r'^hook-dirs\s*=\s*"%s"' % re.escape(ENTRY_POINT))

    def test_entry_point_is_registered_in_the_installed_metadata(self):
        points = [e for e in importlib.metadata.entry_points(group="pyinstaller40")
                  if e.value == ENTRY_POINT]
        if not points:
            self.skipTest("installed odmlib metadata predates the hook; "
                          "run pip install -e . to refresh its entry points")
        self.assertEqual(points[0].name, "hook-dirs")
        self.assertEqual(points[0].load()(), get_hook_dirs())

    def test_hook_directory_contains_the_hook(self):
        dirs = get_hook_dirs()
        self.assertEqual(len(dirs), 1)
        self.assertTrue(os.path.isfile(os.path.join(dirs[0], "hook-odmlib.py")))

    def test_importing_the_package_does_not_need_pyinstaller(self):
        import odmlib.__pyinstaller as hook_package
        self.assertNotIn("PyInstaller", vars(hook_package))


@unittest.skipUnless(HAS_PYINSTALLER, "PyInstaller is not installed")
class TestHookContents(TestCase):
    """What the hook hands PyInstaller (it imports PyInstaller, so run it only with it)."""

    @classmethod
    def setUpClass(cls):
        hook = runpy.run_path(os.path.join(get_hook_dirs()[0], "hook-odmlib.py"))
        cls.datas = hook["datas"]
        cls.hiddenimports = hook["hiddenimports"]
        cls.sources = {os.path.normcase(os.path.abspath(src)) for src, _ in cls.datas}

    def test_valuesets_are_collected(self):
        self.assertTrue(any(src.endswith("valuesets.json") for src in self.sources))

    def test_every_registered_schema_and_its_includes_are_collected(self):
        for (standard, version) in sorted(SM._MAIN_SCHEMA):
            schema_dir = SM.get_schema_dir(standard, version)
            for name in sorted(os.listdir(schema_dir)):
                if name.endswith(".xsd"):
                    with self.subTest(schema=f"{standard}/{version}/{name}"):
                        path = os.path.normcase(os.path.abspath(os.path.join(schema_dir, name)))
                        self.assertIn(path, self.sources)

    def test_every_model_module_is_a_hidden_import(self):
        import pkgutil
        import odmlib
        models = sorted(m.name for m in pkgutil.walk_packages(odmlib.__path__, "odmlib.")
                        if m.name.endswith(".model"))
        self.assertGreaterEqual(len(models), 8)
        for name in models:
            with self.subTest(module=name):
                self.assertIn(name, self.hiddenimports)

    def test_data_packages_and_the_hook_are_not_imported(self):
        self.assertFalse([n for n in self.hiddenimports
                          if n.startswith(("odmlib.schemas", "odmlib.__pyinstaller"))])
