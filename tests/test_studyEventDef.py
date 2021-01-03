from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM


class TestStudyEventDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_attributes()
        self.sed = ODM.StudyEventDef(**attrs)

    def test_add_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        self.sed.Description = ODM.Description()
        self.sed.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.sed.Description.TranslatedText), 2)
        self.assertEqual(self.sed.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_bad_attribute(self):
        attrs = self.set_attributes()
        attrs["Type"] = "Rescheduled"
        with self.assertRaises(ValueError):
            self.sed = ODM.StudyEventDef(**attrs)

    def test_add_form_ref(self):
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber=3)
        self.sed.FormRef = [fr1, fr2, fr3]
        self.assertEqual(self.sed.FormRef[0].FormOID, "ODM.F.VS")
        self.assertEqual(self.sed.FormRef[2].OrderNumber, 3)

    def test_add_alias(self):
        a1 = ODM.Alias(Context="SDTMIG", Name="VS")
        a2 = ODM.Alias(Context="CDASHIG", Name="VS")
        self.sed.Alias = [a1, a2]
        self.assertEqual(len(self.sed.Alias), 2)
        self.assertEqual(self.sed.Alias[1].Context, "CDASHIG")

    def test_to_json(self):
        attrs = self.set_attributes()
        sed = ODM.StudyEventDef(**attrs)
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        sed.Description = desc
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber=3)
        sed.FormRef = [fr1, fr2, fr3]
        a1 = ODM.Alias(Context="SDTMIG", Name="VS")
        sed.Alias = [a1]
        sed_json = sed.to_json()
        sed_dict = json.loads(sed_json)
        print(sed_dict)
        self.assertEqual(sed_dict["OID"], "ODM.SE.BASELINE")
        self.assertDictEqual(sed_dict, self.expected_dict())

    def test_to_dict(self):
        attrs = self.set_attributes()
        sed = ODM.StudyEventDef(**attrs)
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        sed.Description = desc
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber=3)
        sed.FormRef = [fr1, fr2, fr3]
        a1 = ODM.Alias(Context="SDTMIG", Name="VS")
        sed.Alias = [a1]
        sed_dict = sed.to_dict()
        self.assertEqual(sed_dict["OID"], "ODM.SE.BASELINE")
        self.assertDictEqual(sed_dict, self.expected_dict())

    def test_to_xml(self):
        attrs = self.set_attributes()
        sed = ODM.StudyEventDef(**attrs)
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        sed.Description = desc
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber=3)
        sed.FormRef = [fr1, fr2, fr3]
        a1 = ODM.Alias(Context="SDTMIG", Name="VS")
        sed.Alias = [a1]
        sed_xml = sed.to_xml()
        self.assertEqual(sed_xml.attrib["OID"], "ODM.SE.BASELINE")
        fr = sed_xml.findall("FormRef")
        self.assertEqual(len(fr), 3)
        self.assertEqual(fr[0].attrib, {"FormOID": "ODM.F.VS", "Mandatory": "Yes", "OrderNumber": "1"})

    def test_studyeventdef_slice(self):
        """ test the ability to reference a specific or slice of FormRefs """
        attrs = self.set_attributes()
        sed = ODM.StudyEventDef(**attrs)
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        sed.Description = desc
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber=3)
        sed.FormRef = [fr1, fr2, fr3]
        self.assertEqual(len(sed.FormRef), 3)
        first_fr = sed[0]
        self.assertEqual(first_fr.FormOID, "ODM.F.VS")
        slice_fr = sed[1:3]
        self.assertEqual(slice_fr[1].FormOID, "ODM.F.MH")

    @staticmethod
    def set_attributes():
        """
        set some StudyEventDef element attributes using test data
        :return: dictionary with StudyEventDef attribute information
        """
        return {"OID": "ODM.SE.BASELINE", "Name": "Baseline Visit", "Repeating": "No", "Type": "Scheduled",
                "Category": "Pre-treatment"}

    @staticmethod
    def expected_dict():
        return {'OID': 'ODM.SE.BASELINE', 'Name': 'Baseline Visit', 'Repeating': 'No', 'Type': 'Scheduled',
                'Category': 'Pre-treatment', 'FormRef': [{'FormOID': 'ODM.F.VS', 'Mandatory': 'Yes', 'OrderNumber': 1},
                                                  {'FormOID': 'ODM.F.DM', 'Mandatory': 'Yes', 'OrderNumber': 2},
                                                  {'FormOID': 'ODM.F.MH', 'Mandatory': 'Yes', 'OrderNumber': 3}],
                'Description': {'TranslatedText': [{'lang': 'en', '_content': 'this is the first test description'}]},
                'Alias': [{'Context': 'SDTMIG', 'Name': 'VS'}]}
