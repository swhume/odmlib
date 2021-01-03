from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestCodeList(TestCase):
    def setUp(self) -> None:
        attrs = self._set_attributes()
        self.cl = ODM.CodeList(**attrs)

    def test_add_code_list_item(self):
        cli1 = ODM.CodeListItem(CodedValue="HGB", OrderNumber=1)
        cli1.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        self.cl.CodeListItem.append(cli1)
        cli2 = ODM.CodeListItem(CodedValue="VITB12", OrderNumber=2)
        cli2.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64817"))
        self.cl.CodeListItem.append(cli2)
        cli3 = ODM.CodeListItem(CodedValue="GLUC", OrderNumber=3)
        cli3.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C41376")]
        self.cl.CodeListItem.append(cli3)
        cl_dict = self.cl.to_dict()
        print(cl_dict)
        self.assertDictEqual(cl_dict, self.expected_cli_dict())

    def test_add_enumerated_item(self):
        eni1 = ODM.EnumeratedItem(CodedValue="HGB", OrderNumber=1)
        eni1.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        self.cl.EnumeratedItem.append(eni1)
        eni2 = ODM.EnumeratedItem(CodedValue="VITB12", OrderNumber=2)
        eni2.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64817")]
        self.cl.EnumeratedItem.append(eni2)
        eni3 = ODM.EnumeratedItem(CodedValue="GLUC", OrderNumber=3)
        eni3.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C41376")]
        self.cl.EnumeratedItem.append(eni3)
        ei_dict = self.cl.to_dict()
        print(ei_dict)
        self.assertDictEqual(ei_dict, self.expected_eni_dict())

    def test_external_code_list(self):
        self.cl.ExternalCodeList = ODM.ExternalCodeList(Dictionary="MedDRA", Version="23.0", href="https://www.meddra.org/")
        ex_dict = self.cl.to_dict()
        self.assertDictEqual(ex_dict, self.expected_ex_dict())

    def test_add_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1, tt2]
        self.cl.Description = desc
        self.assertEqual(len(self.cl.Description.TranslatedText), 2)
        self.assertEqual(self.cl.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_alias(self):
        alias = ODM.Alias(Context="nci:ExtCodeID", Name="C64848")
        self.cl.Alias = [alias]
        self.assertEqual(self.cl.Alias[0].Name, "C64848")

    def test_to_json(self):
        attrs = self._set_attributes()
        cl = ODM.CodeList(**attrs)
        eni = ODM.EnumeratedItem(CodedValue="HGB", OrderNumber=1)
        eni.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        cl.EnumeratedItem.append(eni)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C65047"))
        cl_json = cl.to_json()
        cl_dict = json.loads(cl_json)
        print(cl_dict)
        self.assertDictEqual(cl_dict, self.expected_json_dict())

    def test_to_dict(self):
        attrs = self._set_attributes()
        cl = ODM.CodeList(**attrs)
        eni = ODM.EnumeratedItem(CodedValue="HGB", OrderNumber=1)
        eni.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        cl.EnumeratedItem.append(eni)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C65047"))
        cl_dict = cl.to_dict()
        self.assertDictEqual(cl_dict, self.expected_json_dict())

    def test_to_xml(self):
        attrs = self._set_attributes()
        cl = ODM.CodeList(**attrs)
        eni = ODM.EnumeratedItem(CodedValue="HGB", OrderNumber=1)
        eni.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        cl.EnumeratedItem.append(eni)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C65047"))
        cl_xml = cl.to_xml()
        self.assertEqual(cl_xml.attrib["OID"], "ODM.CL.LBTESTCD")
        ei = cl_xml.find("EnumeratedItem")
        self.assertEqual(ei.attrib["CodedValue"], "HGB")

    def test_to_xml_code_list_item(self):
        attrs = self._set_attributes()
        cl = ODM.CodeList(**attrs)
        cli1 = ODM.CodeListItem(CodedValue="HGB", OrderNumber=1)
        cli1.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        cl.CodeListItem.append(cli1)
        cli2 = ODM.CodeListItem(CodedValue="VITB12", OrderNumber=2)
        cli2.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64817"))
        cl.CodeListItem.append(cli2)
        cli3 = ODM.CodeListItem(CodedValue="GLUC", OrderNumber=3)
        cli3.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C41376"))
        cl.CodeListItem.append(cli3)
        cl_xml = cl.to_xml()
        self.assertEqual(cl_xml.attrib["OID"], "ODM.CL.LBTESTCD")
        ei = cl_xml.findall("CodeListItem")
        self.assertEqual(ei[0].attrib["CodedValue"], "HGB")

    def test_to_xml_external_code_list(self):
        attrs = self._set_attributes()
        cl = ODM.CodeList(**attrs)
        excl = ODM.ExternalCodeList(Dictionary="MedDRA", Version="23.0", href="https://www.meddra.org/")
        cl.ExternalCodeList = excl
        cl_xml = cl.to_xml()
        self.assertEqual(cl_xml.attrib["OID"], "ODM.CL.LBTESTCD")
        ecl = cl_xml.find("ExternalCodeList")
        self.assertEqual(ecl.attrib["Dictionary"], "MedDRA")


    def _set_attributes(self):
        """
        set some CodeList element attributes using test data
        :return: dictionary with CodeList attribute information
        """
        return {"OID": "ODM.CL.LBTESTCD", "Name": "Laboratory Test Code", "DataType": "text"}

    def expected_cli_dict(self):
        return {'OID': 'ODM.CL.LBTESTCD', 'Name': 'Laboratory Test Code', 'DataType': 'text',
                'CodeListItem': [{'CodedValue': 'HGB', 'OrderNumber': 1,
                                  'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64848'}]},
                                 {'CodedValue': 'VITB12', 'OrderNumber': 2,
                                  'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64817'}]},
                                 {'CodedValue': 'GLUC', 'OrderNumber': 3,
                                  'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C41376'}]}]}

    def expected_eni_dict(self):
        return {'OID': 'ODM.CL.LBTESTCD', 'Name': 'Laboratory Test Code', 'DataType': 'text',
                'EnumeratedItem': [{'CodedValue': 'HGB', 'OrderNumber': 1,
                                    'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64848'}]},
                                   {'CodedValue': 'VITB12', 'OrderNumber': 2,
                                    'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64817'}]},
                                   {'CodedValue': 'GLUC', 'OrderNumber': 3,
                                    'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C41376'}]}]}

    def expected_ex_dict(self):
        return {'OID': 'ODM.CL.LBTESTCD', 'Name': 'Laboratory Test Code', 'DataType': 'text',
                'ExternalCodeList': {'Dictionary': 'MedDRA', 'Version': '23.0', 'href': 'https://www.meddra.org/'}}

    def expected_json_dict(self):
        return {'OID': 'ODM.CL.LBTESTCD', 'Name': 'Laboratory Test Code', 'DataType': 'text',
                'EnumeratedItem': [{'CodedValue': 'HGB', 'OrderNumber': 1,
                                    'Alias': [{'Context': 'nci:ExtCodeID', 'Name': 'C64848'},
                                              {'Context': 'nci:ExtCodeID', 'Name': 'C65047'}]
                                    }]
                }

