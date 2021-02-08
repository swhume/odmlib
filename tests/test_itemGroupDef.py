from unittest import TestCase
import json
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_parser as ODM_PARSER
import xml.etree.ElementTree as ET
import os
import datetime


class TestItemGroupDef(TestCase):
    def setUp(self) -> None:
        attrs = self.set_itemgroupdef_attributes()
        self.igd = ODM.ItemGroupDef(**attrs)
        self.odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_igd_001.xml')

    def test_item_group_valid_kwargs_only(self):
        igd = ODM.ItemGroupDef(OID="IG.VS", Name="VS", Repeating="Yes")
        self.assertEqual(igd.OID, "IG.VS")

    def test_add_description(self):
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        tt2 = ODM.TranslatedText(_content="this is the second test description", lang="en")
        self.igd.Description = ODM.Description()
        self.igd.Description.TranslatedText = [tt1, tt2]
        self.assertEqual(len(self.igd.Description.TranslatedText), 2)
        self.assertEqual(self.igd.Description.TranslatedText[1]._content, 'this is the second test description')

    def test_add_item_ref(self):
        self.igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1))
        self.igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2))
        self.igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="Yes", OrderNumber=3, MethodOID="MT.METHODFEX"))
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.STUDYID")
        self.assertEqual(self.igd.ItemRef[2].MethodOID, "MT.METHODFEX")

    def test_add_item_ref_list(self):
        ir1 = ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        self.igd.ItemRef.append(ir1)
        ir2 = ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        self.igd.ItemRef.append(ir2)
        ir3 = ODM.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="Yes", OrderNumber=3, MethodOID="MT.METHODFEX")
        self.igd.ItemRef.append(ir3)
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.STUDYID")
        self.assertEqual(self.igd.ItemRef[2].MethodOID, "MT.METHODFEX")

    def test_add_item_ref_missing_kwarg(self):
        with self.assertRaises(ValueError):
            self.igd.ItemRef = [ODM.ItemRef(Mandatory="Yes", OrderNumber=1)]

    def test_add_item_ref_invalid_kwarg(self):
        with self.assertRaises(TypeError):
            self.igd.ItemRef = [ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", InValid="Yes")]

    def test_item_ref_exists(self):
        self.igd.ItemRef = [ODM.ItemRef(ItemOID="IT.VS.VSTESTCD", Mandatory="Yes", OrderNumber=4)]
        self.assertEqual(self.igd.ItemRef[0].ItemOID, "IT.VS.VSTESTCD")

    def test_add_alias(self):
        a1 = ODM.Alias(Context="SDTMIG", Name="VSORRES")
        a2 = ODM.Alias(Context="SDTMIG", Name="VSTESTCD")
        self.igd.Alias = [a1, a2]
        self.assertEqual(len(self.igd.Alias), 2)
        self.assertEqual(self.igd.Alias[1].Name, "VSTESTCD")

    def test_to_json(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="this is the first test description", lang="en")
        igd.Description = ODM.Description()
        igd.Description.TranslatedText = [tt]
        ir1 = ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        ir2 = ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        igd.ItemRef = [ir1, ir2]
        igd_json = igd.to_json()
        igd_dict = json.loads(igd_json)
        print(igd_dict)
        self.assertEqual(igd_dict["OID"], "IG.VS")
        self.assertEqual(igd_dict["ItemRef"][1]["ItemOID"], "IT.VS.VSTEST")

    def test_to_xml(self):
        attrs = self.set_itemgroupdef_attributes()
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="this is the first test description", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt]
        igd.Description = desc
        ir1 = ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1)
        ir2 = ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber=2)
        igd.ItemRef = [ir1, ir2]
        igd_xml = igd.to_xml()
        self.assertEqual(igd_xml.attrib["OID"], "IG.VS")
        self.assertListEqual(["Description", "ItemRef", "ItemRef"], [e.tag for e in igd_xml.getchildren()])

    def test_itemgroupdef_round_trip(self):
        """ system test to create and serialize an ItemGroupDef object """
        attrs = self.set_itemgroupdef_attributes()
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = ODM.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.odm_test_file)
        parser.parse()
        mdv = parser.MetaDataVersion()
        igd_list = parser.ItemGroupDef(parent=mdv[0])
        igd_dict = igd_list[0]
        self.assertEqual(igd_dict["OID"], "IG.VS")
        ir_list = parser.ItemRef(parent=igd_dict["elem"])
        # tests the __len__ in ItemGroupDef as well as the add_item_ref
        self.assertEqual(len(ir_list), len(igd))

    def test_itemgroupdef_slice(self):
        """ test the ability to reference a specific or slice of ItemRefs """
        attrs = self.set_itemgroupdef_attributes()
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = ODM.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.odm_test_file)
        parser.parse()
        parser.MetaDataVersion()
        self.assertEqual(len(igd), 13)
        self.assertEqual(igd.ItemRef[0].ItemOID, "IT.STUDYID")
        slice_itr = igd.ItemRef[1:5]
        self.assertEqual(slice_itr[1].ItemOID, "IT.VS.USUBJID")

    def test_itemgroupdef_iterator(self):
        """ test the ability to reference a specific or slice of ItemRefs """
        attrs = self.set_itemgroupdef_attributes()
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="Vital Signs", lang="en")
        igd.Description = ODM.Description()
        igd.Description.TranslatedText = [tt]
        item_refs = self.set_itemrefs()
        igd.ItemRef = item_refs
        parser = ODM_PARSER.ODMParser(self.odm_test_file)
        parser.parse()
        parser.MetaDataVersion()
        irs = [ir.ItemOID for ir in igd]
        self.assertEqual(len(irs), 13)
        self.assertEqual(len(igd), 13)

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
                "IsReferenceData": "No", "Purpose": "Tabulation"}


    def set_itemrefs(self):
        """
        set some ItemRef element attributes using test data
        :return: return a list of ItemRef named tuples
        """
        itemrefs = []
        itemrefs.append(ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber=1, KeySequence=1))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.DOMAIN", Mandatory="Yes", OrderNumber=2))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.USUBJID", Mandatory="Yes", OrderNumber=3, KeySequence=2, MethodOID="MT.USUBJID"))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSSEQ", Mandatory="Yes", OrderNumber=4, MethodOID="MT.SEQ"))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSTESTCD", Mandatory="Yes", OrderNumber=5, KeySequence=3))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="Yes", OrderNumber=6))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSPOS", Mandatory="No", OrderNumber=7))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSORRES", Mandatory="No", OrderNumber=8))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSORRESU", Mandatory="No", OrderNumber=9))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSSTRESC", Mandatory="No", OrderNumber=10, MethodOID="MT.VSSTRESC"))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSSTRESN", Mandatory="No", OrderNumber=11, MethodOID="MT.VSSTRESN"))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSSTRESU", Mandatory="No", OrderNumber=12))
        itemrefs.append(ODM.ItemRef(ItemOID="IT.VS.VSBLFL", Mandatory="No", OrderNumber=13, MethodOID="MT.VSBLFL"))
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
        root = ODM.odm_root.ODMRoot("ODM.TEST.IGD.001", **root)
        return root


    def create_study(self):
        """
        create the ODM Study object instantiated with test data
        :return: ODM Study element object
        """
        study = ODM.study.Study("ST.TEST.IGD.001")
        study.StudyName = "TEST ODM ItemGroupDef"
        study.StudyDescription = "ItemGroupDef 001"
        study.ProtocolName = "ODM ItemGroupDef"
        return study


    def create_mdv(self):
        """
        create the ODM MetaDataVersion object instantiated with test data
        :return: ODM MetaDataVersion element object
        """
        mdv = ODM.metadataversion.MetaDataVersion("MDV.TEST.IGD.001", "ItemGroupDefTest001", "ItemGroupDef Test 001",
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
