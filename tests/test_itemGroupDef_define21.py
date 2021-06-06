from unittest import TestCase
import odmlib.define_2_1.model as DEFINE
import odmlib.odm_parser as ODM_PARSER
import xml.etree.ElementTree as ET
import odmlib.ns_registry as NS
import odmlib.define_loader as OL
import odmlib.loader as LD
import os
import datetime


class TestItemGroupDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_itemgroupdef_attributes()
        self.igd = DEFINE.ItemGroupDef(**attrs)
        self.test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM-test.xml')
        self.test_file_json = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM-test.json')
        self.input_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM.xml')
        self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        self.nsr = NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")

    def test_context(self):
        odm = DEFINE.ODM(
            FileOID="DEFINE.TEST.IGD.001", FileType="Snapshot", AsOfDateTime=self.set_datetime(),
            CreationDateTime=self.set_datetime(), ODMVersion="1.3.2", Originator="CDISC 360", SourceSystem="WS2",
            SourceSystemVersion="0.1", Context="Other"
        )
        self.assertEqual(odm.Context, "Other")

    def test_standards(self):
        mdv = self.create_mdv()
        mdv.Standards = DEFINE.Standards()
        std1 = DEFINE.Standard(OID="STD.1", Name="SDTMIG", Type="IG", Version="3.1.2", Status="Final", CommentOID="COM.STD1")
        mdv.Standards.Standard.append(std1)
        std2 = DEFINE.Standard(OID="STD.2", Name="CDISC/NCI", Type="CT", PublishingSet="SDTM", Version="2011-12-09", Status="Final")
        mdv.Standards.Standard.append(std2)
        self.assertEqual(mdv.Standards.Standard[0].Name, "SDTMIG")
        self.assertEqual(mdv.Standards.Standard[1].Version, "2011-12-09")

    def test_add_class(self):
        def_class = DEFINE.Class(Name="FINDINGS")
        def_class.SubClass.append(DEFINE.SubClass(Name="SUBFINDINGS", ParentClass="FINDINGS"))
        self.igd.Class = def_class
        self.assertEqual(self.igd.Class.Name, "FINDINGS")
        self.assertEqual(self.igd.Class.SubClass[0].ParentClass, "FINDINGS")

    def test_add_description(self):
        tt1 = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = DEFINE.TranslatedText(_content="this is the second test description", lang="en")
        self.igd.Description = DEFINE.Description()
        self.igd.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.igd.Description.TranslatedText), 2)
        self.assertEqual(self.igd.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_item_ref(self):
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1, IsNonStandard="Yes"))
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2, HasNoData="Yes"))
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="Yes", OrderNumber=3, MethodOID="MT.METHODFEX"))
        self.assertEqual(self.igd.ItemRef[0].IsNonStandard, "Yes")
        self.assertEqual(self.igd.ItemRef[1].HasNoData, "Yes")

    def test_add_item_ref_list(self):
        ir1 = DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        self.igd.ItemRef.append(ir1)
        ir2 = DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        self.igd.ItemRef.append(ir2)
        ir3 = DEFINE.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="Yes", OrderNumber=3, MethodOID="MT.METHODFEX")
        self.igd.ItemRef.append(ir3)
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.STUDYID")
        self.assertEqual(self.igd.ItemRef[2].MethodOID, "MT.METHODFEX")

    def test_add_item_ref_missing_kwarg(self):
        with self.assertRaises(ValueError):
            self.igd.ItemRef = [DEFINE.ItemRef(Mandatory="Yes", OrderNumber=1)]

    def test_add_item_ref_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            self.igd.ItemRef = [DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", InValid="Yes")]

    def test_item_ref_exists(self):
        self.igd.ItemRef = [DEFINE.ItemRef(ItemOID="IT.VS.VSTESTCD", Mandatory="Yes", OrderNumber=4)]
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.VS.VSTESTCD")

    def test_add_alias(self):
        a1 = DEFINE.Alias(Context="SDTMIG", Name="VSORRES")
        a2 = DEFINE.Alias(Context="SDTMIG", Name="VSTESTCD")
        self.igd.Alias = [a1, a2]
        self.assertEqual(len(self.igd.Alias), 2)
        self.assertEqual(self.igd.Alias[1].Name, "VSTESTCD")

    def test_to_xml(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText = [tt]
        igd.Description = desc
        ir1 = DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        ir2 = DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        igd.ItemRef = [ir1, ir2]
        igd_xml = igd.to_xml()
        self.assertEqual(igd_xml.attrib["OID"], "IG.VS")
        self.assertListEqual(["Description", "ItemRef", "ItemRef"], [e.tag for e in igd_xml.getchildren()])

    def test_itemgroupdef_parse_xml(self):
        parser = ODM_PARSER.ODMParser(self.input_file, self.nsr)
        parser.parse()
        mdv = parser.MetaDataVersion()
        igd_list = parser.ItemGroupDef(parent=mdv[0])
        igd_dict = igd_list[0]
        self.assertEqual(igd_dict["OID"], "IG.TS")
        ir_list = parser.ItemRef(parent=igd_dict["elem"])
        # tests the __len__ in ItemGroupDef as well as the add_item_ref
        self.assertEqual(len(ir_list), 6)
        igd_class = parser.Class(parent=igd_dict["elem"], ns_prefix="def")
        self.assertEqual(igd_class[0]["Name"], "TRIAL DESIGN")

    def test_write_xml(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText = [tt]
        igd.Description = desc
        ir_list = self.set_itemrefs()
        igd.ItemRef = ir_list
        self.create_odm_document(igd)
        loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
        loader.open_odm_document(self.test_file)
        mdv = loader.MetaDataVersion()

        igd_list = mdv.ItemGroupDef
        igd = igd_list[0]
        self.assertEqual(igd.OID, "IG.VS")
        # tests the __len__ in ItemGroupDef
        self.assertEqual(len(igd.ItemRef), 10)

    def test_write_json(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        desc = DEFINE.Description()
        desc.TranslatedText = [tt]
        igd.Description = desc
        ir_list = self.set_itemrefs()
        igd.ItemRef = ir_list
        self.create_odm_document_json(igd)
        loader = LD.ODMLoader(OL.JSONDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.test_file_json)
        mdv = loader.MetaDataVersion()

        igd_list = mdv.ItemGroupDef
        igd = igd_list[0]
        self.assertEqual(igd.OID, "IG.VS")
        # tests the __len__ in ItemGroupDef
        self.assertEqual(len(igd.ItemRef), 10)

    @staticmethod
    def add_itemrefs(igd, item_refs):
        """
        add ItemRefs to the ItemGroupDef object
        :param igd: ItemGroupDef object
        :param item_refs: list of ItemRef dictionaries containing ItemRef attributes
        """
        for it in item_refs:
            attrs = {"ItemOID": it.oid, "Mandatory": it.mandatory, "OrderNumber": it.order_number}
            if it.key_sequence:
                attrs["KeySequence"] = it.key_sequence
            if it.method:
                attrs["MethodOID"] = it.method
            igd.add_item_ref(**attrs)

    @staticmethod
    def set_itemgroupdef_attributes():
        """
        set some ItemGroupDef element attributes using test data
        :return: dictionary with ItemGroupDef attribute information
        """
        return {"OID": "IG.VS", "Name": "VS", "Repeating": "Yes", "Domain": "VS", "SASDatasetName": "VS",
                "IsReferenceData": "No", "Purpose": "Tabulation", "ArchiveLocationID": "LF.VS",
                "Structure": "One record per vital sign measurement per visit per subject", "StandardOID": "STD.1",
                "IsNonStandard": "Yes", "HasNoData": "Yes"}

    @staticmethod
    def set_itemrefs():
        """
        set some ItemRef element attributes using test data
        :return: return a list of ItemRef named tuples
        """
        itemrefs = [
            DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1, KeySequence=1),
            DEFINE.ItemRef(ItemOID="IT.TA.DOMAIN", Mandatory="Yes", OrderNumber=2),
            DEFINE.ItemRef(ItemOID="IT.TA.ARMCD", Mandatory="Yes", OrderNumber=3, KeySequence=2),
            DEFINE.ItemRef(ItemOID="IT.TA.ARM", Mandatory="Yes", OrderNumber=4),
            DEFINE.ItemRef(ItemOID="IT.TA.TAETORD", Mandatory="Yes", OrderNumber=5, KeySequence=3),
            DEFINE.ItemRef(ItemOID="IT.TA.ETCD", Mandatory="Yes", OrderNumber=6),
            DEFINE.ItemRef(ItemOID="IT.TA.ELEMENT", Mandatory="No", OrderNumber=7),
            DEFINE.ItemRef(ItemOID="IT.TA.TABRANCH", Mandatory="No", OrderNumber=8),
            DEFINE.ItemRef(ItemOID="IT.TA.TATRANS", Mandatory="No", OrderNumber=9),
            DEFINE.ItemRef(ItemOID="IT.TA.EPOCH", Mandatory="No", OrderNumber=10)
        ]
        return itemrefs

    def create_odm_document(self, igd):
        """
        assemble the ODM document, add the ItemGroupDef, and write it to a file
        :param igd: ItemGroupDef object
        """
        odm = self.create_root()
        study = self.create_study()
        odm.Study = [study]
        mdv = self.create_mdv()
        odm.Study[0].MetaDataVersion = [mdv]
        odm.Study[0].MetaDataVersion[0].ItemGroupDef.append(igd)
        odm.write_xml(self.test_file)
        return odm

    def create_odm_document_json(self, igd):
        """
        assemble the ODM document, add the ItemGroupDef, and write it to a file
        :param igd: ItemGroupDef object
        """
        odm = self.create_root()
        study = self.create_study()
        odm.Study = [study]
        mdv = self.create_mdv()
        odm.Study[0].MetaDataVersion = [mdv]
        odm.Study[0].MetaDataVersion[0].ItemGroupDef.append(igd)
        odm.write_json(self.test_file_json)
        return odm

    def create_root(self):
        """
        create the ODM root element object with test data
        :return: ODM root element object
        """
        root = {"FileOID": "DEFINE.TEST.IGD.001", "FileType": "Snapshot", "AsOfDateTime": self.set_datetime(),
                "CreationDateTime": self.set_datetime(), "ODMVersion": "1.3.2", "Originator": "CDISC 360", "SourceSystem": "WS2",
                "SourceSystemVersion": "0.1", "Context": "Other"}
        root = DEFINE.ODM(**root)
        return root


    @staticmethod
    def create_study():
        """
        create the ODM Study object instantiated with test data
        :return: ODM Study element object
        """
        study = DEFINE.Study(OID="ST.TEST.IGD.001")
        study.GlobalVariables.StudyName = DEFINE.StudyName(_content="TEST ODM ItemGroupDef")
        study.GlobalVariables.StudyDescription = DEFINE.StudyDescription(_content="ItemGroupDef 001")
        study.GlobalVariables.ProtocolName = DEFINE.ProtocolName(_content="ODM ItemGroupDef")
        return study


    @staticmethod
    def create_mdv():
        """
        create the ODM MetaDataVersion object instantiated with test data
        :return: ODM MetaDataVersion element object
        """
        mdv = DEFINE.MetaDataVersion(OID="MDV.TEST.IGD.001", Name="ItemGroupDefTest001",
                                     Description="ItemGroupDef Test 001", DefineVersion="2.1.0")
        return mdv


    @staticmethod
    def write_odm_file(odm, odm_file):
        """
        write the ODM document to a file
        :param odm: ODM document
        :param odm_file: path and name of ODM file to write ODM document to
        """
        tree = ET.ElementTree(odm)
        tree.write(odm_file, xml_declaration=True)


    @staticmethod
    def set_datetime():
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
