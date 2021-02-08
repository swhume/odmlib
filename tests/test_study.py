from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM


class TestStudy(TestCase):
    def setUp(self) -> None:
        self.study = ODM.Study(OID="ST.001.Test")

    def test_required_attributes(self):
        self.assertEqual(self.study.OID, "ST.001.Test")

    def test_full_study(self):
        study_name = ODM.StudyName(_content="The ODM study name")
        study_desc = ODM.StudyDescription(_content="The description of the ODM study")
        protocol_name = ODM.ProtocolName(_content="The ODM protocol name")
        self.study.GlobalVariables = ODM.GlobalVariables()
        self.study.GlobalVariables.StudyName = study_name
        self.study.GlobalVariables.StudyDescription = study_desc
        self.study.GlobalVariables.ProtocolName = protocol_name
        self.assertEqual(self.study.GlobalVariables.StudyName._content, "The ODM study name")

    def test_study_dict(self):
        self.study.GlobalVariables = ODM.GlobalVariables()
        self.study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        self.study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        self.study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study_dict = self.study.to_dict()
        print(study_dict)
        self.assertDictEqual(self.expected_dict(), study_dict)

    def test_study_to_xml(self):
        self.study.GlobalVariables = ODM.GlobalVariables()
        self.study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        self.study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        self.study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study_xml = self.study.to_xml()
        gv = study_xml.find("GlobalVariables")
        pn = gv.find("ProtocolName")
        self.assertEqual(pn.text, "The ODM protocol name")

    def expected_dict(self):
        return {'OID': 'ST.001.Test', "GlobalVariables": {
                'StudyName': {'_content': 'The ODM study name'},
                'StudyDescription': {'_content': 'The description of the ODM study'},
                'ProtocolName': {'_content': 'The ODM protocol name'}}}
