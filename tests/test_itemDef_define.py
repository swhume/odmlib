from unittest import TestCase
import json
import odmlib.define_2_0.model as DEFINE


class TestItemDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_item_attributes()
        self.item = DEFINE.ItemDef(**attrs)

    def test_required_attributes_only(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text"}
        self.item = DEFINE.ItemDef(**attrs)
        self.assertEqual(self.item.OID, "ODM.IT.AE.AEYN")

    def test_add_value_list_ref(self):
        vlr = DEFINE.ValueListRef(ValueListOID="VL.DA.DAORRES")
        attrs = {"OID": "IT.DA.DAORRES", "Name": "DAORRES", "DataType": "text", "Length": "2", "SASFieldName": "DAORRES"}
        itd = DEFINE.ItemDef(**attrs)
        tt1 = DEFINE.TranslatedText(_content="Assessment Result in Original Units", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText.append(tt1)
        itd.Description = desc
        itd.ValueListRef = vlr
        self.assertEqual(itd.ValueListRef.ValueListOID, "VL.DA.DAORRES")
        self.assertEqual(itd.OID, "IT.DA.DAORRES")

    def test_set_description(self):
        attrs = {"_content": "Assessment Result in Original Units", "lang": "en"}
        tt1 = DEFINE.TranslatedText(**attrs)
        self.item.Description.TranslatedText.append(tt1)
        self.assertEqual(self.item.Description.TranslatedText[0].lang, "en")
        self.assertEqual(self.item.Description.TranslatedText[0]._content, "Assessment Result in Original Units")

    def test_set_invalid_description(self):
        rc = DEFINE.RangeCheck(Comparator="EQ", SoftHard="Soft", ItemOID="IT.DA.DAORRES")
        rc.CheckValue = [DEFINE.CheckValue(_content="DIABP")]
        self.item.RangeCheck = [rc]
        # Description requires a Description object, not a RangeCheck object
        with self.assertRaises(TypeError):
            self.item.Description = rc

    def test_add_description(self):
        attrs = {"_content": "this is the first test description", "lang": "en"}
        tt1 = DEFINE.TranslatedText(**attrs)
        attrs = {"_content": "this is the second test description", "lang": "en"}
        tt2 = DEFINE.TranslatedText(**attrs)
        self.item.Description.TranslatedText.append(tt1)
        self.item.Description.TranslatedText.append(tt2)
        self.assertEqual(self.item.Description.TranslatedText[1]._content, "this is the second test description")

    def test_codelist_ref(self):
        self.item.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        self.assertEqual(self.item.CodeListRef.CodeListOID, "CL.NY_SUB_Y_N_2011-10-24")

    def test_origin(self):
        self.item.Origin = DEFINE.Origin(Type="Assigned")
        self.assertEqual(self.item.Origin.Type, "Assigned")

    def test_add_alias(self):
        self.item.Alias = [DEFINE.Alias(Context="CDASH", Name="AEYN")]
        self.assertEqual(self.item.Alias[0].Name, "AEYN")

    def test_to_json(self):
        attrs = self.set_item_attributes()
        item = DEFINE.ItemDef(**attrs)
        item.Description.TranslatedText.append(DEFINE.TranslatedText(_content="this is the first test description", lang="en"))
        item.Question.TranslatedText = [DEFINE.TranslatedText(_content="Any AEs?", lang="en")]
        item.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item_json = item.to_json()
        item_dict = json.loads(item_json)
        self.assertEqual(item_dict["OID"], "ODM.IT.AE.AEYN")

    def test_to_dict(self):
        attrs = self.set_item_attributes()
        item = DEFINE.ItemDef(**attrs)
        item.Description.TranslatedText = [DEFINE.TranslatedText(_content="this is the first test description", lang="en")]
        item.Question.TranslatedText = [DEFINE.TranslatedText(_content="Any AEs?", lang="en")]
        item.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item_dict = item.to_dict()
        expected_dict = {'OID': 'ODM.IT.AE.AEYN', 'Name': 'Any AEs?', 'DataType': 'text', 'Length': 1,
                         'SASFieldName': 'AEYN', "CommentOID": "ODM.CO.120",
                         'Description': {'TranslatedText': [{'_content': 'this is the first test description',
                                          'lang': 'en'}]},
                         'Question': {'TranslatedText': [{'_content': 'Any AEs?', 'lang': 'en'}]},
                         'CodeListRef': {'CodeListOID': 'CL.NY_SUB_Y_N_2011-10-24'}}
        self.assertDictEqual(item_dict, expected_dict)

    def test_to_dict_description(self):
        tt1 = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = DEFINE.TranslatedText(_content="this is the second test description", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText = [tt1, tt2]
        desc_dict = desc.to_dict()
        print(desc_dict)
        self.assertDictEqual(desc_dict["TranslatedText"][1],
                             {'_content': 'this is the second test description', 'lang': 'en'})

    def test_to_xml_description(self):
        tt1 = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = DEFINE.TranslatedText(_content="this is the second test description", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText = [tt1, tt2]
        desc_xml = desc.to_xml()
        tts = desc_xml.findall("TranslatedText")
        self.assertEqual(tts[0].text, "this is the first test description")

    def test_to_xml(self):
        attrs = self.set_item_attributes()
        item = DEFINE.ItemDef(**attrs)
        item.Description.TranslatedText = [DEFINE.TranslatedText(_content="this is the first test description", lang="en")]
        item.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item.RangeCheck = [DEFINE.RangeCheck(Comparator="EQ", SoftHard="Soft", ItemOID="IT.DA.DAORRES")]
        item.RangeCheck[0].CheckValue = [DEFINE.CheckValue(_content="DIABP")]
        item_xml = item.to_xml()
        self.assertEqual(item_xml.attrib["OID"], "ODM.IT.AE.AEYN")
        cv = item_xml.find("*/CheckValue")
        self.assertEqual(cv.text, "DIABP")
        dt = item_xml.findall("Description/TranslatedText")
        self.assertEqual(len(dt), 1)


    def test_missing_itemdef_attributes(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?"}
        with self.assertRaises(ValueError):
            DEFINE.ItemDef(**attrs)

    def test_invalid_attribute_data_type(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "SignificantDigits": "A"}
        with self.assertRaises(TypeError):
            self.item = DEFINE.ItemDef(**attrs)

    def set_item_attributes(self):
        """
        set some ItemDef element attributes using test data
        :return: dictionary with ItemDef attribute information
        """
        return {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "CommentOID": "ODM.CO.120"}

