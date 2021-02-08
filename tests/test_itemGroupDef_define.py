from unittest import TestCase
import json
import odmlib.define_2_0.model as DEFINE
import odmlib.odm_parser as ODM_PARSER
import xml.etree.ElementTree as ET
import odmlib.ns_registry as NS
import os
import datetime


class TestItemGroupDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_itemgroupdef_attributes()
        self.igd = DEFINE.ItemGroupDef(**attrs)
        self.test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'define2-0-0-sdtm-test.xml')
        self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        self.nsr = NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")

    def test_item_group_valid_kwargs_only(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        self.assertEqual(igd.OID, "IG.VS")

    def test_add_description(self):
        tt1 = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = DEFINE.TranslatedText(_content="this is the second test description", lang="en")
        self.igd.Description = DEFINE.Description()
        self.igd.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.igd.Description.TranslatedText), 2)
        self.assertEqual(self.igd.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_item_ref(self):
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1))
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2))
        self.igd.ItemRef.append(DEFINE.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="Yes", OrderNumber=3, MethodOID="MT.METHODFEX"))
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.STUDYID")
        self.assertEqual(self.igd.ItemRef[2].MethodOID, "MT.METHODFEX")

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

    def test_to_json(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="this is the first test description", lang="en")
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText = [tt]
        ir1 = DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        ir2 = DEFINE.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        igd.ItemRef = [ir1, ir2]
        igd_json = igd.to_json()
        igd_dict = json.loads(igd_json)
        print(igd_dict)
        self.assertEqual(igd_dict["OID"], "IG.VS")
        self.assertEqual(igd_dict["ItemRef"][1]["ItemOID"], "IT.VS.VSTEST")

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

    def test_itemgroupdef_round_trip(self):
        """ system test to create and serialize an ItemGroupDef object """
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.test_file, self.nsr)
        parser.parse()
        mdv = parser.MetaDataVersion()
        igd_list = parser.ItemGroupDef(parent=mdv[0])
        igd_dict = igd_list[0]
        self.assertEqual(igd_dict["OID"], "IG.TA")
        ir_list = parser.ItemRef(parent=igd_dict["elem"])
        # tests the __len__ in ItemGroupDef as well as the add_item_ref
        self.assertEqual(len(ir_list), len(igd))

    def test_itemgroupdef_slice(self):
        """ test the ability to reference a specific or slice of ItemRefs """
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.test_file, self.nsr)
        parser.parse()
        parser.MetaDataVersion()
        self.assertEqual(len(igd), 10)
        self.assertEqual(igd.ItemRef[0].ItemOID, "IT.STUDYID")
        slice_itr = igd.ItemRef[1:5]
        self.assertEqual(slice_itr[1].ItemOID, "IT.TA.ARMCD")

    def test_itemgroupdef_iterator(self):
        """ test the ability to reference a specific or slice of ItemRefs """
        attrs = self.set_itemgroupdef_attributes()
        igd = DEFINE.ItemGroupDef(**attrs)
        tt = DEFINE.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.test_file, self.nsr)
        parser.parse()
        parser.MetaDataVersion()
        irs = [ir.ItemOID for ir in igd]
        self.assertEqual(len(irs), 10)

    def add_itemrefs(self, igd, item_refs):
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

    def set_itemgroupdef_attributes(self):
        """
        set some ItemGroupDef element attributes using test data
        :return: dictionary with ItemGroupDef attribute information
        """
        return {"OID": "IG.VS", "Name": "VS", "Repeating": "Yes", "Domain": "VS", "Name": "VS", "SASDatasetName": "VS",
                "IsReferenceData": "No", "Purpose": "Tabulation", "Class": "FINDINGS", "ArchiveLocationID": "LF.VS",
                "Structure": "One record per vital sign measurement per visit per subject"}


    def set_itemrefs(self):
        """
        set some ItemRef element attributes using test data
        :return: return a list of ItemRef named tuples
        """
        itemrefs = []
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1, KeySequence=1))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.DOMAIN", Mandatory="Yes", OrderNumber=2))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.ARMCD", Mandatory="Yes", OrderNumber=3, KeySequence=2))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.ARM", Mandatory="Yes", OrderNumber=4))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.TAETORD", Mandatory="Yes", OrderNumber=5, KeySequence=3))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.ETCD", Mandatory="Yes", OrderNumber=6))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.ELEMENT", Mandatory="No", OrderNumber=7))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.TABRANCH", Mandatory="No", OrderNumber=8))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.TATRANS", Mandatory="No", OrderNumber=9))
        itemrefs.append(DEFINE.ItemRef(ItemOID="IT.TA.EPOCH", Mandatory="No", OrderNumber=10))
        return itemrefs


    def create_odm_document(self, igd):
        """
        assemble the ODM document, add the ItemGroupDef, and write it to a file
        :param igd: ItemGroupDef object
        """
        odm_elem = self.create_root().to_xml()
        study_elem = self.create_study().to_xml()
        odm_elem.insert(0, study_elem)
        mdv_elem = self.create_mdv().to_xml()
        study_elem.insert(1, mdv_elem)
        igd_elem = igd.to_xml()
        mdv_elem.insert(1, igd_elem)
        self.write_odm_file(odm_elem, self.odm_test_file)
        return odm_elem


    def create_root(self):
        """
        create the ODM root element object with test data
        :return: ODM root element object
        """
        root = {"xmlns:def": "http://www.cdisc.org/ns/def/v2.1", "Granularity": "Metadata", "AsOfDateTime": self.set_datetime(),
                "CreationDateTime": self.set_datetime(), "ODMVersion": "1.3.2", "Originator": "CDISC 360", "SourceSystem": "WS2",
                "SourceSystemVersion": "0.1", "def:Context": "Other"}
        root = DEFINE.ODM("DEFINE.TEST.IGD.001", **root)
        return root


    def create_study(self):
        """
        create the ODM Study object instantiated with test data
        :return: ODM Study element object
        """
        study = DEFINE.Study("ST.TEST.IGD.001")
        study.StudyName = "TEST ODM ItemGroupDef"
        study.StudyDescription = "ItemGroupDef 001"
        study.ProtocolName = "ODM ItemGroupDef"
        return study


    def create_mdv(self):
        """
        create the ODM MetaDataVersion object instantiated with test data
        :return: ODM MetaDataVersion element object
        """
        mdv = DEFINE.MetaDataVersion("MDV.TEST.IGD.001", "ItemGroupDefTest001", "ItemGroupDef Test 001",
                                                  "2.1.0")
        return mdv


    def write_odm_file(self, odm, odm_file):
        """
        write the ODM document to a file
        :param odm: ODM document
        :param odm_file: path and name of ODM file to write ODM document to
        """
        tree = ET.ElementTree(odm)
        tree.write(odm_file, xml_declaration=True)


    def set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
