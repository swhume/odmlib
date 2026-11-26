from unittest import TestCase
import odmlib.arm_loader as ARM
import odmlib.loader as LD
import odmlib.ns_registry as NS
import os
import json
import tempfile
from odmlib.exceptions import OdmlibTypeError


def _tmp_dir(test_case):
    """A throw-away directory for generated output, removed after the test.

    Writing into the tracked tests/data/ directory dirtied the working tree.
    """
    tmp_dir = tempfile.TemporaryDirectory()
    test_case.addCleanup(tmp_dir.cleanup)
    return tmp_dir.name


class TestODMLoader(TestCase):
    def setUp(self) -> None:
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'definev21-adam.xml')
        self.loader = LD.ODMLoader(ARM.XMLArmLoader(model_package="arm_1_0", ns_uri="http://www.cdisc.org/ns/arm/v1.0"))
        self.jloader = LD.ODMLoader(ARM.JSONArmLoader())
        self.tmp_dir = _tmp_dir(self)

    def test_unknown_loader(self):
        with self.assertRaises(OdmlibTypeError):
            loader = LD.ODMLoader(self.test_mdv_find_by_OID())

    def test_open_odm_document(self):
        root = self.loader.open_odm_document(self.odm_file)
        elem_name = root.tag[root.tag.find('}') + 1:]
        self.assertEqual("ODM", elem_name)
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", root.attrib["FileOID"])

    def test_load_odm(self):
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.load_odm()
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", odm.FileOID)

    def test_load_missing(self):
        root = self.loader.open_odm_document(self.odm_file)
        with self.assertRaises(AttributeError):
            odm = self.loader.load_standard()

    def test_load_study(self):
        root = self.loader.open_odm_document(self.odm_file)
        study = self.loader.load_study()
        self.assertEqual("STDY.www.cdisc.org/CDISC-Sample/ADaM", study.OID)

    def test_meta_data_version(self):
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC-Sample, Data Definitions")
        self.assertEqual(mdv.AnalysisResultDisplays[0].OID, "RD.Table_14-3.01")

    def test_mdv_find_by_OID(self):
        self.loader.open_odm_document(self.odm_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC-Sample, Data Definitions")
        ir = mdv.ItemGroupDef[0].find("ItemRef", "ItemOID", "IT.ADSL.USUBJID")
        self.assertEqual(ir.ItemOID, mdv.ItemGroupDef[0].ItemRef[1].ItemOID)
        it = mdv.find("ItemDef", "OID", "IT.ADAE.AESEV")
        self.assertEqual(it.CodeListRef.CodeListOID, "CL.AESEV")
        cli = mdv.CodeList[27].find("CodeListItem", "CodedValue", "MODERATE")
        self.assertEqual(cli.Decode.TranslatedText[0]._content, "Grade 2")
        ir = mdv.ValueListDef[2].find("ItemRef", "ItemOID", "IT.ADQSADAS.QSSEQ.ACTOT")
        self.assertEqual(ir.WhereClauseRef[0].WhereClauseOID, "WC.ADQSADAS.QSSEQ.ACTOT")

    def test_odm_round_trip(self):
        """Test XML -> JSON -> XML round-trip with ARM-specific elements preserved."""
        root = self.loader.open_odm_document(self.odm_file)
        odm = self.loader.create_odmlib(root)
        odm_json = odm.to_json()
        odm_json_file = os.path.join(self.tmp_dir, 'adam_define21_test.json')
        with open(odm_json_file, "w") as odm_in:
            odm_in.write(odm_json)
        # Use JSONArmLoader to load JSON back with ARM model classes
        json_loader = LD.ODMLoader(ARM.JSONArmLoader())
        odm_dict = json_loader.open_odm_document(odm_json_file)
        rt_odm = json_loader.create_odmlib(odm_dict, "ODM")
        def_xml_file = os.path.join(self.tmp_dir, 'adam_def_test_roundtrip.xml')
        rt_odm.write_xml(def_xml_file)
        root2 = self.loader.open_odm_document(def_xml_file)
        odm2 = self.loader.create_odmlib(root2)
        self.assertEqual(odm2.Study.MetaDataVersion.OID, "MDV.CDISC01.ADaMIG.1.1.ADaM.2.1")
        self.assertEqual(len(odm2.Study.MetaDataVersion.ItemGroupDef[1]), 40)
        # Verify ARM-specific elements survive the round-trip
        mdv2 = odm2.Study.MetaDataVersion
        self.assertEqual(len(mdv2.AnalysisResultDisplays), 2)
        self.assertEqual(mdv2.AnalysisResultDisplays[0].OID, "RD.Table_14-3.01")
        self.assertEqual(mdv2.AnalysisResultDisplays[0].AnalysisResult[0].OID, "AR.Table_14-3.01.R.1")


class TestJSONArmLoader(TestCase):
    """Tests for JSONArmLoader loading ARM JSON documents."""

    def setUp(self) -> None:
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'definev21-adam.xml')
        # Create JSON from XML for testing
        xml_loader = LD.ODMLoader(ARM.XMLArmLoader())
        xml_loader.open_odm_document(self.odm_file)
        odm = xml_loader.load_odm()
        self.json_file = os.path.join(_tmp_dir(self), 'adam_arm_test.json')
        with open(self.json_file, "w") as f:
            f.write(odm.to_json())
        self.loader = LD.ODMLoader(ARM.JSONArmLoader())

    def test_load_odm(self):
        self.loader.open_odm_document(self.json_file)
        odm = self.loader.load_odm()
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", odm.FileOID)

    def test_load_study(self):
        self.loader.open_odm_document(self.json_file)
        study = self.loader.load_study()
        self.assertEqual("STDY.www.cdisc.org/CDISC-Sample/ADaM", study.OID)

    def test_load_metadataversion(self):
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "Study CDISC-Sample, Data Definitions")
        self.assertEqual(mdv.OID, "MDV.CDISC01.ADaMIG.1.1.ADaM.2.1")

    def test_load_analysis_result_displays(self):
        """Verify ARM-specific AnalysisResultDisplays load from JSON."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(len(mdv.AnalysisResultDisplays), 2)
        rd = mdv.AnalysisResultDisplays[0]
        self.assertEqual(rd.OID, "RD.Table_14-3.01")
        self.assertEqual(rd.Name, "Table 14-3.01")

    def test_load_analysis_result(self):
        """Verify AnalysisResult elements load from JSON with all attributes."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        ar = mdv.AnalysisResultDisplays[0].AnalysisResult[0]
        self.assertEqual(ar.OID, "AR.Table_14-3.01.R.1")
        self.assertEqual(ar.ParameterOID, "IT.ADQSADAS.PARAMCD")
        self.assertEqual(ar.AnalysisReason, "SPECIFIED IN SAP")
        self.assertEqual(ar.AnalysisPurpose, "PRIMARY OUTCOME MEASURE")

    def test_load_analysis_result_description(self):
        """Verify AnalysisResult Description loads from JSON."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        ar = mdv.AnalysisResultDisplays[0].AnalysisResult[0]
        self.assertEqual(ar.Description.TranslatedText[0]._content,
                         "Dose response analysis for ADAS-Cog changes from baseline")

    def test_load_documentation(self):
        """Verify ARM Documentation element loads from JSON."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        ar = mdv.AnalysisResultDisplays[0].AnalysisResult[0]
        self.assertTrue(ar.Documentation.Description.TranslatedText[0]._content.startswith(
            "Linear model analysis of CHG for dose response"))
        self.assertEqual(ar.Documentation.DocumentRef[0].leafID, "LF.CSR")

    def test_load_programming_code(self):
        """Verify ARM ProgrammingCode element loads from JSON."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        ar = mdv.AnalysisResultDisplays[0].AnalysisResult[0]
        self.assertEqual(ar.ProgrammingCode.Context, "SAS version 9.2")
        self.assertTrue(str(ar.ProgrammingCode.Code._content).startswith(
            "\nproc glm data = ADQSADAS"))

    def test_load_analysis_datasets(self):
        """Verify ARM AnalysisDatasets load from JSON."""
        self.loader.open_odm_document(self.json_file)
        mdv = self.loader.MetaDataVersion()
        ar = mdv.AnalysisResultDisplays[0].AnalysisResult[0]
        self.assertEqual(len(ar.AnalysisDatasets), 1)
        ad = ar.AnalysisDatasets.AnalysisDataset[0]
        self.assertEqual(ad.ItemGroupOID, "IG.ADQSADAS")
        self.assertEqual(ad.AnalysisVariable[0].ItemOID, "IT.ADQSADAS.CHG")

    def test_load_odm_before_create_raises(self):
        """Verify proper error when loading before creating document."""
        from odmlib.exceptions import OdmlibLoaderStateError
        raw_loader = ARM.JSONArmLoader()
        with self.assertRaises(OdmlibLoaderStateError):
            raw_loader.load_odm()

    def test_load_study_before_create_raises(self):
        from odmlib.exceptions import OdmlibLoaderStateError
        raw_loader = ARM.JSONArmLoader()
        with self.assertRaises(OdmlibLoaderStateError):
            raw_loader.load_study()

    def test_load_metadataversion_before_create_raises(self):
        from odmlib.exceptions import OdmlibLoaderStateError
        raw_loader = ARM.JSONArmLoader()
        with self.assertRaises(OdmlibLoaderStateError):
            raw_loader.load_metadataversion()

    def test_load_from_string(self):
        """Verify JSONArmLoader can load from a JSON string."""
        with open(self.json_file) as f:
            json_string = f.read()
        raw_loader = ARM.JSONArmLoader()
        raw_loader.create_document_from_string(json_string)
        odm = raw_loader.load_odm()
        self.assertEqual("www.cdisc.org/CDISC-Sample/ADaM/1/Define-XML_2.1.0", odm.FileOID)
        mdv = odm.Study.MetaDataVersion
        self.assertEqual(len(mdv.AnalysisResultDisplays), 2)


if __name__ == '__main__':
    import unittest
    unittest.main()
