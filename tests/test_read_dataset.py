import unittest
import odmlib.odm_loader as OL
import odmlib.ns_registry as NS
import os


class TestReadDataset(unittest.TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'ae_test.xml')
        self.loader = OL.XMLODMLoader(model_package="dataset_1_0_1", ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        self.ns = NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    def test_open_odm_document(self):
        self.loader.create_document(self.odm_file, self.ns)
        self.odm = self.loader.load_odm()
        self.assertEqual(self.odm.FileOID, "ODM.DATASET.001")
        self.assertEqual(self.odm.ClinicalData.ItemGroupData[0].ItemGroupOID, "IG.AE")
        self.assertEqual(self.odm.ClinicalData.ItemGroupData[0].ItemData[2].Value, "CDISC01.100008")
        self.assertEqual(self.odm.ClinicalData.ItemGroupData[1].ItemData[4].Value, "ANXIETY")

    def test_dataset_iterator(self):
        self.loader.create_document(self.odm_file, self.ns)
        self.odm = self.loader.load_odm()
        test_values = self._get_igd_values()
        values = []
        for item in self.odm.ClinicalData.ItemGroupData[1]:
            values.append(item.Value)
        self.assertListEqual(values, test_values)


    def _get_igd_values(self):
        return ["CDISC01", "AE", "CDISC01.100008", "2", "ANXIETY", "AGITATION", "Anxiety", "MODERATE", "N",
                "DOSE NOT CHANGED", "POSSIBLY RELATED"]


if __name__ == '__main__':
    unittest.main()
