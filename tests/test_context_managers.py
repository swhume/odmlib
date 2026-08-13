"""Tests for odmlib context managers (odmlib.context).

Covers:
- open_odm(): loading XML and JSON ODM documents.
- open_define(): loading Define-XML documents.
- Auto-save on clean exit.
- No-save when an exception propagates.
- Custom output_file parameter.
- Format auto-detection from file extension.
"""
import json
import os
import shutil
import tempfile
from unittest import TestCase
from odmlib.context import open_odm, open_define, ODMContext, DefineContext


DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
CDASH_XML = os.path.join(DATA_DIR, "cdash-odm-test.xml")
CDASH_JSON = os.path.join(DATA_DIR, "cdash_odm_test.json")
DEFINE_21_XML = os.path.join(DATA_DIR, "defineV21-SDTM.xml")


class TestOpenOdmXML(TestCase):
    """Tests for open_odm() with XML format."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_odm_loads_document(self):
        """open_odm() context manager yields a loaded ODM root object."""
        out_path = os.path.join(self.tmpdir, "out.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            self.assertIsNotNone(odm)
            self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")

    def test_open_odm_writes_on_clean_exit(self):
        """open_odm() saves the document to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "output.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")
        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

    def test_open_odm_no_write_on_exception(self):
        """open_odm() does NOT save if an exception escapes the with block."""
        out_path = os.path.join(self.tmpdir, "should_not_exist.xml")
        with self.assertRaises(ValueError):
            with open_odm(CDASH_XML, output_file=out_path) as odm:
                raise ValueError("intentional test error")
        self.assertFalse(os.path.exists(out_path))

    def test_open_odm_exception_is_propagated(self):
        """open_odm() does not suppress exceptions."""
        with self.assertRaises(RuntimeError):
            with open_odm(CDASH_XML) as odm:
                raise RuntimeError("test error")

    def test_open_odm_modifies_and_saves(self):
        """Changes made inside the with block are persisted to disk."""
        out_path = os.path.join(self.tmpdir, "modified.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            odm.SourceSystem = "TestSystem"
        # Read back and verify the change was saved
        with open_odm(out_path) as odm2:
            self.assertEqual(odm2.SourceSystem, "TestSystem")

    def test_open_odm_auto_detect_xml_format(self):
        """open_odm() detects XML format from .xml file extension."""
        ctx = open_odm(CDASH_XML)
        self.assertEqual(ctx.format, "xml")

    def test_open_odm_in_place_update(self):
        """open_odm() with write_on_exit=True writes back to the input file."""
        in_path = os.path.join(self.tmpdir, "inplace.xml")
        shutil.copy(CDASH_XML, in_path)
        with open_odm(in_path, write_on_exit=True) as odm:
            odm.SourceSystem = "InPlaceTest"
        with open_odm(in_path) as odm2:
            self.assertEqual(odm2.SourceSystem, "InPlaceTest")

    def test_open_odm_default_is_read_only(self):
        """open_odm() with no output_file must NOT modify the input file."""
        in_path = os.path.join(self.tmpdir, "readonly.xml")
        shutil.copy(CDASH_XML, in_path)
        with open(in_path, "rb") as f:
            original = f.read()
        with open_odm(in_path) as odm:
            odm.SourceSystem = "ShouldNotPersist"
        with open(in_path, "rb") as f:
            self.assertEqual(f.read(), original)


class TestOpenOdmJSON(TestCase):
    """Tests for open_odm() with JSON format."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_odm_json_loads_document(self):
        """open_odm() context manager yields a loaded ODM root from JSON."""
        out_path = os.path.join(self.tmpdir, "out.json")
        with open_odm(CDASH_JSON, output_file=out_path) as odm:
            self.assertIsNotNone(odm)
            # Verify it loaded a valid ODM object
            self.assertTrue(hasattr(odm, "FileOID"))

    def test_open_odm_json_auto_detect_format(self):
        """open_odm() detects JSON format from .json file extension."""
        ctx = open_odm(CDASH_JSON)
        self.assertEqual(ctx.format, "json")

    def test_open_odm_json_writes_on_clean_exit(self):
        """open_odm() saves JSON to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "output.json")
        with open_odm(CDASH_JSON, output_file=out_path) as odm:
            pass  # no modifications
        self.assertTrue(os.path.exists(out_path))
        with open(out_path) as fh:
            d = json.load(fh)
        self.assertIn("FileOID", d)

    def test_open_odm_json_no_write_on_exception(self):
        """open_odm() does NOT save JSON if an exception escapes."""
        out_path = os.path.join(self.tmpdir, "should_not_exist.json")
        with self.assertRaises(ValueError):
            with open_odm(CDASH_JSON, output_file=out_path) as odm:
                raise ValueError("test error")
        self.assertFalse(os.path.exists(out_path))


