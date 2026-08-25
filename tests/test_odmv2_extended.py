"""Extended tests for ODM 2.0 model (odmlib.odm_2_0).

Supplements test_odmv2_model.py with serialisation, round-trip, and
structural-difference tests (no FormDef/FormRef, has ItemGroupRef
directly on StudyEventDef, WorkflowDef, etc.).
"""
import json
import os
from unittest import TestCase
import odmlib.odm_2_0.model as ODM2
import odmlib.ns_registry as NS


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


# ---------------------------------------------------------------------------
# Structural differences from ODM 1.3.2
# ---------------------------------------------------------------------------

class TestODMv2Structure(TestCase):
    """ODM v2.0 has a flatter structure than v1.3.2."""

    def setUp(self):
        _setup_odm2_namespaces()

    def test_study_event_def_has_item_group_ref(self):
        """StudyEventDef contains ItemGroupRef directly (no FormRef layer)."""
        sed = ODM2.StudyEventDef(OID="SE.TEST", Name="Test Event", Repeating="No", Type="Common")
        igr = ODM2.ItemGroupRef(ItemGroupOID="IG.TEST", Mandatory="Yes")
        sed.ItemGroupRef.append(igr)
        self.assertEqual(len(sed.ItemGroupRef), 1)
        self.assertEqual(sed.ItemGroupRef[0].ItemGroupOID, "IG.TEST")

    def test_study_event_def_has_workflow_ref(self):
        """StudyEventDef may reference a WorkflowDef (new in v2.0)."""
        sed = ODM2.StudyEventDef(OID="SE.TEST", Name="Test Event", Repeating="No", Type="Common")
        # the XSD allows at most one WorkflowRef on a StudyEventDef
        sed.WorkflowRef = ODM2.WorkflowRef(WorkflowOID="WF.STANDARD")
        self.assertEqual(sed.WorkflowRef.WorkflowOID, "WF.STANDARD")

    def test_metadata_version_no_form_def(self):
        """ODM v2.0 MetaDataVersion should not expose FormDef."""
        mdv = ODM2.MetaDataVersion(OID="MDV.TEST", Name="Test MDV")
        self.assertFalse(hasattr(type(mdv), "FormDef"))

    def test_metadata_version_has_study_event_def(self):
        """ODM v2.0 MetaDataVersion holds StudyEventDef as a list."""
        mdv = ODM2.MetaDataVersion(OID="MDV.TEST", Name="Test MDV")
        sed = ODM2.StudyEventDef(OID="SE.SCREENING", Name="Screening", Repeating="No", Type="Scheduled")
        mdv.StudyEventDef.append(sed)
        self.assertEqual(len(mdv.StudyEventDef), 1)
        self.assertEqual(mdv.StudyEventDef[0].OID, "SE.SCREENING")

    def test_study_has_name_and_protocol_name_as_attrs(self):
        """ODM v2.0 Study uses flat attributes (StudyName, ProtocolName) not child elements."""
        study = ODM2.Study(OID="S.TEST", StudyName="Test Study", ProtocolName="Protocol A")
        self.assertEqual(study.StudyName, "Test Study")
        self.assertEqual(study.ProtocolName, "Protocol A")


# ---------------------------------------------------------------------------
# StudyEventDef
# ---------------------------------------------------------------------------

