from unittest import TestCase
import odmlib.define_loader as OL
import odmlib.loader as LD
import os


class TestODMLoader(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'define2-0-0-sdtm-test.xml')
        self.odm_file_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'sdtm_define2_test.json')
        self.loader = LD.ODMLoader(OL.XMLDefineLoader())
        self.jloader = LD.ODMLoader(OL.JSONDefineLoader())

    def test_unknown_loader(self):
        with self.assertRaises(TypeError):
            loader = LD.ODMLoader(self.test_mdv_find_by_OID())

    def test_open_odm_document(self):
        root = self.loader.open_odm_document(self.odm_file)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("www.cdisc.org.Studycdisc01-Define-XML_2.0.0", root.attrib["FileOID"])

    def test_load_odm(self):
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.load_odm()
        self.assertEqual("www.cdisc.org.Studycdisc01-Define-XML_2.0.0", odm.FileOID)

    def test_load_missing(self):
        root = self.loader.open_odm_document(self.odm_file)
        with self.assertRaises(AttributeError):
            odm = self.loader.load_standard()

    def test_load_study(self):
        root = self.loader.open_odm_document(self.odm_file)
        study = self.loader.load_study()
        self.assertEqual("cdisc01", study.OID)

    def test_load_doc_from_string_json(self):
        with open(self.odm_file_json, 'r') as file:
            json_string = file.read()
        odm = self.jloader.create_document_from_string(json_string)
        self.assertEqual("www.cdisc.org.Studycdisc01-Define-XML_2.0.0", odm["FileOID"])

    def test_load_odm_json(self):
        root = self.jloader.open_odm_document(self.odm_file_json)
        odm = self.jloader.load_odm()
        self.assertEqual("www.cdisc.org.Studycdisc01-Define-XML_2.0.0", odm.FileOID)

    def test_load_study_json(self):
        root = self.jloader.open_odm_document(self.odm_file_json)
        study = self.jloader.load_study()
        self.assertEqual("cdisc01", study.OID)
        study = self.jloader.Study()
        self.assertEqual("cdisc01", study.OID)

    def test_meta_data_version(self):
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC01, Data Definitions")
        self.assertEqual(mdv.ValueListDef[0].OID, "VL.DA.DAORRES")
        self.assertEqual(mdv.ItemDef[0].CodeListRef.CodeListOID, "CL.ACN")
        self.assertEqual(mdv.CodeList[1].CodeListItem[0].CodedValue, "AE")
        self.assertEqual(mdv.CommentDef[0].OID, "COM.AGEU")

    def test_meta_data_version_json(self):
        self.jloader.open_odm_document(self.odm_file_json)
        mdv = self.jloader.load_metadataversion()
        self.assertEqual(mdv.Name, "Study CDISC01, Data Definitions")
        self.assertEqual(mdv.ValueListDef[0].OID, "VL.DA.DAORRES")
        self.assertEqual(mdv.ItemDef[0].CodeListRef.CodeListOID, "CL.ACN")
        self.assertEqual(mdv.CodeList[1].CodeListItem[0].CodedValue, "AE")
        self.assertEqual(mdv.CommentDef[0].OID, "COM.AGEU")

    def test_mdv_find_by_OID(self):
        self.loader.open_odm_document(self.odm_file)
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
        root = self.loader.open_odm_document(self.odm_file)
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