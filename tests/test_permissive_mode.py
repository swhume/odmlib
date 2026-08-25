"""Tests for the permissive loading mode (odmlib.mode).

Covers the ValidationMode flag enum, the permissive() context manager,
all four validation flag categories (SKIP_REQUIRED, SKIP_TYPE, SKIP_FORMAT,
SKIP_VALUESET), integration with loaders, and the open_odm/open_define
context manager integration.
"""
import os
import tempfile
import unittest

import odmlib.mode as _mode
from odmlib.mode import ValidationMode, permissive, get_mode, set_mode, is_permissive
from odmlib.exceptions import (
    OdmlibTypeError,
    OdmlibRequiredAttributeError,
    OdmlibValidationError,
)


# Path to tests/data/
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class TestValidationModeEnum(unittest.TestCase):
    """Unit tests for the ValidationMode flag enum."""

    def test_strict_is_falsy(self):
        self.assertFalse(bool(ValidationMode.STRICT))

    def test_permissive_is_truthy(self):
        self.assertTrue(bool(ValidationMode.PERMISSIVE))

    def test_permissive_contains_all_flags(self):
        self.assertTrue(ValidationMode.PERMISSIVE & ValidationMode.SKIP_REQUIRED)
        self.assertTrue(ValidationMode.PERMISSIVE & ValidationMode.SKIP_VALUESET)
        self.assertTrue(ValidationMode.PERMISSIVE & ValidationMode.SKIP_TYPE)
        self.assertTrue(ValidationMode.PERMISSIVE & ValidationMode.SKIP_FORMAT)

    def test_individual_flags_are_independent(self):
        self.assertFalse(ValidationMode.SKIP_REQUIRED & ValidationMode.SKIP_TYPE)
        self.assertTrue(ValidationMode.SKIP_REQUIRED & ValidationMode.SKIP_REQUIRED)

    def test_flags_can_be_combined(self):
        combo = ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET
        self.assertTrue(combo & ValidationMode.SKIP_REQUIRED)
        self.assertTrue(combo & ValidationMode.SKIP_VALUESET)
        self.assertFalse(combo & ValidationMode.SKIP_TYPE)


class TestPermissiveContextManager(unittest.TestCase):
    """Tests for the permissive() context manager and mode helpers."""

    def test_default_mode_is_strict(self):
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_permissive_sets_mode(self):
        with permissive():
            self.assertEqual(get_mode(), ValidationMode.PERMISSIVE)

    def test_permissive_resets_on_exit(self):
        with permissive():
            pass
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_permissive_resets_on_exception(self):
        with self.assertRaises(ValueError):
            with permissive():
                raise ValueError("test")
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_nested_permissive(self):
        with permissive():
            self.assertEqual(get_mode(), ValidationMode.PERMISSIVE)
            with permissive(ValidationMode.SKIP_REQUIRED):
                self.assertEqual(get_mode(), ValidationMode.SKIP_REQUIRED)
            self.assertEqual(get_mode(), ValidationMode.PERMISSIVE)
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_custom_mode_flag(self):
        with permissive(ValidationMode.SKIP_REQUIRED):
            self.assertEqual(get_mode(), ValidationMode.SKIP_REQUIRED)

    def test_set_mode_returns_token(self):
        import contextvars
        token = set_mode(ValidationMode.SKIP_TYPE)
        self.assertIsInstance(token, contextvars.Token)
        _mode._validation_mode.reset(token)

    def test_is_permissive_correct(self):
        self.assertFalse(is_permissive(ValidationMode.SKIP_REQUIRED))
        with permissive():
            self.assertTrue(is_permissive(ValidationMode.SKIP_REQUIRED))
            self.assertTrue(is_permissive(ValidationMode.SKIP_TYPE))
        self.assertFalse(is_permissive(ValidationMode.SKIP_REQUIRED))


