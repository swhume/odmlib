from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestEnumeratedItem(TestCase):
    def setUp(self) -> None:
        attrs = self._set_attributes()
        self.eni = ODM.EnumeratedItem(**attrs)

    def test_add_alias(self):
        self.eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        self.assertEqual(self.eni.Alias[0].Context, "nci:ExtCodeID")
        self.assertEqual(self.eni.Alias[0].Name, "C64848")

    def test_to_json(self):
        attrs = self._set_attributes()
        eni = ODM.EnumeratedItem(**attrs)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        eni_json = eni.to_json()
        eni_dict = json.loads(eni_json)
        self.assertEqual(eni_dict["CodedValue"], "HGB")
        self.assertDictEqual(eni_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self._set_attributes()
        eni = ODM.EnumeratedItem(**attrs)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        eni_dict = eni.to_dict()
        self.assertEqual(eni_dict["CodedValue"], "HGB")
        self.assertDictEqual(eni_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self._set_attributes()
        eni = ODM.EnumeratedItem(**attrs)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        eni_xml = eni.to_xml()
        self.assertEqual(eni_xml.attrib["CodedValue"], "HGB")
        alias_elem = eni_xml.find("Alias")
        self.assertEqual(alias_elem.attrib["Name"], "C64848")

    @staticmethod
    def _set_attributes():
        """
        set some EnumeratedItem element attributes using test data
        :return: (dict) dictionary with EnumeratedItem attribute information
        """
        return {"CodedValue": "HGB", "OrderNumber": 1}

    @staticmethod
    def expected_dict():
        return {'CodedValue': 'HGB', 'OrderNumber': 1, 'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64848'}]}