class TestOpenDefine(TestCase):
    """Tests for open_define() context manager."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_open_define_loads_document(self):
        """open_define() loads a Define-XML 2.1 document successfully."""
        out_path = os.path.join(self.tmpdir, "define_out.xml")
        with open_define(DEFINE_21_XML, output_file=out_path) as define:
            self.assertIsNotNone(define)
            self.assertTrue(hasattr(define, "FileOID"))

    def test_open_define_writes_on_clean_exit(self):
        """open_define() saves to output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "define_out.xml")
        with open_define(DEFINE_21_XML, output_file=out_path) as define:
            pass
        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

    def test_open_define_no_write_on_exception(self):
        """open_define() does NOT save if an exception escapes."""
        out_path = os.path.join(self.tmpdir, "no_output.xml")
        with self.assertRaises(RuntimeError):
            with open_define(DEFINE_21_XML, output_file=out_path) as define:
                raise RuntimeError("test error")
        self.assertFalse(os.path.exists(out_path))


class TestWriteOnExit(TestCase):
    """Tests for the ``write_on_exit`` opt-out on the context managers.

    Confirms two halves of the contract:
    - ``write_on_exit=False`` produces no file write on clean exit (no
      side effects on the input even when ``output_file`` defaults to it).
    - The default (``write_on_exit=True``, or no kwarg) still writes,
      preserving the documented in-place save behaviour.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # --- write_on_exit=False : no write ------------------------------------

    def test_open_odm_write_on_exit_false_no_output_file_created(self):
        """open_odm(write_on_exit=False) does not create output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "should_not_be_written.xml")
        with open_odm(CDASH_XML, output_file=out_path, write_on_exit=False) as odm:
            self.assertIsNotNone(odm)
        self.assertFalse(os.path.exists(out_path))

    def test_open_odm_json_write_on_exit_false_no_output_file_created(self):
        """open_odm(write_on_exit=False) does not create the JSON output_file."""
        out_path = os.path.join(self.tmpdir, "should_not_be_written.json")
        with open_odm(CDASH_JSON, output_file=out_path, write_on_exit=False) as odm:
            self.assertIsNotNone(odm)
        self.assertFalse(os.path.exists(out_path))

    def test_open_odm_write_on_exit_false_preserves_input_in_place(self):
        """write_on_exit=False protects the input even when output_file defaults to it.

        Regression guard for the original footgun: a context manager opened
        only to inspect would silently overwrite the input file on exit.
        """
        in_path = os.path.join(self.tmpdir, "inspect_me.xml")
        shutil.copy(CDASH_XML, in_path)
        original_mtime = os.path.getmtime(in_path)
        original_size = os.path.getsize(in_path)
        # No output_file -> would default to in_path; write_on_exit=False
        # must suppress the save entirely.
        with open_odm(in_path, write_on_exit=False) as odm:
            self.assertIsNotNone(odm.FileOID)
        self.assertEqual(os.path.getmtime(in_path), original_mtime)
        self.assertEqual(os.path.getsize(in_path), original_size)

    def test_open_define_write_on_exit_false_no_output_file_created(self):
        """open_define(write_on_exit=False) does not create output_file on clean exit."""
        out_path = os.path.join(self.tmpdir, "should_not_be_written.xml")
        with open_define(DEFINE_21_XML, output_file=out_path,
                         write_on_exit=False) as define:
            self.assertIsNotNone(define)
        self.assertFalse(os.path.exists(out_path))

    # --- default (write_on_exit=True) : still writes -----------------------

    def test_open_odm_default_still_writes(self):
        """Regression guard: omitting write_on_exit preserves the documented save-on-exit default."""
        out_path = os.path.join(self.tmpdir, "default_write.xml")
        with open_odm(CDASH_XML, output_file=out_path) as odm:
            self.assertIsNotNone(odm)
        self.assertTrue(os.path.exists(out_path))
        self.assertGreater(os.path.getsize(out_path), 0)

    def test_open_odm_explicit_true_still_writes(self):
        """write_on_exit=True (explicit) behaves identically to the default."""
        out_path = os.path.join(self.tmpdir, "explicit_true.xml")
        with open_odm(CDASH_XML, output_file=out_path, write_on_exit=True) as odm:
            self.assertIsNotNone(odm)
        self.assertTrue(os.path.exists(out_path))

    def test_open_define_default_still_writes(self):
        """Regression guard for open_define: default still writes."""
        out_path = os.path.join(self.tmpdir, "define_default.xml")
        with open_define(DEFINE_21_XML, output_file=out_path) as define:
            self.assertIsNotNone(define)
        self.assertTrue(os.path.exists(out_path))


