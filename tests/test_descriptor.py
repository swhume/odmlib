import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.typed as T
import odmlib.odm_element as OE


class TestText(OE.ODMElement):
    Name = T.String(required=True)
    OrderNumber = T.PositiveInteger(required=False)


class TestDescriptor(unittest.TestCase):

    def test_assignment(self):
        test = TestText(Name="test name", OrderNumber="1")
        self.assertEqual(test.Name, "test name")
        with self.assertRaises(TypeError):
            test.OID = None
        TestText.Name = "VariableOne"
        self.assertEqual(TestText.Name, "VariableOne")

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
        with self.assertRaises(TypeError):
            itd.new_thing = "hello"

