from unittest import TestCase
import odmlib.odm_loader as OL
import odmlib.loader as LD
import os
import json


class TestJsonFromXml(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        self.loader = LD.ODMLoader(OL.XMLODMLoader())

    def test_open_odm_document(self):
        root = self.loader.open_odm_document(self.odm_file)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("CDASH_File_2011-10-24", root.attrib["FileOID"])

    def test_json_from_xml(self):
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.create_odmlib(root)
        odm_json = odm.to_json()
        odm_json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash_odm_test.json')
        with open(odm_json_file, "w") as odm_in:
            odm_in.write(odm_json)
        odm_dict = json.loads(odm_json)
        self.assertEqual(odm_dict["Study"][0]["MetaDataVersion"][0]["ItemDef"][0]["OID"], "ODM.IT.Common.StudyID")
