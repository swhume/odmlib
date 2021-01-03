from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestConditionDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_attributes()
        self.cond_def = ODM.ConditionDef(**attrs)

    def test_add_formal_expression(self):
        fex = ODM.FormalExpression(Context="Python 3.7", _content="BRTHYR != 4")
        self.cond_def.FormalExpression = [fex]
        self.assertEqual(self.cond_def.FormalExpression[0]._content, "BRTHYR != 4")

    def test_add_description(self):
        tt1 = ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")
        self.cond_def.Description = ODM.Description()
        self.cond_def.Description.TranslatedText = [tt1]
        self.assertEqual(len(self.cond_def.Description.TranslatedText), 1)
        self.assertEqual(self.cond_def.Description.TranslatedText[0]._content, 'Skip the BRTHMO field when BRTHYR length NE 4')

    def test_add_alias(self):
        a = ODM.Alias(Context="CDASH", Name="AGE")
        self.cond_def.Alias = [a]
        self.assertEqual(self.cond_def.Alias[0].Name, "AGE")

    def test_to_json(self):
        attrs = self.set_attributes()
        cd = ODM.ConditionDef(**attrs)
        tt1 = ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")
        cd.Description = ODM.Description()
        cd.Description.TranslatedText.append(tt1)
        cd.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="BRTHYR != 4")]
        cd_dict = cd.to_dict()
        print(cd_dict)
        method_json = cd.to_json()
        method_dict = json.loads(method_json)
        self.assertEqual(method_dict["OID"], "ODM.CD.BRTHMO")
        self.assertDictEqual(method_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self.set_attributes()
        cd = ODM.ConditionDef(**attrs)
        cd.Description = ODM.Description()
        cd.Description.TranslatedText = [ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")]
        cd.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="BRTHYR != 4")]
        cd_dict = cd.to_dict()
        print(cd_dict)
        self.assertEqual(cd_dict["OID"], "ODM.CD.BRTHMO")
        self.assertDictEqual(cd_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self.set_attributes()
        cd = ODM.ConditionDef(**attrs)
        cd.Description = ODM.Description()
        cd.Description.TranslatedText = [ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")]
        cd.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="BRTHYR != 4")]
        cd_xml = cd.to_xml()
        self.assertEqual(cd_xml.attrib["OID"], "ODM.CD.BRTHMO")
        fex_xml = cd_xml.find("FormalExpression")
        self.assertEqual(fex_xml.attrib["Context"], "Python 3.7")

    def set_attributes(self):
        """
        set some cond_def element attributes using test data
        :return: dictionary with cond_def attribute information
        """
        return {"OID": "ODM.CD.BRTHMO", "Name": "Skip BRTHMO when no BRTHYR"}

    def expected_dict(self):
        return {'OID': 'ODM.CD.BRTHMO', 'Name': 'Skip BRTHMO when no BRTHYR', 'Description':
            {'TranslatedText': [{'_content': 'Skip the BRTHMO field when BRTHYR length NE 4', 'lang': 'en'}]},
             'FormalExpression': [{'Context': 'Python 3.7', '_content': 'BRTHYR != 4'}]}
