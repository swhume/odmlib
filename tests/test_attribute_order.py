import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA


class TestAttributeOrder(unittest.TestCase):
    def setUp(self):
        self.validator = METADATA.MetadataSchema()

    def test_study_invalid_study_object(self):
        study = ODM.Study(OID="ST.001.Test")
        # StudyName is a child of GLobalVariables, not of Study
        with self.assertRaises(TypeError):
            study.StudyName = ODM.StudyName(_content="The ODM study name")

    def test_study_invalid_study_object_assignment(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        with self.assertRaises(TypeError):
            study.GlobalVariables.StudyName = ODM.ProtocolName(_content="The ODM protocol name")

    def test_valid_order_study_objects(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        self.assertTrue(study.verify_order())

    def test_invalid_order_study_objects(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        with self.assertRaises(ValueError):
            study.verify_order()

