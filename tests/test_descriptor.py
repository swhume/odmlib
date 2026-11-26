import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.typed as T
import odmlib.odm_element as OE
import odmlib.mode as mode
from odmlib.exceptions import OdmlibRequiredAttributeError, OdmlibTypeError


class TextModel(OE.ODMElement):
    Name = T.String(required=True)
    OrderNumber = T.PositiveInteger(required=False)


class TestDescriptor(unittest.TestCase):

    def test_assignment(self):
        test = TextModel(Name="test name", OrderNumber="1")
        self.assertEqual(test.Name, "test name")
        with self.assertRaises(OdmlibTypeError):
            test.OID = None
        TextModel.Name = "VariableOne"
        self.assertEqual(TextModel.Name, "VariableOne")

    def test_get_missing_attribute(self):
        igd = ODM.ItemGroupDef(OID="IG.VS", Name="Vital Signs", Repeating="Yes")
        self.assertEqual(igd.OID, "IG.VS")
        self.assertIsNone(igd.Comment)

    def test_get_missing_element_with_required(self):
        itd = ODM.ItemDef(OID="IT.VS.VSORRES", Name="Vital Signs Results", DataType="text")
        self.assertEqual(itd.OID, "IT.VS.VSORRES")
        self.assertIsNone(itd.CodeListRef)

    def test_get_missing_undefined_attribute(self):
        itd = ODM.ItemDef(OID="IT.VS.VSORRES", Name="Vital Signs Results", DataType="text")
        self.assertEqual(itd.OID, "IT.VS.VSORRES")
        self.assertListEqual(itd.MeasurementUnitRef, [])
        result = itd.CodeListRef
        self.assertIsNone(result)
        itd.Alias.append(itd.CodeListRef)
        self.assertListEqual(itd.Alias, [None])
        with self.assertRaises(OdmlibTypeError):
            itd.new_thing = "hello"

    def test_required_attr_get_raises(self):
        """Accessing an unset required attribute raises OdmlibRequiredAttributeError."""
        # Use a fresh model class to avoid descriptor pollution from other tests
        class _ReqModel(OE.ODMElement):
            ReqAttr = T.String(required=True)
            OptAttr = T.String(required=False)

        with mode.permissive(mode.ValidationMode.SKIP_REQUIRED):
            obj = _ReqModel()
        # In strict mode, accessing unset required attr should raise
        with self.assertRaises(OdmlibRequiredAttributeError):
            _ = obj.ReqAttr

    def test_required_attr_get_permissive_returns_none(self):
        """In permissive mode, accessing an unset required attribute returns None."""
        class _ReqModel2(OE.ODMElement):
            ReqAttr = T.String(required=True)

        with mode.permissive(mode.ValidationMode.SKIP_REQUIRED):
            obj = _ReqModel2()
            self.assertIsNone(obj.ReqAttr)

    def test_optional_attr_get_default(self):
        """Accessing an unset optional attribute returns the auto-initialized default."""
        obj = TextModel(Name="test")
        self.assertIsNone(obj.OrderNumber)

    def test_optional_list_attr_get_default(self):
        """Accessing an unset optional list attribute auto-initializes to []."""
        itd = ODM.ItemDef(OID="IT.TEST", Name="Test", DataType="text")
        self.assertListEqual(itd.Alias, [])

    def test_optional_element_attr_get_default(self):
        """Accessing an unset optional element attribute returns None (element_class() raises)."""
        itd = ODM.ItemDef(OID="IT.TEST", Name="Test", DataType="text")
        # CodeListRef is an optional ODMObject; accessing it auto-initializes
        self.assertIsNone(itd.CodeListRef)