class TestODMv2StudyEventDef(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_create_minimal(self):
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Study Visit", Repeating="Yes", Type="Scheduled")
        self.assertEqual(sed.OID, "SE.VISIT")
        self.assertEqual(sed.Name, "Study Visit")
        self.assertEqual(sed.Repeating, "Yes")
        self.assertEqual(sed.Type, "Scheduled")

    def test_create_with_category(self):
        sed = ODM2.StudyEventDef(
            OID="SE.VISIT", Name="Study Visit",
            Repeating="No", Type="Common", Category="Baseline",
        )
        self.assertEqual(sed.Category, "Baseline")

    def test_valid_type_values(self):
        for t in ("Scheduled", "Unscheduled", "Common"):
            sed = ODM2.StudyEventDef(OID=f"SE.{t.upper()}", Name=t, Repeating="No", Type=t)
            self.assertEqual(sed.Type, t)

    def test_invalid_type_raises(self):
        with self.assertRaises((TypeError, ValueError)):
            ODM2.StudyEventDef(OID="SE.BAD", Name="Bad", Repeating="No", Type="InvalidType")

    def test_invalid_repeating_raises(self):
        with self.assertRaises((TypeError, ValueError)):
            ODM2.StudyEventDef(OID="SE.BAD", Name="Bad", Repeating="Maybe", Type="Common")

    def test_to_xml(self):
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Study Visit", Repeating="No", Type="Scheduled")
        elem = sed.to_xml()
        self.assertEqual(elem.tag, "StudyEventDef")
        self.assertEqual(elem.attrib["OID"], "SE.VISIT")
        self.assertEqual(elem.attrib["Name"], "Study Visit")
        self.assertEqual(elem.attrib["Repeating"], "No")
        self.assertEqual(elem.attrib["Type"], "Scheduled")

    def test_to_json(self):
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Study Visit", Repeating="No", Type="Scheduled")
        data = json.loads(sed.to_json())
        self.assertEqual(data["OID"], "SE.VISIT")
        self.assertEqual(data["Type"], "Scheduled")

    def test_to_dict(self):
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Visit", Repeating="No", Type="Common")
        d = sed.to_dict()
        self.assertEqual(d["OID"], "SE.VISIT")
        self.assertEqual(d["Type"], "Common")

    def test_iterator(self):
        """StudyEventDef supports len() and iteration over ItemGroupRef."""
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Visit", Repeating="No", Type="Common")
        sed.ItemGroupRef = [
            ODM2.ItemGroupRef(ItemGroupOID="IG.DM", Mandatory="Yes"),
            ODM2.ItemGroupRef(ItemGroupOID="IG.VS", Mandatory="No"),
        ]
        self.assertEqual(len(sed), 2)
        oids = [igr.ItemGroupOID for igr in sed]
        self.assertIn("IG.DM", oids)
        self.assertIn("IG.VS", oids)
        self.assertEqual(sed[0].ItemGroupOID, "IG.DM")


# ---------------------------------------------------------------------------
# ItemGroupDef (v2.0)
# ---------------------------------------------------------------------------

class TestODMv2ItemGroupDef(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_create(self):
        igd = ODM2.ItemGroupDef(OID="IG.DM", Name="DM", Repeating="No", Type="Dataset")
        self.assertEqual(igd.OID, "IG.DM")

    def test_add_item_refs(self):
        igd = ODM2.ItemGroupDef(OID="IG.DM", Name="DM", Repeating="No", Type="Dataset")
        igd.ItemRef = [
            ODM2.ItemRef(ItemOID="IT.USUBJID", Mandatory="Yes"),
            ODM2.ItemRef(ItemOID="IT.SEX",     Mandatory="Yes"),
        ]
        self.assertEqual(len(igd), 2)
        self.assertEqual(igd[0].ItemOID, "IT.USUBJID")

    def test_to_xml(self):
        igd = ODM2.ItemGroupDef(OID="IG.DM", Name="DM", Repeating="No", Type="Dataset")
        elem = igd.to_xml()
        self.assertEqual(elem.attrib["OID"], "IG.DM")
        self.assertEqual(elem.attrib["Repeating"], "No")

    def test_to_json(self):
        igd = ODM2.ItemGroupDef(OID="IG.DM", Name="DM", Repeating="No", Type="Dataset")
        data = json.loads(igd.to_json())
        self.assertEqual(data["OID"], "IG.DM")


# ---------------------------------------------------------------------------
# ItemDef (v2.0)
# ---------------------------------------------------------------------------

class TestODMv2ItemDef(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_create(self):
        item = ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer")
        self.assertEqual(item.OID, "IT.AGE")
        self.assertEqual(item.DataType, "integer")

    def test_create_with_description(self):
        tt   = ODM2.TranslatedText(_content="Subject Age", lang="en", Type="text/plain")
        desc = ODM2.Description(TranslatedText=[tt])
        item = ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer", Description=desc)
        self.assertEqual(item.Description.TranslatedText[0]._content, "Subject Age")

    def test_to_xml(self):
        item = ODM2.ItemDef(OID="IT.WEIGHT", Name="Weight", DataType="float", Length=8)
        elem = item.to_xml()
        self.assertEqual(elem.attrib["OID"], "IT.WEIGHT")
        self.assertEqual(elem.attrib["DataType"], "float")
        self.assertEqual(elem.attrib["Length"], "8")

    def test_to_json_round_trip(self):
        item = ODM2.ItemDef(OID="IT.SEX", Name="Sex", DataType="text")
        data = json.loads(item.to_json())
        self.assertEqual(data["OID"], "IT.SEX")
        self.assertEqual(data["DataType"], "text")

    def test_display_format_variable_set_round_trip(self):
        """DisplayFormat/VariableSet (v0.2.1 XSD alignment) round-trip."""
        item = ODM2.ItemDef(OID="IT.BMI", Name="BMI", DataType="float",
                            Length=6, DisplayFormat="9.2", VariableSet="VS1")
        self.assertEqual(item.DisplayFormat, "9.2")
        self.assertEqual(item.VariableSet, "VS1")

        elem = item.to_xml()
        self.assertEqual(elem.attrib["DisplayFormat"], "9.2")
        self.assertEqual(elem.attrib["VariableSet"], "VS1")

        data = json.loads(item.to_json())
        self.assertEqual(data["DisplayFormat"], "9.2")
        self.assertEqual(data["VariableSet"], "VS1")

        d = item.to_dict()
        self.assertEqual(d["DisplayFormat"], "9.2")
        self.assertEqual(d["VariableSet"], "VS1")


# ---------------------------------------------------------------------------
# MetaDataVersion (v2.0)
# ---------------------------------------------------------------------------

class TestODMv2MetaDataVersion(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_create(self):
        mdv = ODM2.MetaDataVersion(OID="MDV.001", Name="Version 1")
        self.assertEqual(mdv.OID, "MDV.001")
        self.assertEqual(mdv.Name, "Version 1")

    def test_add_all_major_elements(self):
        mdv = ODM2.MetaDataVersion(OID="MDV.001", Name="Version 1")
        sed = ODM2.StudyEventDef(OID="SE.VISIT", Name="Visit", Repeating="No", Type="Scheduled")
        igd = ODM2.ItemGroupDef(OID="IG.DM", Name="DM", Repeating="No", Type="Dataset")
        itd = ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer")
        mdv.StudyEventDef.append(sed)
        mdv.ItemGroupDef.append(igd)
        mdv.ItemDef.append(itd)
        self.assertEqual(len(mdv.StudyEventDef), 1)
        self.assertEqual(len(mdv.ItemGroupDef), 1)
        self.assertEqual(len(mdv.ItemDef), 1)

    def test_to_json(self):
        mdv = ODM2.MetaDataVersion(OID="MDV.001", Name="Version 1")
        data = json.loads(mdv.to_json())
        self.assertEqual(data["OID"], "MDV.001")


# ---------------------------------------------------------------------------
# Full ODM v2.0 document construction
# ---------------------------------------------------------------------------

class TestODMv2Document(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def _make_odm(self):
        mdv   = ODM2.MetaDataVersion(OID="MDV.001", Name="Version 1")
        study = ODM2.Study(OID="S.TEST", StudyName="Test Study", ProtocolName="Protocol A",
                           MetaDataVersion=[mdv])
        return ODM2.ODM(
            FileOID="F.TEST",
            FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            Study=[study],
        )

    def test_create(self):
        odm = self._make_odm()
        self.assertEqual(odm.FileOID, "F.TEST")
        self.assertEqual(odm.FileType, "Snapshot")

    def test_to_xml(self):
        odm = self._make_odm()
        elem = odm.to_xml()
        self.assertEqual(elem.tag, "ODM")
        self.assertEqual(elem.attrib["FileOID"], "F.TEST")

    def test_to_json(self):
        odm = self._make_odm()
        data = json.loads(odm.to_json())
        self.assertEqual(data["FileOID"], "F.TEST")
        self.assertIn("Study", data)

    def test_to_dict(self):
        odm = self._make_odm()
        d = odm.to_dict()
        self.assertIn("FileOID", d)
        self.assertIn("Study", d)
        self.assertIsInstance(d["Study"], list)

    def test_json_round_trip_preserves_oids(self):
        odm = self._make_odm()
        data = json.loads(odm.to_json())
        self.assertEqual(data["FileOID"], "F.TEST")
        self.assertEqual(data["Study"][0]["OID"], "S.TEST")
        self.assertEqual(data["Study"][0]["MetaDataVersion"][0]["OID"], "MDV.001")


# ---------------------------------------------------------------------------
# Load ODM 2.0 from real XML file
# ---------------------------------------------------------------------------

class TestODMv2LoadFromFile(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

    def test_load_odmv2_example(self):
        from odmlib import odm_loader as OL, loader as LO
        import odmlib.ns_registry as NS
        nsr = NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        odm_file = os.path.join(self.data_dir, "odmv2_example.xml")
        loader = LO.ODMLoader(OL.XMLODMLoader(
            model_package="odm_2_0",
            ns_uri="http://www.cdisc.org/ns/odm/v2.0",
            local_model=False,
            nsr=nsr,
        ))
        loader.open_odm_document(odm_file)
        study = loader.Study()
        mdv   = loader.MetaDataVersion()
        self.assertEqual(study.OID, "ODM.COSA.STUDY")
        self.assertIsNotNone(mdv.OID)

    def test_load_cdash_v20(self):
        from odmlib import odm_loader as OL, loader as LO
        import odmlib.ns_registry as NS
        nsr = NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        cdash_file = os.path.join(self.data_dir, "cdash_demo_v20.xml")
        loader = LO.ODMLoader(OL.XMLODMLoader(
            model_package="odm_2_0",
            ns_uri="http://www.cdisc.org/ns/odm/v2.0",
            local_model=False,
            nsr=nsr,
        ))
        loader.open_odm_document(cdash_file)
        study = loader.Study()
        self.assertEqual(study.OID, "ODM.CDASH.STUDY")

    def test_metadata_version_has_study_event_defs(self):
        from odmlib import odm_loader as OL, loader as LO
        import odmlib.ns_registry as NS
        nsr = NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        odm_file = os.path.join(self.data_dir, "odmv2_example.xml")
        loader = LO.ODMLoader(OL.XMLODMLoader(
            model_package="odm_2_0",
            ns_uri="http://www.cdisc.org/ns/odm/v2.0",
            local_model=False,
            nsr=nsr,
        ))
        loader.open_odm_document(odm_file)
        mdv = loader.MetaDataVersion()
        # v2.0 MetaDataVersion should not have FormDef
        self.assertFalse(hasattr(type(mdv), "FormDef"))
        # v2.0 MetaDataVersion may have StudyEventDef
        self.assertTrue(hasattr(mdv, "StudyEventDef"))
