import unittest
import os
import odmlib.odm_parser as P


class TestOdmParserMetaData(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash_odm_test.json')
        with open(self.odm_file_1, "r", encoding="utf-8") as f:
            self.odm_string = f.read()
        self.parser = P.ODMJSONStringParser(self.odm_string)
        self.root = self.parser.parse()
        self.mdv = self.parser.MetaDataVersion()

    def test_MetaDataVersion(self):
        self.assertTrue(isinstance(self.mdv, list))
        self.assertEqual(self.mdv[0]["Name"], "TRACE-XML MDV")
        self.assertEqual(self.mdv[0]["OID"], "MDV.TRACE-XML-ODM-01")
        self.assertEqual(8, len(self.mdv[0]))

    def test_Protocol(self):
        protocol = self.mdv[0]["Protocol"]
        self.assertIsInstance(protocol['StudyEventRef'], list)
        self.assertEqual(protocol['StudyEventRef'][0]["StudyEventOID"], "BASELINE")

    def test_StudyEventDef(self):
        sed = self.mdv[0]["StudyEventDef"]
        self.assertEqual(sed[0]["OID"], "BASELINE")
        self.assertEqual(sed[0]["Name"], "Baseline Visit")

    def test_FormRef(self):
        fr = self.mdv[0]["StudyEventDef"][0]["FormRef"]
        self.assertEqual(fr[0]["FormOID"], "ODM.F.DM")
        fr_list = ["ODM.F.DM", "ODM.F.VS", "ODM.F.AE"]
        self.assertListEqual(fr_list, [f["FormOID"] for f in fr])

    def test_FormDef(self):
        fd = self.mdv[0]["FormDef"]
        self.assertEqual(fd[0]["OID"], "ODM.F.DM")
        self.assertEqual(fd[2]["Name"], "Adverse Event")

    def test_ItemGroupDef(self):
        ig = self.mdv[0]["ItemGroupDef"]
        self.assertEqual(len(ig), 7)
        self.assertEqual('Demographics', ig[1]['Name'])
        self.assertEqual('ODM.IG.DM', ig[1]['OID'])
        self.assertEqual(ig[3]["OID"], "ODM.IG.VS")


if __name__ == '__main__':
    unittest.main()
