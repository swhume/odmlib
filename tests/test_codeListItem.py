from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestCodeListItem(TestCase):
    def setUp(self) -> None:
        attrs = self._set_attributes()
        self.cli = ODM.CodeListItem(**attrs)

    def test_add_decode(self):
        tt1 = ODM.TranslatedText(_content="Hemoglobin", lang="en")
        decode = ODM.Decode()
        decode.TranslatedText.append(tt1)
        self.cli.Decode = decode
        self.assertEqual(len(self.cli.Decode.TranslatedText), 1)
        self.assertEqual(self.cli.Decode.TranslatedText[0]._content, 'Hemoglobin')

    def test_add_alias(self):
        self.cli.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        self.assertEqual(self.cli.Alias[0].Name, "C64848")

    def test_missing_attribute(self):
        # missing coded value
        attrs1 = {"OrderNumber": 1}
        with self.assertRaises(ValueError):
            cli = ODM.CodeListItem(**attrs1)
        attrs2 = {"CodedValue": "HGB", "OrderNumber": 1}
        cli = ODM.CodeListItem(**attrs2)
        self.assertEqual(cli.CodedValue, "HGB")
        attrs3 = {"DeCodedValue": "HGB", "OrderNumber": 1}
        # invalid attribute
        with self.assertRaises(TypeError):
            cli = ODM.CodeListItem(**attrs3)

    def test_missing_element(self):
        attrs = {"CodedValue": "HGB", "OrderNumber": 1}
        cli = ODM.CodeListItem(**attrs)
        decode = ODM.Decode()
        # this works because TT is set to an empty list - this model violation will be caught with conformance test
        decode.TranslatedText.append(None)
        cli.Decode = decode
        self.assertEqual(len(cli.Decode.TranslatedText), 1)
        # test translating missing element into dict
        with self.assertRaises(AttributeError):
            cli_dict = cli.to_dict()
        with self.assertRaises(AttributeError):
            cli_xml = cli.to_xml()

    def test_to_json(self):
        attrs = self._set_attributes()
        cli = ODM.CodeListItem(**attrs)
        tt1 = ODM.TranslatedText(_content="Hemoglobin", lang="en")
        decode = ODM.Decode()
        decode.TranslatedText.append(tt1)
        cli.Decode = decode
        cli.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        cli_json = cli.to_json()
        cli_dict = json.loads(cli_json)
        print(cli_dict)
        self.assertEqual(cli_dict["CodedValue"], "HGB")
        self.assertDictEqual(cli_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self._set_attributes()
        cli = ODM.CodeListItem(**attrs)
        tt1 = ODM.TranslatedText(_content="Hemoglobin", lang="en")
        decode = ODM.Decode()
        decode.TranslatedText.append(tt1)
        cli.Decode = decode
        cli.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        cli_dict = cli.to_dict()
        print(cli_dict)
        self.assertDictEqual(cli_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self._set_attributes()
        cli = ODM.CodeListItem(**attrs)
        tt1 = ODM.TranslatedText(_content="Hemoglobin", lang="en")
        decode = ODM.Decode()
        decode.TranslatedText.append(tt1)
        cli.Decode = decode
        cli.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        cli_xml = cli.to_xml()
        tt = cli_xml.find("Decode/TranslatedText")
        self.assertEqual(tt.text, "Hemoglobin")

    @staticmethod
    def _set_attributes():
        """
        set some CodeListItem element attributes using test data
        :return: (dict) dictionary with CodeListItem attribute information
        """
        return {"CodedValue": "HGB", "OrderNumber": 1}

    @staticmethod
    def expected_dict():
        return {'CodedValue': 'HGB', 'OrderNumber': 1,
                'Decode': {'TranslatedText': [{'lang': 'en', '_content': 'Hemoglobin'}]},
                'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64848'}]}
