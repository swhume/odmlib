from unittest import TestCase
import odmlib.define_loader as OL
import odmlib.loader as LD
import os


class TestDefineLoaderString(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'define2-0-0-sdtm-test.xml')
        with open(self.odm_file, "r", encoding="utf-8") as f:
            self.odm_string = f.read()
        self.loader = LD.ODMLoader(OL.XMLDefineLoader())

    def test_open_odm_document(self):
        root = self.loader.load_odm_string(self.odm_string)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("www.cdisc.org.Studycdisc01-Define-XML_2.0.0", root.attrib["FileOID"])

    def test_meta_data_version(self):
        self.loader.load_odm_string(self.odm_string)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC01, Data Definitions")
        self.assertEqual(mdv.ValueListDef[0].OID, "VL.DA.DAORRES")
        self.assertEqual(mdv.ItemDef[0].CodeListRef.CodeListOID, "CL.ACN")
        self.assertEqual(mdv.CodeList[1].CodeListItem[0].CodedValue, "AE")
        self.assertEqual(mdv.CommentDef[0].OID, "COM.AGEU")

    def test_mdv_find_by_OID(self):
        self.loader.load_odm_string(self.odm_string)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC01, Data Definitions")
        ir = mdv.ItemGroupDef[0].find("ItemRef", "ItemOID", "IT.TA.DOMAIN")
        self.assertEqual(ir.ItemOID, mdv.ItemGroupDef[0].ItemRef[1].ItemOID)
        it = mdv.find("ItemDef", "OID", "IT.AE.AESEV")
        self.assertEqual(it.CodeListRef.CodeListOID, "CL.AESEV")
        cli = mdv.CodeList[4].find("CodeListItem", "CodedValue", "MODERATE")
        self.assertEqual(cli.Decode.TranslatedText[0]._content, "Grade 2")
        ir = mdv.ValueListDef[2].find("ItemRef", "ItemOID", "IT.EG.EGSTRESC.QTCF")
        self.assertEqual(ir.WhereClauseRef[0].WhereClauseOID, "WC.EG.EGTESTCD.QTCF")

    def test_odm_round_trip(self):
        root = self.loader.load_odm_string(self.odm_string)
        odm = self.loader.create_odmlib(root)
        odm_json = odm.to_json()
        odm_json_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'sdtm_define2_test.json')
        with open(odm_json_file, "w") as odm_in:
            odm_in.write(odm_json)
        json_loader = LD.ODMLoader(OL.JSONDefineLoader())
        odm_dict = json_loader.open_odm_document(odm_json_file)
        rt_odm = json_loader.create_odmlib(odm_dict, "ODM")
        def_xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'sdtm_def_test_roundtrip.xml')
        rt_odm.write_xml(def_xml_file)
        root2 = self.loader.open_odm_document(def_xml_file)
        odm2 = self.loader.create_odmlib(root2)
        self.assertEqual(odm2.Study[0].MetaDataVersion.OID, "MDV.CDISC01.SDTMIG.3.1.2.SDTM.1.2")
        print(f"ItemRefs = {len(odm2.Study[0].MetaDataVersion.ItemGroupDef[1])}")
        self.assertEqual(len(odm2.Study[0].MetaDataVersion.ItemGroupDef[1]), 6)