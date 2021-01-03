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
        self.study.StudyName = study_name
        self.study.StudyDescription = study_desc
        self.study.ProtocolName = protocol_name
        self.assertEqual(self.study.StudyName._content, "The ODM study name")

    def test_study_dict(self):
        self.study.StudyName = ODM.StudyName(_content="The ODM study name")
        self.study.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        self.study.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study_dict = self.study.to_dict()
        print(study_dict)
        self.assertDictEqual(self.expected_dict(), study_dict)

    def test_study_to_xml(self):
        self.study.StudyName = ODM.StudyName(_content="The ODM study name")
        self.study.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        self.study.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study_xml = self.study.to_xml()
        pn = study_xml.find("ProtocolName")
        self.assertEqual(pn.text, "The ODM protocol name")

    def expected_dict(self):
        return {'OID': 'ST.001.Test',
                'StudyName': {'_content': 'The ODM study name'},
                'StudyDescription': {'_content': 'The description of the ODM study'},
                'ProtocolName': {'_content': 'The ODM protocol name'}}
