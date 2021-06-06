import unittest
import model_extended as ODM


class TestExtendedAlias(unittest.TestCase):
    def test_valid_standard_attribute(self):
        ODM.Alias = ODM.Alias(Context="CDASH", Name="AEYN", Standard="CDASHIG")
        self.assertEqual(ODM.Alias.Standard, "CDASHIG")

    def test_invalid_standard_attribute(self):
        with self.assertRaises(TypeError):
            ODM.Alias = ODM.Alias(Context="CDASH", Name="AEYN", Standard="HL7 FHIR")


if __name__ == '__main__':
    unittest.main()