class TestContextManagerClasses(TestCase):
    """Unit tests for ODMContext and DefineContext class behaviour."""

    def test_odmcontext_detect_xml(self):
        """ODMContext detects xml format from .xml extension."""
        ctx = ODMContext("file.xml")
        self.assertEqual(ctx.format, "xml")

    def test_odmcontext_detect_json(self):
        """ODMContext detects json format from .json extension."""
        ctx = ODMContext("file.json")
        self.assertEqual(ctx.format, "json")

    def test_odmcontext_explicit_format_overrides(self):
        """Explicit format parameter overrides auto-detection."""
        ctx = ODMContext("file.xml", format="json")
        self.assertEqual(ctx.format, "json")

    def test_odmcontext_output_file_default(self):
        """output_file defaults to input_file when not specified."""
        ctx = ODMContext("study.xml")
        self.assertEqual(ctx.output_file, "study.xml")

    def test_odmcontext_custom_output_file(self):
        """output_file is stored when specified."""
        ctx = ODMContext("study.xml", output_file="out.xml")
        self.assertEqual(ctx.output_file, "out.xml")

    def test_definecontext_default_package(self):
        """DefineContext defaults to define_2_1 model package."""
        ctx = DefineContext("define.xml")
        self.assertEqual(ctx.model_package, "define_2_1")

    def test_odmcontext_default_package(self):
        """ODMContext defaults to odm_1_3_2 model package."""
        ctx = ODMContext("study.xml")
        self.assertEqual(ctx.model_package, "odm_1_3_2")

    def test_open_odm_returns_odmcontext(self):
        """open_odm() returns an ODMContext instance."""
        ctx = open_odm("study.xml")
        self.assertIsInstance(ctx, ODMContext)

    def test_open_define_returns_definecontext(self):
        """open_define() returns a DefineContext instance."""
        ctx = open_define("define.xml")
        self.assertIsInstance(ctx, DefineContext)

    def test_odmcontext_write_on_exit_default_depends_on_output_file(self):
        """Without output_file the default is read-only; with one, writing is on."""
        ctx = ODMContext("study.xml")
        self.assertFalse(ctx._write_on_exit)
        ctx = ODMContext("study.xml", output_file="study_v2.xml")
        self.assertTrue(ctx._write_on_exit)

    def test_odmcontext_write_on_exit_false_stored(self):
        """ODMContext stores write_on_exit=False when explicitly opted out."""
        ctx = ODMContext("study.xml", write_on_exit=False)
        self.assertFalse(ctx._write_on_exit)

    def test_definecontext_write_on_exit_propagated(self):
        """DefineContext passes write_on_exit through to its ODMContext base."""
        ctx = DefineContext("define.xml", write_on_exit=False)
        self.assertFalse(ctx._write_on_exit)
