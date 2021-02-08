import unittest
import os
import odmlib.odm_parser as P
import odmlib.ns_registry as NS

ODM_NS = "{http://www.cdisc.org/ns/odm/v1.3}"


class TestOdmParserMetaData(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'define2-0-0-sdtm-test.xml')
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        self.nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        self.parser = P.ODMParser(self.odm_file_1, self.nsr)
        self.root = self.parser.parse()
        self.mdv = self.parser.MetaDataVersion()

    def test_MetaDataVersion(self):
        self.assertTrue(isinstance(self.mdv, list))
        # elementree does not support using the suffix for accessing attributes not in the default ns
        mdv_dict = {"OID": "MDV.CDISC01.SDTMIG.3.1.2.SDTM.1.2", "Name": "Study CDISC01, Data Definitions",
                    "Description": "Study CDISC01, Data Definitions",
                    "{http://www.cdisc.org/ns/def/v2.0}DefineVersion": "2.0.0",
                    "{http://www.cdisc.org/ns/def/v2.0}StandardName": "SDTM-IG",
                    "{http://www.cdisc.org/ns/def/v2.0}StandardVersion": "3.1.2"}
        self.assertDictEqual(self.mdv[0].attrib, mdv_dict)
        self.assertEqual(mdv_dict["{http://www.cdisc.org/ns/def/v2.0}DefineVersion"],
                         self.mdv[0].attrib["{http://www.cdisc.org/ns/def/v2.0}DefineVersion"])
        self.assertEqual(769, len([e.tag for e in self.mdv[0].getchildren()]))

    def test_ItemGroupDef(self):
        ig = self.parser.ItemGroupDef(parent=self.mdv[0])
        self.assertEqual(len(ig), 34)
        dm_itg = {"OID": "IG.DM", "Domain": "DM", "Name": "DM", "Repeating": "No", "IsReferenceData": "No",
                  "SASDatasetName": "DM", "Purpose": "Tabulation",
                  "{http://www.cdisc.org/ns/def/v2.0}Structure": "One record per subject",
                  "{http://www.cdisc.org/ns/def/v2.0}Class": "SPECIAL PURPOSE",
                  "{http://www.cdisc.org/ns/def/v2.0}CommentOID": "COM.DOMAIN.DM",
                  "{http://www.cdisc.org/ns/def/v2.0}ArchiveLocationID": "LF.DM"}
        self.assertDictEqual(dm_itg, ig[5]['elem'].attrib)
        self.assertEqual(ig[4]["{http://www.cdisc.org/ns/def/v2.0}ArchiveLocationID"], "LF.TV")

    def test_ItemGroupDef_nsr(self):
        ig = self.parser.ItemGroupDef(parent=self.mdv[0])
        self.assertEqual(len(ig), 34)
        dm_itg = {"OID": "IG.DM", "Domain": "DM", "Name": "DM", "Repeating": "No", "IsReferenceData": "No",
                  "SASDatasetName": "DM", "Purpose": "Tabulation",
                  self.nsr.get_ns_attribute_name("Structure", "def"): "One record per subject",
                  self.nsr.get_ns_attribute_name("Class", "def"): "SPECIAL PURPOSE",
                  self.nsr.get_ns_attribute_name("CommentOID", "def"): "COM.DOMAIN.DM",
                  self.nsr.get_ns_attribute_name("ArchiveLocationID", "def"): "LF.DM"}
        self.assertDictEqual(dm_itg, ig[5]['elem'].attrib)
        self.assertEqual(ig[4][self.nsr.get_ns_attribute_name("ArchiveLocationID", "def")], "LF.TV")

    def test_ItemRef(self):
        ig = self.parser.ItemGroupDef(parent=self.mdv[0])
        ir = self.parser.ItemRef(parent=ig[0]['elem'])
        self.assertEqual(len(ir), 10)
        self.assertDictEqual({'ItemOID': 'IT.TA.ARMCD', 'Mandatory': 'Yes', "OrderNumber": "3", "KeySequence": "2"},
                             ir[2]['elem'].attrib)

    def test_ValueListDef(self):
        # test using an element from the define-xml v2.0 namespace
        vld = self.parser.ValueListDef(parent=self.mdv[0], ns_prefix="def")
        self.assertEqual(len(vld), 19)
        self.assertDictEqual({'OID': 'VL.DA.DAORRES'}, vld[0]['elem'].attrib)
        # now back to retrieving an element from the Define-XML doc that exists in the ODM namespace
        ir_list = self.parser.ItemRef(parent=vld[0]['elem'])
        self.assertEqual(len(ir_list), 2)
        wc = self.parser.WhereClauseRef(parent=ir_list[0]['elem'], ns_prefix="def")
        self.assertEqual(wc[0]["WhereClauseOID"], "WC.DA.DATESTCD.DISPAMT")


if __name__ == '__main__':
    unittest.main()
