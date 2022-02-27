import unittest
import os
import odmlib.odm_parser as P
import odmlib.ns_registry as NS
import odmlib.define_loader as OL
import odmlib.loader as LD

ODM_NS = "{http://www.cdisc.org/ns/odm/v1.3}"


class TestDefine21LoaderMetaData(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM-metadata.xml')
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        self.nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        self.parser = P.ODMParser(self.odm_file_1, self.nsr)
        self.loader = LD.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
        self.root = self.loader.create_document(self.odm_file_1)
        self.odm = self.loader.load_odm()
        self.parser.parse()
        self.mdv = self.parser.MetaDataVersion()

    def test_MetaDataVersion(self):
        self.assertTrue(isinstance(self.mdv, list))
        # elementree does not support using the suffix for accessing attributes not in the default ns
        mdv_dict = {"OID": "MDV.CDISC01_1.1.SDTMIG.3.1.2.SDTM.1.2_X",
                    "Name": "Study CDISC01_1, Data Definitions V-1",
                    "Description": "Data Definitions for CDISC01-01 SDTM datasets. This metadata version contains only a subset of datasets compared to the prior version.",
                    "{http://www.cdisc.org/ns/def/v2.1}DefineVersion": "2.1.0"}
        self.assertDictEqual(self.mdv[0].attrib, mdv_dict)
        self.assertEqual(mdv_dict["{http://www.cdisc.org/ns/def/v2.1}DefineVersion"],
                         self.mdv[0].attrib["{http://www.cdisc.org/ns/def/v2.1}DefineVersion"])
        # self.assertEqual(769, len([e.tag for e in self.mdv[0].getchildren()]))

    def test_Standards(self):
        # self.assertTrue(isinstance(self.mdv[0].Standards.Standard, list))
        # elementree does not support using the suffix for accessing attributes not in the default ns
        mdv = self.odm.Study.MetaDataVersion
        self.assertEqual(mdv.Standards.Standard[0].OID, "STD.1")

    # def test_ItemGroupDef(self):
    #     ig = self.parser.ItemGroupDef(parent=self.mdv[0])
    #     self.assertEqual(len(ig), 34)
    #     dm_itg = {"OID": "IG.DM", "Domain": "DM", "Name": "DM", "Repeating": "No", "IsReferenceData": "No",
    #               "SASDatasetName": "DM", "Purpose": "Tabulation",
    #               "{http://www.cdisc.org/ns/def/v2.0}Structure": "One record per subject",
    #               "{http://www.cdisc.org/ns/def/v2.0}Class": "SPECIAL PURPOSE",
    #               "{http://www.cdisc.org/ns/def/v2.0}CommentOID": "COM.DOMAIN.DM",
    #               "{http://www.cdisc.org/ns/def/v2.0}ArchiveLocationID": "LF.DM"}
    #     self.assertDictEqual(dm_itg, ig[5]['elem'].attrib)
    #     self.assertEqual(ig[4]["{http://www.cdisc.org/ns/def/v2.0}ArchiveLocationID"], "LF.TV")
    #
    # def test_ItemGroupDef_nsr(self):
    #     ig = self.parser.ItemGroupDef(parent=self.mdv[0])
    #     self.assertEqual(len(ig), 34)
    #     dm_itg = {"OID": "IG.DM", "Domain": "DM", "Name": "DM", "Repeating": "No", "IsReferenceData": "No",
    #               "SASDatasetName": "DM", "Purpose": "Tabulation",
    #               self.nsr.get_ns_attribute_name("Structure", "def"): "One record per subject",
    #               self.nsr.get_ns_attribute_name("Class", "def"): "SPECIAL PURPOSE",
    #               self.nsr.get_ns_attribute_name("CommentOID", "def"): "COM.DOMAIN.DM",
    #               self.nsr.get_ns_attribute_name("ArchiveLocationID", "def"): "LF.DM"}
    #     self.assertDictEqual(dm_itg, ig[5]['elem'].attrib)
    #     self.assertEqual(ig[4][self.nsr.get_ns_attribute_name("ArchiveLocationID", "def")], "LF.TV")
    #
    # def test_ItemRef(self):
    #     ig = self.parser.ItemGroupDef(parent=self.mdv[0])
    #     ir = self.parser.ItemRef(parent=ig[0]['elem'])
    #     self.assertEqual(len(ir), 10)
    #     self.assertDictEqual({'ItemOID': 'IT.TA.ARMCD', 'Mandatory': 'Yes', "OrderNumber": "3", "KeySequence": "2"},
    #                          ir[2]['elem'].attrib)
    #
    # def test_ValueListDef(self):
    #     # test using an element from the define-xml v2.0 namespace
    #     vld = self.parser.ValueListDef(parent=self.mdv[0], ns_prefix="def")
    #     self.assertEqual(len(vld), 19)
    #     self.assertDictEqual({'OID': 'VL.DA.DAORRES'}, vld[0]['elem'].attrib)
    #     # now back to retrieving an element from the Define-XML doc that exists in the ODM namespace
    #     ir_list = self.parser.ItemRef(parent=vld[0]['elem'])
    #     self.assertEqual(len(ir_list), 2)
    #     wc = self.parser.WhereClauseRef(parent=ir_list[0]['elem'], ns_prefix="def")
    #     self.assertEqual(wc[0]["WhereClauseOID"], "WC.DA.DATESTCD.DISPAMT")


if __name__ == '__main__':
    unittest.main()
