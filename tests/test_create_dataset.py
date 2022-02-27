import unittest
import odmlib.dataset_1_0_1.model as ODM
import datetime
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL


ODM_XML_FILE = "./data/ae_test.xml"
ODM_JSON_FILE = "./data/ae_test.json"

class TestCreateDataset(unittest.TestCase):
    def setUp(self) -> None:
        current_datetime = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
        self.root = ODM.ODM(FileOID="ODM.DATASET.001", AsOfDateTime=current_datetime, DatasetXMLVersion="1.0.0",
                       CreationDateTime=current_datetime, ODMVersion="1.3.2", FileType="Snapshot",
                       Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")

        self.root.ClinicalData = ODM.ClinicalData(StudyOID="cdisc.odmlib.001", MetaDataVersionOID="MDV.001")

        self.root.ClinicalData.ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="1"))
        self._generate_igd_rows_1()
        self.root.ClinicalData.ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="2"))
        self._generate_igd_rows_2()


    def test_write_dataset_xml(self):
        self.root.write_xml(ODM_XML_FILE)
        loader = OL.XMLODMLoader(model_package="dataset_1_0_1", ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        ns = NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        loader.create_document(ODM_XML_FILE, ns)
        odm = loader.load_odm()
        self.assertEqual(odm.FileOID, "ODM.DATASET.001")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemGroupOID, "IG.AE")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemData[2].Value, "CDISC01.100008")
        self.assertEqual(odm.ClinicalData.ItemGroupData[1].ItemData[4].Value, "ANXIETY")

    def test_write_dataset_json(self):
        self.root.write_json(ODM_JSON_FILE)
        loader = OL.JSONODMLoader(model_package="dataset_1_0_1")
        loader.create_document(ODM_JSON_FILE)
        odm = loader.load_odm()
        self.assertEqual(odm.FileOID, "ODM.DATASET.001")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemGroupOID, "IG.AE")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemData[2].Value, "CDISC01.100008")
        self.assertEqual(odm.ClinicalData.ItemGroupData[1].ItemData[4].Value, "ANXIETY")

    def _generate_igd_rows_1(self):
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.DOMAIN", Value="AE"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.USUBJID", Value="CDISC01.100008"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESEQ", Value="1"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AETERM", Value="AGITATED"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEMODIFY", Value="AGITATION"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEDECOD", Value="Agitation"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESEV", Value="MILD"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESER", Value="N"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEACN", Value="DOSE NOT CHANGED"))
        self.root.ClinicalData.ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEREL", Value="POSSIBLY RELATED"))

    def _generate_igd_rows_2(self):
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.DOMAIN", Value="AE"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.USUBJID", Value="CDISC01.100008"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESEQ", Value="2"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AETERM", Value="ANXIETY"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEMODIFY", Value="AGITATION"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEDECOD", Value="Anxiety"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESEV", Value="MODERATE"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AESER", Value="N"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEACN", Value="DOSE NOT CHANGED"))
        self.root.ClinicalData.ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.AE.AEREL", Value="POSSIBLY RELATED"))


if __name__ == '__main__':
    unittest.main()
