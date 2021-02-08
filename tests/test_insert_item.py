import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_loader as OL
import odmlib.loader as LD
import os


class TestInsertItem(unittest.TestCase):
    def setUp(self):
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        self.odm_file_out = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test-insert.xml')
        self.loader = LD.ODMLoader(OL.XMLODMLoader())

    def test_insert_item_with_none_element(self):
        attrs = self.set_item_attributes()
        item = ODM.ItemDef(**attrs)
        # to support the test a null version of CodeListRef is created, but should be ignored on output
        if item.CodeListRef:
            self.assertIsNotNone(item.CodeListRef)
        if item.SignificantDigits:
            self.assertIsNotNone(item.SignificantDigits)
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        mdv.ItemDef.append(item)
        attrs = self.get_root_attributes()
        root = ODM.ODM(**attrs)
        study = self.add_study(mdv)
        root.Study = [study]
        root.write_xml(self.odm_file_out)
        loader = LD.ODMLoader(OL.XMLODMLoader())
        loader.open_odm_document(self.odm_file_out)
        mdv = loader.MetaDataVersion()
        is_found_inserted_item = False
        for it in mdv.ItemDef:
            if it.OID == "ODM.IT.AE.TEST":
                is_found_inserted_item = True
        self.assertTrue(is_found_inserted_item)
        # TODO test json for None values
        odm_json = root.to_json()

    def add_study(self, mdv):
        study_name = ODM.StudyName(_content="ODM XML Test Study Name")
        protocol_name = ODM.ProtocolName(_content="ODM XML Test Study")
        study_description = ODM.StudyDescription(_content="Testing the generation of an ODM XML file")
        gv = ODM.GlobalVariables()
        gv.StudyName = study_name
        gv.StudyDescription = study_description
        gv.ProtocolName = protocol_name
        study = ODM.Study(OID="ODM.STUDY.001")
        study.GlobalVariables = gv
        study.MetaDataVersion = [mdv]
        return study

    def set_item_attributes(self):
            return {"OID": "ODM.IT.AE.TEST", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": None}

    def get_root_attributes(self):
        return {"FileOID": "ODM.MDV.TEST.001", "Granularity": "Metadata",
                "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
                "CreationDateTime": "2020-07-13T00:13:51.309617+00:00", "ODMVersion": "1.3.2", "FileType": "Snapshot",
                "Originator": "RDS", "SourceSystem": "ODMLib", "SourceSystemVersion": "0.1"}
