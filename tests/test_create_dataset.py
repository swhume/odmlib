import os
import tempfile
import unittest
import odmlib.dataset_1_0_1.model as ODM
import datetime
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL


class TestCreateDataset(unittest.TestCase):
    def setUp(self) -> None:
        # Write generated documents to a throw-away directory. Writing them into
        # the tracked data/ fixtures left a dirty working tree after every run,
        # because CreationDateTime/AsOfDateTime change on each execution.
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        self.odm_xml_file = os.path.join(tmp_dir.name, "ae_test.xml")
        self.odm_json_file = os.path.join(tmp_dir.name, "ae_test.json")
        # Register the Dataset-XML 1.0.1 namespace set required for write_xml().
        # The autouse conftest fixture resets to only the base odm namespace, so
        # we explicitly add xs, xml, and data here.
        NS.NamespaceRegistry(prefix="xs",   uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",  uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        current_datetime = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.root = ODM.ODM(FileOID="ODM.DATASET.001", AsOfDateTime=current_datetime, DatasetXMLVersion="1.0.0",
                       CreationDateTime=current_datetime, ODMVersion="1.3.2", FileType="Snapshot",
                       Originator="swhume", SourceSystem="odmlib", SourceSystemVersion="0.1")

        self.root.ClinicalData = ODM.ClinicalData(StudyOID="cdisc.odmlib.001", MetaDataVersionOID="MDV.001")

        self.root.ClinicalData.ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="1"))
        self._generate_igd_rows_1()
        self.root.ClinicalData.ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="2"))
        self._generate_igd_rows_2()


    def test_write_dataset_xml(self):
        self.root.write_xml(self.odm_xml_file)
        loader = OL.XMLODMLoader(model_package="dataset_1_0_1", ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        ns = NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        loader.create_document(self.odm_xml_file, ns)
        odm = loader.load_odm()
        self.assertEqual(odm.FileOID, "ODM.DATASET.001")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemGroupOID, "IG.AE")
        self.assertEqual(odm.ClinicalData.ItemGroupData[0].ItemData[2].Value, "CDISC01.100008")
        self.assertEqual(odm.ClinicalData.ItemGroupData[1].ItemData[4].Value, "ANXIETY")

    def test_write_dataset_json(self):
        self.root.write_json(self.odm_json_file)
        loader = OL.JSONODMLoader(model_package="dataset_1_0_1")
        loader.create_document(self.odm_json_file)
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
