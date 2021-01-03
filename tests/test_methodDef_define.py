from unittest import TestCase
import json
import odmlib.define_2_0.model as DEFINE


class TestMethodDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_attributes()
        self.methoddef = DEFINE.MethodDef(**attrs)

    def test_add_formal_expression(self):
        self.FormalExpression = [DEFINE.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        self.assertEqual(self.FormalExpression[0]._content, "print('hello world')")

    def test_add_description(self):
        tt1 = DEFINE.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        tt2 = DEFINE.TranslatedText(_content="For the complete algorithm see the referenced external document.", lang="fr")
        self.methoddef.Description = DEFINE.Description()
        self.methoddef.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.methoddef.Description.TranslatedText), 2)
        self.assertEqual(self.methoddef.Description.TranslatedText[1]._content,
                         'For the complete algorithm see the referenced external document.')

    def test_add_alias(self):
        self.methoddef.Alias = [DEFINE.Alias(Context="CDASH", Name="AGE")]
        self.assertEqual(self.methoddef.Alias[0].Name, "AGE")

    def test_to_json(self):
        attrs = self.set_attributes()
        method = DEFINE.MethodDef(**attrs)
        tt1 = DEFINE.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        method.Description = DEFINE.Description()
        method.Description.TranslatedText = [tt1]
        fex = DEFINE.FormalExpression(Context="Python 3.7", _content="print('hello world')")
        method.FormalExpression = [fex]
        method_dict = method.to_dict()
        print(method_dict)
        method_json = method.to_json()
        method_dict = json.loads(method_json)
        self.assertEqual(method_dict["OID"], "ODM.MT.AGE")
        self.assertDictEqual(method_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self.set_attributes()
        method = DEFINE.MethodDef(**attrs)
        desc = DEFINE.Description()
        tt1 = DEFINE.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        desc.TranslatedText = [tt1]
        method.Description = desc
        fex = DEFINE.FormalExpression(Context="Python 3.7", _content="print('hello world')")
        method.FormalExpression = [fex]
        method_dict = method.to_dict()
        self.assertEqual(method_dict["OID"], "ODM.MT.AGE")
        self.assertDictEqual(method_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self.set_attributes()
        method = DEFINE.MethodDef(**attrs)
        desc = DEFINE.Description()
        tt1 = DEFINE.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        desc.TranslatedText = [tt1]
        method.Description = desc
        fex = DEFINE.FormalExpression(Context="Python 3.7", _content="print('hello world')")
        method.FormalExpression = [fex]
        method_xml = method.to_xml()
        self.assertEqual(method_xml.attrib["OID"], "ODM.MT.AGE")
        fex = method_xml.find("FormalExpression")
        self.assertEqual(fex.attrib["Context"], "Python 3.7")


    def set_attributes(self):
        """
        set some MethodDef element attributes using test data
        :return: dictionary with MethodDef attribute information
        """
        return {"OID": "ODM.MT.AGE", "Name": "Algorithm to derive AGE", "Type": "Computation"}

    def expected_dict(self):
        return {'OID': 'ODM.MT.AGE', 'Name': 'Algorithm to derive AGE', 'Type': 'Computation', 'Description':
            {'TranslatedText': [{'_content': 'Age at Screening Date (Screening Date - Birth date)', 'lang': 'en'}]},
             'FormalExpression': [{'Context': 'Python 3.7', '_content': "print('hello world')"}]}
