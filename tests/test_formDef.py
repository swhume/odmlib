from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestFormDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_formdef_attributes()
        self.formdef = ODM.FormDef(**attrs)

    def test_add_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        self.formdef.Description = ODM.Description()
        self.formdef.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.formdef.Description.TranslatedText), 2)
        self.assertEqual(self.formdef.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_item_group_ref(self):
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1)
        self.formdef.ItemGroupRef.append(igr)
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2)
        self.formdef.ItemGroupRef.append(igr)
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3)
        self.formdef.ItemGroupRef.append(igr)
        self.assertEqual(self.formdef.ItemGroupRef[0].ItemGroupOID, "ODM.IG.COMMON")
        self.assertEqual(self.formdef.ItemGroupRef[2].OrderNumber, 3)

    def test_add_alias(self):
        self.formdef.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        self.formdef.Alias.append(ODM.Alias(Context="CDASHIG", Name="VS"))
        self.assertEqual(len(self.formdef.Alias), 2)
        self.assertEqual(self.formdef.Alias[1].Context, "CDASHIG")

    def test_add_not_alias(self):
        item = ODM.ItemDef(OID="ODM.IT.VSPOS", Name="VS Position", DataType="text")
        with self.assertRaises(TypeError):
            self.formdef.Alias = [item]
        self.formdef.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        # list accepts invalid objects
        self.formdef.Alias.append(ODM.ItemDef(OID="ODM.IT.VSDT", Name="VS Date", DataType="text"))
        self.assertEqual(len(self.formdef.Alias), 2)
        self.assertEqual(self.formdef.Alias[0].Context, "SDTMIG")

    def test_to_json(self):
        attrs = self.set_formdef_attributes()
        fd = ODM.FormDef(**attrs)
        tt = ODM.TranslatedText(_content="this is the first test description", lang="en")
        fd.Description = ODM.Description()
        fd.Description.TranslatedText = [tt]
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
        fd.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        fd_json = fd.to_json()
        fd_dict = json.loads(fd_json)
        print(fd_dict)
        self.assertEqual(fd_dict["OID"], "ODM.F.VS")
        self.assertDictEqual(fd_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self.set_formdef_attributes()
        fd = ODM.FormDef(**attrs)
        fd.Description = ODM.Description()
        fd.Description.TranslatedText.append(ODM.TranslatedText(_content="this is the first test description", lang="en"))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
        fd.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        fd_dict = fd.to_dict()
        self.assertEqual(fd_dict["OID"], "ODM.F.VS")
        self.assertDictEqual(fd_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self.set_formdef_attributes()
        fd = ODM.FormDef(**attrs)
        fd.Description = ODM.Description()
        fd.Description.TranslatedText.append(ODM.TranslatedText(_content="this is the first test description", lang="en"))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
        fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
        fd.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        fd_xml = fd.to_xml()
        self.assertEqual(fd_xml.attrib["OID"], "ODM.F.VS")
        igr = fd_xml.findall("ItemGroupRef")
        self.assertEqual(len(igr), 3)
        self.assertEqual(igr[0].attrib, {"ItemGroupOID": "ODM.IG.COMMON", "Mandatory": "Yes", "OrderNumber": "1"})

    @staticmethod
    def set_formdef_attributes():
        """
        set some FormDef element attributes using test data
        :return: dictionary with FormDef attribute information
        """
        return {"OID": "ODM.F.VS", "Name": "Vital Signs Form", "Repeating": "Yes"}

    @staticmethod
    def expected_dict():
        return {'OID': 'ODM.F.VS', 'Name': 'Vital Signs Form', 'Repeating': 'Yes',
                'ItemGroupRef': [{'ItemGroupOID': 'ODM.IG.COMMON', 'Mandatory': 'Yes', 'OrderNumber': 1},
                                 {'ItemGroupOID': 'ODM.IG.VS_GENERAL', 'Mandatory': 'Yes', 'OrderNumber': 2},
                                 {'ItemGroupOID': 'ODM.IG.VS', 'Mandatory': 'Yes', 'OrderNumber': 3}],
                'Description': {'TranslatedText':
                                [{'_content': 'this is the first test description', 'lang': 'en'}]},
                'Alias': [{'Context': 'SDTMIG', 'Name': 'VS'}]}