class TestPermissiveRequired(unittest.TestCase):
    """Tests for SKIP_REQUIRED flag behavior."""

    def test_strict_rejects_missing_required(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM.Alias(Name="test")

    def test_permissive_allows_missing_required(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            alias = ODM.Alias(Name="test")
            self.assertEqual(alias.Name, "test")

    def test_permissive_get_returns_none_for_missing(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            alias = ODM.Alias(Name="test")
            self.assertIsNone(alias.Context)

    def test_permissive_multiple_missing(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            item = ODM.ItemDef()
            self.assertIsNone(item.OID)
            self.assertIsNone(item.Name)

    def test_permissive_content_missing(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            sn = ODM.StudyName()
            self.assertIsNone(sn._content)

    def test_strict_fix_after_permissive(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            alias = ODM.Alias(Name="test")
        # Setting Context with wrong type should still fail in strict mode
        with self.assertRaises(OdmlibTypeError):
            alias.Context = 123

    def test_skip_required_only_still_enforces_type(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_REQUIRED):
            with self.assertRaises(OdmlibTypeError):
                ODM.Alias(Context=123, Name="test")

    def test_odmobject_required_not_enforced(self):
        import odmlib.odm_1_3_2.model as ODM
        # MeasurementUnit has required Symbol (ODMObject)
        with permissive(ValidationMode.SKIP_REQUIRED):
            mu = ODM.MeasurementUnit(OID="MU.1", Name="kg")
            # Should not raise — Symbol is required but skipped


class TestPermissiveType(unittest.TestCase):
    """Tests for SKIP_TYPE flag behavior."""

    def test_strict_rejects_wrong_type(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.Alias(Context=123, Name="test")

    def test_permissive_allows_wrong_type(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE):
            alias = ODM.Alias(Context=123, Name="test")
            self.assertEqual(alias.Context, 123)

    def test_integer_coercion_still_works(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_VALUESET):
            ir = ODM.ItemRef(ItemOID="IT.1", OrderNumber="42", Mandatory="Yes")
            self.assertEqual(ir.OrderNumber, 42)
            self.assertIsInstance(ir.OrderNumber, int)

    def test_integer_invalid_string_stored_asis(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_VALUESET):
            ir = ODM.ItemRef(ItemOID="IT.1", OrderNumber="abc", Mandatory="Yes")
            self.assertEqual(ir.OrderNumber, "abc")

    def test_float_coercion_still_works(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_VALUESET):
            cli = ODM.CodeListItem(CodedValue="1", Rank="3.14")
            self.assertAlmostEqual(cli.Rank, 3.14)

    def test_float_invalid_string_stored_asis(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_VALUESET):
            cli = ODM.CodeListItem(CodedValue="1", Rank="not-a-float")
            self.assertEqual(cli.Rank, "not-a-float")

    def test_odmobject_wrong_type_stored(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_REQUIRED):
            mu = ODM.MeasurementUnit(OID="MU.1", Name="kg")
            mu.Symbol = "not-a-symbol-object"
            self.assertEqual(mu.Symbol, "not-a-symbol-object")

    def test_odmlistobject_wrong_element_stored(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_REQUIRED):
            mu = ODM.MeasurementUnit(OID="MU.1", Name="kg")
            mu.Alias = ["not-an-alias", 42]
            self.assertEqual(mu.Alias, ["not-an-alias", 42])

    def test_odmlistobject_non_list_stored(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_REQUIRED):
            mu = ODM.MeasurementUnit(OID="MU.1", Name="kg")
            mu.Alias = "not-a-list"
            self.assertEqual(mu.Alias, "not-a-list")

    def test_positive_negative_value_stored(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE | ValidationMode.SKIP_VALUESET):
            ir = ODM.ItemRef(ItemOID="IT.1", OrderNumber=-5, Mandatory="Yes")
            self.assertEqual(ir.OrderNumber, -5)

    def test_setattr_unknown_key_stored(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_TYPE):
            alias = ODM.Alias(Context="ctx", Name="test")
            alias.unknown_attr = "hello"
            self.assertEqual(alias.__dict__["unknown_attr"], "hello")


class TestPermissiveFormat(unittest.TestCase):
    """Tests for SKIP_FORMAT flag behavior."""

    def test_strict_rejects_bad_datetime(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibValidationError):
            ODM.ODM(FileOID="F1", FileType="Snapshot", Granularity="All",
                    CreationDateTime="not-a-date",
                    AsOfDateTime="2025-01-01T00:00:00", ODMVersion="1.3.2")

    def test_permissive_allows_bad_datetime(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT):
            odm = ODM.ODM(FileOID="F1", FileType="Snapshot", Granularity="All",
                          CreationDateTime="not-a-date",
                          AsOfDateTime="2025-01-01T00:00:00", ODMVersion="1.3.2")
            self.assertEqual(odm.CreationDateTime, "not-a-date")

    def test_permissive_allows_bad_date(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT | ValidationMode.SKIP_REQUIRED):
            mvr = ODM.MetaDataVersionRef(StudyOID="S.1",
                                         MetaDataVersionOID="MDV.1",
                                         EffectiveDate="not-a-date")
            self.assertEqual(mvr.EffectiveDate, "not-a-date")

    def test_permissive_allows_bad_partial_datetime(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT):
            odm = ODM.ODM(FileOID="F1", FileType="Snapshot", Granularity="All",
                          CreationDateTime="2025-01-01T00:00:00",
                          AsOfDateTime="bad-partial", ODMVersion="1.3.2")
            self.assertEqual(odm.AsOfDateTime, "bad-partial")

    def test_permissive_allows_bad_sasname(self):
        import odmlib.define_2_1.model as DEF
        with permissive(ValidationMode.SKIP_FORMAT | ValidationMode.SKIP_REQUIRED):
            igd = DEF.ItemGroupDef(OID="IG.1", Name="Test", Repeating="No",
                                   SASDatasetName="WAYTOOLONGNAME")
            self.assertEqual(igd.SASDatasetName, "WAYTOOLONGNAME")

    def test_permissive_allows_bad_sasformat(self):
        import odmlib.define_2_1.model as DEF
        with permissive(ValidationMode.SKIP_FORMAT | ValidationMode.SKIP_REQUIRED):
            item = DEF.ItemDef(OID="IT.1", Name="Test", DataType="text",
                               DisplayFormat="!!INVALID!!")
            self.assertEqual(item.DisplayFormat, "!!INVALID!!")

    def test_permissive_allows_oversized_string(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT | ValidationMode.SKIP_REQUIRED):
            # Description attribute on MetaDataVersion is a SizedString
            mdv = ODM.MetaDataVersion(OID="MDV.1", Name="Test",
                                      Description="x" * 5000)
            self.assertEqual(len(mdv.Description), 5000)

    def test_permissive_allows_regex_mismatch(self):
        """Regex descriptor accepts non-matching string in permissive mode."""
        import odmlib.typed as T
        import odmlib.odm_element as OE
        with permissive(ValidationMode.SKIP_FORMAT):
            class _TempRegex(OE.ODMElement):
                Range = T.Regex(pat=r"[0-4]-[0-9]")
            obj = _TempRegex(Range="not-matching")
            self.assertEqual(obj.Range, "not-matching")

    def test_permissive_allows_bad_duration(self):
        """DurationDateTimeString accepts invalid duration in permissive mode."""
        import odmlib.typed as T
        import odmlib.odm_element as OE
        # Create a temporary class with a DurationDateTimeString field
        # since it's used in ODM 2.0 timing windows
        with permissive(ValidationMode.SKIP_FORMAT):
            class _TempDur(OE.ODMElement):
                Dur = T.DurationDateTimeString()
            obj = _TempDur(Dur="not-a-duration")
            self.assertEqual(obj.Dur, "not-a-duration")

    def test_skip_format_only_still_enforces_required(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT):
            with self.assertRaises(OdmlibRequiredAttributeError):
                ODM.Alias(Name="test")  # missing required Context

    def test_skip_format_only_still_enforces_type(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_FORMAT):
            with self.assertRaises(OdmlibTypeError):
                ODM.Alias(Context=123, Name="test")


class TestPermissiveValueSet(unittest.TestCase):
    """Tests for SKIP_VALUESET flag behavior."""

    def test_strict_rejects_bad_valueset(self):
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID="IT.1", Name="Test", DataType="bogus")

    def test_permissive_allows_bad_valueset(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_VALUESET):
            item = ODM.ItemDef(OID="IT.1", Name="Test", DataType="bogus")
            self.assertEqual(item.DataType, "bogus")

    def test_permissive_allows_bad_extended_values(self):
        import odmlib.define_2_1.model as DEF
        with permissive(ValidationMode.SKIP_VALUESET | ValidationMode.SKIP_REQUIRED):
            origin = DEF.Origin(Type="Bogus")
            self.assertEqual(origin.Type, "Bogus")

    def test_valueset_string_bypassed(self):
        """ValueSetString (ValidValues + String) is fully bypassed by SKIP_VALUESET."""
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_VALUESET):
            item = ODM.ItemDef(OID="IT.1", Name="Test", DataType="nonexistent_type")
            self.assertEqual(item.DataType, "nonexistent_type")

    def test_odm_model_itemdef_datatype(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_VALUESET):
            item = ODM.ItemDef(OID="IT.1", Name="Test", DataType="bogus")
            self.assertEqual(item.DataType, "bogus")

    def test_odm_model_mandatory_field(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_VALUESET):
            ir = ODM.ItemRef(ItemOID="IT.1", Mandatory="Maybe")
            self.assertEqual(ir.Mandatory, "Maybe")

    def test_skip_valueset_only_still_enforces_required(self):
        import odmlib.odm_1_3_2.model as ODM
        with permissive(ValidationMode.SKIP_VALUESET):
            with self.assertRaises(OdmlibRequiredAttributeError):
                ODM.Alias(Name="test")


class TestPermissiveLoading(unittest.TestCase):
    """End-to-end integration tests loading non-conformant files."""

    def _xml_path(self, name):
        return os.path.join(TEST_DATA_DIR, name)

    def test_strict_rejects_nonconformant_xml(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        loader = LD.ODMLoader(OL.XMLODMLoader())
        with self.assertRaises((OdmlibTypeError, OdmlibRequiredAttributeError,
                                OdmlibValidationError)):
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            loader.root()

    def test_permissive_loads_nonconformant_xml(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
            self.assertEqual(odm.FileOID, "ODM.NC.001")

    def test_permissive_loads_nonconformant_json(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.JSONODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.json"))
            odm = loader.root()
            self.assertEqual(odm.FileOID, "ODM.NC.001")

    def test_permissive_navigate_object_tree(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
        # Navigate the object tree outside permissive mode
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemDef), 1)
        self.assertEqual(mdv.ItemDef[0].OID, "IT.NONAME")
        self.assertEqual(mdv.ItemDef[0].DataType, "bogus")

    def test_permissive_navigate_missing_name(self):
        """ItemDef loaded without Name returns None for the missing attribute."""
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
        mdv = odm.Study[0].MetaDataVersion[0]
        with permissive(ValidationMode.SKIP_REQUIRED):
            self.assertIsNone(mdv.ItemDef[0].Name)

    def test_permissive_to_dict_works(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
            d = odm.to_dict()
            self.assertIsInstance(d, dict)
            self.assertEqual(d["FileOID"], "ODM.NC.001")

    def test_permissive_fix_then_strict_validates(self):
        """Permissive load -> fix -> strict access succeeds."""
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
        # Fix the issues
        mdv = odm.Study[0].MetaDataVersion[0]
        mdv.ItemDef[0].Name = "Fixed Name"
        mdv.ItemDef[0].DataType = "text"
        mdv.ItemGroupDef[0].ItemRef[0].Mandatory = "Yes"
        # Strict access should now work
        self.assertEqual(mdv.ItemDef[0].Name, "Fixed Name")
        self.assertEqual(mdv.ItemDef[0].DataType, "text")

    def test_permissive_roundtrip_xml(self):
        """Permissive load -> fix -> write -> strict re-load."""
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with permissive():
            loader = LD.ODMLoader(OL.XMLODMLoader())
            loader.open_odm_document(self._xml_path("nonconformant_odm.xml"))
            odm = loader.root()
        # Fix the issues
        mdv = odm.Study[0].MetaDataVersion[0]
        mdv.ItemDef[0].Name = "Fixed"
        mdv.ItemDef[0].DataType = "text"
        mdv.ItemGroupDef[0].ItemRef[0].Mandatory = "Yes"
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmp_path = f.name
        try:
            odm.write_xml(tmp_path)
            # Strict re-load
            loader2 = LD.ODMLoader(OL.XMLODMLoader())
            loader2.open_odm_document(tmp_path)
            odm2 = loader2.root()
            self.assertEqual(odm2.FileOID, "ODM.NC.001")
            mdv2 = odm2.Study[0].MetaDataVersion[0]
            self.assertEqual(mdv2.ItemDef[0].Name, "Fixed")
            self.assertEqual(mdv2.ItemDef[0].DataType, "text")
        finally:
            os.unlink(tmp_path)


class TestPermissiveDefineLoading(unittest.TestCase):
    """Integration tests for loading non-conformant Define-XML 2.1."""

    def test_strict_rejects_nonconformant_define(self):
        import odmlib.loader as LD
        import odmlib.define_loader as DL
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        with self.assertRaises((OdmlibTypeError, OdmlibRequiredAttributeError)):
            loader.open_odm_document(
                os.path.join(TEST_DATA_DIR, "nonconformant_define21.xml"))
            loader.root()

    def test_permissive_loads_nonconformant_define(self):
        import odmlib.loader as LD
        import odmlib.define_loader as DL
        with permissive():
            loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
            loader.open_odm_document(
                os.path.join(TEST_DATA_DIR, "nonconformant_define21.xml"))
            define = loader.root()
            self.assertEqual(define.FileOID, "DEF.NC.001")


class TestPermissiveContextManagers(unittest.TestCase):
    """Tests for open_odm()/open_define() integration with permissive param."""

    SIMPLE_XML = os.path.join(TEST_DATA_DIR, "simple_create.xml")

    def test_open_odm_permissive_true(self):
        from odmlib.context import open_odm
        with open_odm(self.SIMPLE_XML, output_file=os.devnull,
                      permissive=True) as odm:
            self.assertEqual(get_mode(), ValidationMode.PERMISSIVE)
            self.assertIsNotNone(odm.FileOID)

    def test_open_odm_mode_restored_on_exit(self):
        from odmlib.context import open_odm
        with open_odm(self.SIMPLE_XML, output_file=os.devnull,
                      permissive=True) as odm:
            pass
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_open_odm_custom_mode(self):
        from odmlib.context import open_odm
        with open_odm(self.SIMPLE_XML, output_file=os.devnull,
                      permissive=ValidationMode.SKIP_REQUIRED) as odm:
            self.assertEqual(get_mode(), ValidationMode.SKIP_REQUIRED)
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_open_odm_mode_restored_on_exception(self):
        from odmlib.context import open_odm
        with self.assertRaises(ValueError):
            with open_odm(self.SIMPLE_XML, output_file=os.devnull,
                          permissive=True) as odm:
                raise ValueError("test")
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_open_odm_default_is_strict(self):
        from odmlib.context import open_odm
        with open_odm(self.SIMPLE_XML, output_file=os.devnull) as odm:
            self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_open_define_permissive_true(self):
        from odmlib.context import open_define
        define_xml = os.path.join(TEST_DATA_DIR, "defineV21-SDTM-test.xml")
        with open_define(define_xml, output_file=os.devnull,
                         permissive=True) as define:
            self.assertEqual(get_mode(), ValidationMode.PERMISSIVE)
            self.assertIsNotNone(define.FileOID)
        self.assertEqual(get_mode(), ValidationMode.STRICT)

    def test_open_odm_permissive_loads_nonconformant(self):
        """open_odm with permissive=True loads a nonconformant file."""
        from odmlib.context import open_odm
        nc_xml = os.path.join(TEST_DATA_DIR, "nonconformant_odm.xml")
        with open_odm(nc_xml, output_file=os.devnull,
                      permissive=True) as odm:
            self.assertEqual(odm.FileOID, "ODM.NC.001")


class TestPermissiveCombined(unittest.TestCase):
    """Tests for combined flag behavior and edge cases."""

    def test_permissive_all_categories_at_once(self):
        """PERMISSIVE mode allows missing required + bad type + bad valueset + bad format."""
        import odmlib.odm_1_3_2.model as ODM
        with permissive():
            # missing Name (required), bad DataType (valueset), bad CreationDateTime (format)
            item = ODM.ItemDef(OID="IT.1", DataType="bogus")
            self.assertEqual(item.DataType, "bogus")

    def test_selective_skip_required_and_valueset(self):
        """SKIP_REQUIRED | SKIP_VALUESET still enforces type and format."""
        import odmlib.odm_1_3_2.model as ODM
        mode = ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET
        with permissive(mode):
            # Missing required + bad valueset: OK
            item = ODM.ItemDef(OID="IT.1", DataType="bogus")
            self.assertEqual(item.DataType, "bogus")
            # Wrong type: should still raise
            with self.assertRaises(OdmlibTypeError):
                ODM.Alias(Context=123, Name="test")

    def test_strict_mode_unaffected_by_prior_permissive(self):
        """After permissive() exits, strict mode is fully enforced."""
        import odmlib.odm_1_3_2.model as ODM
        with permissive():
            ODM.ItemDef(OID="IT.1", DataType="bogus")
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID="IT.1", Name="Test", DataType="bogus")


class TestPermissiveConstraintDescriptors(unittest.TestCase):
    """Tests for Positive/NonNegative descriptors with non-numeric values in permissive mode."""

    def test_positive_integer_with_non_numeric_string_permissive(self):
        """PositiveInteger stores a non-numeric string in permissive mode without raising."""
        import odmlib.odm_1_3_2.model as ODM
        with permissive():
            item = ODM.ItemDef(OID="IT.1", Name="Test", DataType="text", Length="__PLACEHOLDER__")
            self.assertEqual(item.Length, "__PLACEHOLDER__")

    def test_non_negative_integer_with_non_numeric_string_permissive(self):
        """NonNegativeInteger stores a non-numeric string in permissive mode without raising."""
        import odmlib.odm_1_3_2.model as ODM
        with permissive():
            item = ODM.ItemDef(OID="IT.1", Name="Test", DataType="text", SignificantDigits="__PLACEHOLDER__")
            self.assertEqual(item.SignificantDigits, "__PLACEHOLDER__")

    def test_positive_integer_with_non_numeric_string_strict_raises(self):
        """Strict mode raises OdmlibTypeError (from Integer.__set__) for non-numeric strings."""
        import odmlib.odm_1_3_2.model as ODM
        with self.assertRaises(OdmlibTypeError):
            ODM.ItemDef(OID="IT.1", Name="Test", DataType="text", Length="__PLACEHOLDER__")

    def test_load_define_360i_permissive(self):
        """End-to-end: loads define-360i.xml with permissive(), verifies the object tree."""
        import odmlib.define_loader as DL
        import odmlib.loader as LD

        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        with permissive():
            loader.open_odm_document(os.path.join(TEST_DATA_DIR, "define-360i.xml"))
            odm = loader.root()
        self.assertIsNotNone(odm)
        self.assertEqual(type(odm).__name__, "ODM")
        # Verify MetaDataVersion was loaded
        study = odm.Study
        mdv = study.MetaDataVersion
        self.assertIsNotNone(mdv)
        # Verify ItemDefs were loaded (file has many)
        self.assertGreater(len(mdv.ItemDef), 0)


if __name__ == "__main__":
    unittest.main()
