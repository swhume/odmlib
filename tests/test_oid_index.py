import unittest
import odmlib.odm_loader as OL
import odmlib.define_loader as DL
import odmlib.loader as LD
import os
import odmlib.oid_index as IDX


class TestOIDIndex(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        self.loader = LD.ODMLoader(OL.XMLODMLoader())
        self.loader.open_odm_document(self.odm_file)
        self.odm = self.loader.root()

    def test_oid_index_find_item(self):
        idx = self.odm.build_oid_index()
        found = idx.find_all("ODM.IT.DM.SEX")
        self.assertEqual(len(found), 2)
        self.assertEqual(found[0].ItemOID, "ODM.IT.DM.SEX")
        self.assertEqual(found[1].OID, "ODM.IT.DM.SEX")

    def test_oid_index_find_codelist(self):
        idx = self.odm.build_oid_index()
        found = idx.find_all("ODM.CL.NY_SUB_Y_N")
        self.assertEqual(len(found), 7)
        self.assertEqual(found[6].OID, "ODM.CL.NY_SUB_Y_N")
        self.assertEqual(found[1].CodeListOID, "ODM.CL.NY_SUB_Y_N")

    def test_oid_index_define_igd(self):
        self.define_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'defineV21-SDTM.xml')
        self.loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
        self.loader.open_odm_document(self.define_file)
        self.odm = self.loader.root()
        idx = self.odm.build_oid_index()
        found = idx.find_all("IG.VS")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].ItemRef[2].ItemOID, "IT.USUBJID")
        self.assertEqual(found[0].ItemRef[5].ItemOID, "IT.VS.VSTEST")
        it_found = idx.find_all("IT.EX.EXSTDTC")
        self.assertEqual(len(it_found), 2)
        self.assertEqual(it_found[1].Name, "EXSTDTC")

    def test_without_oid_index_build(self):
        idx = IDX.OIDIndex()
        with self.assertRaises(ValueError):
            found = idx.find_all("ODM.CL.NY_SUB_Y_N")

    def test_not_found(self):
        idx = self.odm.build_oid_index()
        with self.assertRaises(ValueError):
            found = idx.find_all("ODM.CL.XXXX")
