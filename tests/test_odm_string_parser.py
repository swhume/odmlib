import unittest
import os
import odmlib.odm_parser as P
from xml.etree.ElementTree import Element
ODM_NS = "{http://www.cdisc.org/ns/odm/v1.3}"


class TestOdmParserMetaData(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file_1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        with open(self.odm_file_1, "r", encoding="utf-8") as f:
            self.odm_string = f.read()
        self.parser = P.ODMStringParser(self.odm_string)
        self.root = self.parser.parse()
        self.mdv = self.parser.MetaDataVersion()

    def test_MetaDataVersion(self):
        self.assertTrue(isinstance(self.mdv, list))
        self.assertDictEqual(self.mdv[0].attrib, {"Name": "TRACE-XML MDV", "OID": "MDV.TRACE-XML-ODM-01"})
        self.assertEqual(81, len([e.tag for e in self.mdv[0].getchildren()]))

    def test_Protocol(self):
        protocol = self.parser.Protocol(parent=self.mdv[0])
        self.assertIsInstance(protocol[0]["elem"], Element)
        self.assertListEqual([ODM_NS + "StudyEventRef"], [e.tag for e in protocol[0]["elem"].getchildren()])

    def test_StudyEventRef(self):
        protocol = self.parser.Protocol(parent=self.mdv[0])
        ser = self.parser.StudyEventRef(parent=protocol[0]["elem"])
        self.assertEqual(ser[0]["StudyEventOID"], "BASELINE")

    def test_StudyEventDef(self):
        sed = self.parser.StudyEventDef(parent=self.mdv[0])
        self.assertEqual(sed[0]["OID"], "BASELINE")
        self.assertIsInstance(sed[0]["elem"], Element)

    def test_FormRef(self):
        sed = self.parser.StudyEventDef(parent=self.mdv[0])
        fr = self.parser.FormRef(parent=sed[0]["elem"])
        self.assertEqual(fr[0]["FormOID"], "ODM.F.DM")
        fr_list = [ODM_NS + "FormRef", ODM_NS + "FormRef", ODM_NS + "FormRef"]
        self.assertListEqual(fr_list, [e.tag for e in sed[0]["elem"].getchildren()])

    def test_FormDef(self):
        fd = self.parser.FormDef(parent=self.mdv[0])
        self.assertEqual(fd[0]["OID"], "ODM.F.DM")
        self.assertEqual(fd[2]["Name"], "Adverse Event")
        self.assertIsInstance(fd[0]["elem"], Element)

    def test_ItemGroupDef(self):
        ig = self.parser.ItemGroupDef(parent=self.mdv[0])
        self.assertEqual(len(ig), 7)
        self.assertDictEqual({'Name': 'Demographics', 'OID': 'ODM.IG.DM', 'Repeating': 'No'}, ig[1]['elem'].attrib)
        self.assertEqual(ig[3]["OID"], "ODM.IG.VS")

    def test_ItemRef(self):
        ig = self.parser.ItemGroupDef(parent=self.mdv[0])
        ir = self.parser.ItemRef(parent=ig[0]['elem'])
        self.assertEqual(len(ir), 4)
        self.assertDictEqual({'ItemOID': 'ODM.IT.Common.SubjectID', 'Mandatory': 'Yes'}, ir[2]['elem'].attrib)


if __name__ == '__main__':
    unittest.main()
