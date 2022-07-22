from unittest import TestCase
import odmlib.odm_loader as OL
import odmlib.loader as LD
import os

from tests import get_data_file_path


class TestODMLoaderString(TestCase):
    def setUp(self) -> None:
        self.odm_file = get_data_file_path("cdash-odm-test.xml")
        with open(self.odm_file, "r", encoding="utf-8") as f:
            self.odm_string = f.read()
        self.loader = LD.ODMLoader(OL.XMLODMLoader())
    
    def test_open_odm_document(self):
        root = self.loader.load_odm_string(self.odm_string)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("CDASH_File_2011-10-24", root.attrib["FileOID"])

    def test_odm(self):
        self.loader.load_odm_string(self.odm_string)
        odm = self.loader.root()
        self.assertEqual(odm.FileOID, "CDASH_File_2011-10-24")

    def test_meta_data_version(self):
        self.loader.load_odm_string(self.odm_string)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "TRACE-XML MDV")
        self.assertEqual(mdv.Protocol.StudyEventRef[0].StudyEventOID, "BASELINE")
        self.assertEqual(mdv.ItemDef[3].Question.TranslatedText[0]._content, "Visit Date")
        self.assertEqual(mdv.CodeList[0].CodeListItem[1].CodedValue, "MODERATE")

    def test_mdv_find_by_OID(self):
        self.loader.load_odm_string(self.odm_string)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "TRACE-XML MDV")
        ir = mdv.ItemGroupDef[0].find("ItemRef", "ItemOID", "ODM.IT.Common.SiteID")
        self.assertEqual(ir.ItemOID, mdv.ItemGroupDef[0].ItemRef[1].ItemOID)
        it = mdv.find("ItemDef", "OID", "ODM.IT.AE.AEYN")
        self.assertEqual(it.CodeListRef.CodeListOID, "ODM.CL.NY_SUB_Y_N")
        cli = mdv.CodeList[2].find("CodeListItem", "CodedValue", "DOSE REDUCED")
        self.assertEqual(cli.Decode.TranslatedText[0]._content, "DOSE REDUCED")

    def test_odm_round_trip(self):
        root = self.loader.load_odm_string(self.odm_string)
        odm = self.loader.create_odmlib(root)
        odm_json = odm.to_json()
        odm_json_file = get_data_file_path("cdash_odm_test.json", check_exists=False)
        with open(odm_json_file, "w") as odm_in:
            odm_in.write(odm_json)
        json_loader = LD.ODMLoader(OL.JSONODMLoader())
        odm_dict = json_loader.open_odm_document(odm_json_file)
        rt_odm = json_loader.create_odmlib(odm_dict, "ODM")
        odm_xml_file = get_data_file_path("cdash_odm_test_roundtrip.xml", check_exists=False)
        rt_odm.write_xml(odm_xml_file)
        root2 = self.loader.open_odm_document(odm_xml_file)
        odm2 = self.loader.create_odmlib(root2)
        self.assertEqual(odm2.Study[0].MetaDataVersion[0].ItemDef[0].OID, "ODM.IT.Common.StudyID")
        self.assertEqual(len(odm2.Study[0].MetaDataVersion[0].ItemGroupDef[1]), 7)