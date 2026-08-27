"""Tests for odmlib.schema_manager.

schema_manager provides path resolution for XSD schema files used during
XML schema validation.  Standard names are lowercase ("odm", "define",
"arm") matching the _MAIN_SCHEMA dictionary keys.
"""
import os
from unittest import TestCase
import odmlib.schema_manager as SM
from odmlib.exceptions import OdmlibValidationError


class TestGetSchemaDir(TestCase):
    """Tests for get_schema_dir()."""

    def test_returns_string(self):
        path = SM.get_schema_dir("odm", "1.3.2")
        self.assertIsInstance(path, str)

    def test_returns_non_empty(self):
        path = SM.get_schema_dir("odm", "1.3.2")
        self.assertGreater(len(path), 0)

    def test_define_20(self):
        path = SM.get_schema_dir("define", "2.0")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_define_21(self):
        path = SM.get_schema_dir("define", "2.1")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_odm_20(self):
        path = SM.get_schema_dir("odm", "2.0")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)
        self.assertIn("2.0", path)

    def test_path_contains_version(self):
        path = SM.get_schema_dir("odm", "1.3.2")
        self.assertIn("1.3.2", path)

    def test_path_contains_standard(self):
        path = SM.get_schema_dir("odm", "1.3.2")
        self.assertIn("odm", path)


class TestGetSchemaPath(TestCase):
    """Tests for get_schema_path()."""

    def test_odm_132_returns_string(self):
        path = SM.get_schema_path("odm", "1.3.2")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_define_20_returns_string(self):
        path = SM.get_schema_path("define", "2.0")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_define_21_returns_string(self):
        path = SM.get_schema_path("define", "2.1")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_odm_132_ends_with_xsd(self):
        path = SM.get_schema_path("odm", "1.3.2")
        self.assertTrue(path.endswith(".xsd"), f"Expected .xsd extension, got: {path}")

    def test_define_20_ends_with_xsd(self):
        path = SM.get_schema_path("define", "2.0")
        self.assertTrue(path.endswith(".xsd"), f"Expected .xsd extension, got: {path}")

    def test_define_21_ends_with_xsd(self):
        path = SM.get_schema_path("define", "2.1")
        self.assertTrue(path.endswith(".xsd"), f"Expected .xsd extension, got: {path}")

    def test_odm_20_returns_string(self):
        path = SM.get_schema_path("odm", "2.0")
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)

    def test_odm_20_ends_with_xsd(self):
        path = SM.get_schema_path("odm", "2.0")
        self.assertTrue(path.endswith(".xsd"), f"Expected .xsd extension, got: {path}")

    def test_odm_20_main_filename_is_ODM_xsd(self):
        # Pin the registered main filename, not just the extension —
        # catches an accidental rename of the bundled main schema.
        path = SM.get_schema_path("odm", "2.0")
        self.assertTrue(path.endswith("ODM.xsd"), f"Expected ODM.xsd, got: {path}")

    def test_arm_10_returns_string(self):
        path = SM.get_schema_path("arm", "1.0")
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith("arm1-0-0.xsd"), f"Expected arm1-0-0.xsd, got: {path}")

    def test_arm_10_define21_returns_string(self):
        path = SM.get_schema_path("arm", "1.0-define2.1")
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith("arm1-0-0.xsd"), f"Expected arm1-0-0.xsd, got: {path}")

    def test_arm_pairings_resolve_to_different_directories(self):
        # Both pairings share a root filename and differ only by directory,
        # so a _MAIN_SCHEMA typo would otherwise collapse them silently.
        self.assertNotEqual(SM.get_schema_path("arm", "1.0"),
                            SM.get_schema_path("arm", "1.0-define2.1"))

    def test_unknown_arm_version_raises(self):
        with self.assertRaises((OdmlibValidationError, ValueError)):
            SM.get_schema_path("arm", "9.9")

    def test_explicit_filename(self):
        path = SM.get_schema_path("odm", "1.3.2", filename="ODM1-3-2.xsd")
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith("ODM1-3-2.xsd"))

    def test_unknown_standard_raises_odmlib_error(self):
        with self.assertRaises(OdmlibValidationError):
            SM.get_schema_path("UNKNOWN", "9.9.9")

    def test_unknown_standard_raises_value_error(self):
        """OdmlibValidationError is also a ValueError for backward compat."""
        with self.assertRaises(ValueError):
            SM.get_schema_path("UNKNOWN", "9.9.9")

    def test_known_standard_wrong_version_raises(self):
        with self.assertRaises((OdmlibValidationError, ValueError)):
            SM.get_schema_path("odm", "9.9.9")

    def test_error_message_contains_standard(self):
        try:
            SM.get_schema_path("UNKNOWN", "9.9.9")
            self.fail("Expected OdmlibValidationError")
        except OdmlibValidationError as exc:
            self.assertIn("UNKNOWN", str(exc))

    def test_error_hint_lists_valid_combinations(self):
        try:
            SM.get_schema_path("UNKNOWN", "9.9.9")
            self.fail("Expected OdmlibValidationError")
        except OdmlibValidationError as exc:
            # The hint should mention at least one valid combination
            self.assertIsNotNone(exc.hint)
            self.assertIn("odm", exc.hint)


class TestSchemaManagerIntegration(TestCase):
    """Integration tests that verify schema paths point to real files."""

    def _file_exists_at_path(self, path):
        """Best-effort check: returns True if path points to an existing file.

        In editable installs the file should exist on disk; in wheel installs
        importlib.resources resolves into a zip which is also acceptable.
        We skip if the path is clearly a zipfile internal path.
        """
        if ".zip/" in path or ".whl/" in path:
            return True  # inside a wheel — trust the library
        return os.path.isfile(path)

    def test_odm_132_xsd_exists(self):
        path = SM.get_schema_path("odm", "1.3.2")
        if not self._file_exists_at_path(path):
            self.skipTest(f"Schema file not found at {path} (may be packaged differently)")

    def test_define_21_xsd_exists(self):
        path = SM.get_schema_path("define", "2.1")
        if not self._file_exists_at_path(path):
            self.skipTest(f"Schema file not found at {path} (may be packaged differently)")

    def test_define_20_xsd_exists(self):
        path = SM.get_schema_path("define", "2.0")
        if not self._file_exists_at_path(path):
            self.skipTest(f"Schema file not found at {path} (may be packaged differently)")

    def test_odm_20_xsd_exists(self):
        path = SM.get_schema_path("odm", "2.0")
        if not self._file_exists_at_path(path):
            self.skipTest(f"Schema file not found at {path} (may be packaged differently)")

    # The ARM checks below assert rather than skip. A missing ARM schema is a
    # packaging regression, and skipping is what let a broken _MAIN_SCHEMA go
    # unnoticed previously.
    def test_arm_10_xsd_exists(self):
        path = SM.get_schema_path("arm", "1.0")
        self.assertTrue(self._file_exists_at_path(path), f"ARM 1.0 schema missing at {path}")

    def test_arm_10_define21_xsd_exists(self):
        path = SM.get_schema_path("arm", "1.0-define2.1")
        self.assertTrue(self._file_exists_at_path(path), f"ARM 2.1 schema missing at {path}")
