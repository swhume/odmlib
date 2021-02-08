from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestItemDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_item_attributes()
        self.item = ODM.ItemDef(**attrs)

    def test_required_attributes_only(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text"}
        self.item = ODM.ItemDef(**attrs)
        self.assertEqual(self.item.OID, "ODM.IT.AE.AEYN")

    def test_add_range_check(self):
        rc = ODM.RangeCheck(Comparator="EQ", SoftHard="Soft")
        tt1 = ODM.TranslatedText(_content="invalid test code", lang="en")
        tt2 = ODM.TranslatedText(_content="code de test invalide", lang="fr")
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        attrs = {"Comparator": "GT", "SoftHard": "Soft"}
        rc1 = ODM.RangeCheck(**attrs)
        tt1 = ODM.TranslatedText(_content="invalid test code", lang="en")
        rc1.ErrorMessage.TranslatedText = [tt1]
        rc1.CheckValue = [ODM.CheckValue(_content="SYSBP")]
        rc1.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc1.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        self.item.RangeCheck = [rc, rc1]
        self.assertEqual(self.item.RangeCheck[0].Comparator, "EQ")
        self.assertEqual(self.item.RangeCheck[1].Comparator, "GT")

    def test_set_description(self):
        attrs = {"_content": "this is the first test description", "lang": "en"}
        tt1 = ODM.TranslatedText(**attrs)
        self.item.Description.TranslatedText.append(tt1)
        self.assertEqual(self.item.Description.TranslatedText[0].lang, "en")
        self.assertEqual(self.item.Description.TranslatedText[0]._content, "this is the first test description")

    def test_set_invalid_description(self):
        rc = ODM.RangeCheck(Comparator="EQ", SoftHard="Soft")
        tt1 = ODM.TranslatedText(_content="invalid test code", lang="en")
        tt2 = ODM.TranslatedText(_content="code de test invalide", lang="fr")
        rc.ErrorMessage.TranslatedText.append(tt1)
        rc.ErrorMessage.TranslatedText.append(tt2)
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = [ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")]
        self.item.RangeCheck = [rc]
        # Description requires a Description object, not a RangeCheck object
        with self.assertRaises(TypeError):
            self.item.Description = rc

    def test_add_description(self):
        attrs = {"_content": "this is the first test description", "lang": "en"}
        tt1 = ODM.TranslatedText(**attrs)
        attrs = {"_content": "this is the second test description", "lang": "en"}
        tt2 = ODM.TranslatedText(**attrs)
        self.item.Description.TranslatedText.append(tt1)
        self.item.Description.TranslatedText.append(tt2)
        self.assertEqual(self.item.Description.TranslatedText[1]._content, "this is the second test description")

    def test_add_question(self):
        tt1 = ODM.TranslatedText(_content="Any AEs?", lang="en")
        self.item.Question.TranslatedText.append(tt1)
        self.assertEqual(self.item.Question.TranslatedText[0]._content, "Any AEs?")

    def test_external_question(self):
        self.item.ExternalQuestion = ODM.ExternalQuestion(Dictionary="SF36", Version="12", Code="Walks 1-mile")
        self.assertEqual(self.item.ExternalQuestion.Dictionary, "SF36")

    def test_add_measurement_unit_ref(self):
        self.item.MeasurementUnitRef.append(ODM.MeasurementUnitRef(MeasurementUnitOID="MU.UNITS"))
        self.item.MeasurementUnitRef.append(ODM.MeasurementUnitRef(MeasurementUnitOID="MU2.UNITS2"))
        self.assertEqual(self.item.MeasurementUnitRef[0].MeasurementUnitOID, "MU.UNITS")

    def test_codelist_ref(self):
        self.item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        self.assertEqual(self.item.CodeListRef.CodeListOID, "CL.NY_SUB_Y_N_2011-10-24")

    def test_codelist_ref_exists_check(self):
        attrs = self.set_item_attributes()
        item = ODM.ItemDef(**attrs)
        codelistref_check_succeeds = False
        if not item.CodeListRef:
            codelistref_check_succeeds = True
        if item.CodeListRef:
            codelistref_check_succeeds = False
        self.assertTrue(codelistref_check_succeeds)

    def test_add_alias(self):
        self.item.Alias = [ODM.Alias(Context="CDASH", Name="AEYN")]
        self.assertEqual(self.item.Alias[0].Name, "AEYN")

    def test_to_json(self):
        attrs = self.set_item_attributes()
        item = ODM.ItemDef(**attrs)
        item.Description.TranslatedText.append(ODM.TranslatedText(_content="this is the first test description", lang="en"))
        item.Question.TranslatedText = [ODM.TranslatedText(_content="Any AEs?", lang="en")]
        item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item_json = item.to_json()
        item_dict = json.loads(item_json)
        self.assertEqual(item_dict["OID"], "ODM.IT.AE.AEYN")

    def test_to_dict(self):
        attrs = self.set_item_attributes()
        item = ODM.ItemDef(**attrs)
        item.Description.TranslatedText = [ODM.TranslatedText(_content="this is the first test description", lang="en")]
        item.Question.TranslatedText = [ODM.TranslatedText(_content="Any AEs?", lang="en")]
        item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item_dict = item.to_dict()
        expected_dict = {'OID': 'ODM.IT.AE.AEYN', 'Name': 'Any AEs?', 'DataType': 'text', 'Length': 1,
                         'SASFieldName': 'AEYN', 'SDSVarName': 'AEYN', 'Origin': 'CRF',
                         'Comment': 'Data management field',
                         'Description': {'TranslatedText': [{'_content': 'this is the first test description',
                                          'lang': 'en'}]},
                         'Question': {'TranslatedText': [{'_content': 'Any AEs?', 'lang': 'en'}]},
                         'CodeListRef': {'CodeListOID': 'CL.NY_SUB_Y_N_2011-10-24'}}
        self.assertDictEqual(item_dict, expected_dict)

    def test_to_dict_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1, tt2]
        desc_dict = desc.to_dict()
        print(desc_dict)
        self.assertDictEqual(desc_dict["TranslatedText"][1],
                             {'_content': 'this is the second test description', 'lang': 'en'})

    def test_to_xml_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1, tt2]
        desc_xml = desc.to_xml()
        tts = desc_xml.findall("TranslatedText")
        self.assertEqual(tts[0].text, "this is the first test description")

    def test_to_xml(self):
        attrs = self.set_item_attributes()
        item = ODM.ItemDef(**attrs)
        item.Description.TranslatedText = [ODM.TranslatedText(_content="this is the first test description", lang="en")]
        item.Question.TranslatedText = [ODM.TranslatedText(_content="Any AEs?", lang="en")]
        item.ExternalQuestion = ODM.ExternalQuestion(Dictionary="SF36", Version="12", Code="Walks 1-mile")
        item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item.RangeCheck = [ODM.RangeCheck(Comparator="EQ", SoftHard="Soft")]
        item.RangeCheck[0].CheckValue = [ODM.CheckValue(_content="DIABP")]
        item.RangeCheck[0].FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        item.RangeCheck[0].MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        item.RangeCheck[0].ErrorMessage.TranslatedText = [ODM.TranslatedText(_content="invalid test code", lang="en")]
        item_xml = item.to_xml()
        self.assertEqual(item_xml.attrib["OID"], "ODM.IT.AE.AEYN")
        cv = item_xml.find("*/CheckValue")
        self.assertEqual(cv.text, "DIABP")
        dt = item_xml.findall("Description/TranslatedText")
        self.assertEqual(len(dt), 1)


    def test_missing_itemdef_attributes(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?"}
        with self.assertRaises(ValueError):
            ODM.ItemDef(**attrs)

    def test_invalid_attribute_data_type(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "SignificantDigits": "A"}
        with self.assertRaises(TypeError):
            self.item = ODM.ItemDef(**attrs)

    def set_item_attributes(self):
        """
        set some ItemDef element attributes using test data
        :return: dictionary with ItemDef attribute information
        """
        return {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field"}

