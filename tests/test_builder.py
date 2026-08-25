"""Tests for the ODMBuilder fluent API.

Covers:
- Building a minimal valid ODM document.
- Adding MetaDataVersion, ItemGroupDef, ItemRef, ItemDef, CodeList.
- Error handling for out-of-order calls.
- XML and JSON round-trip from a builder-produced document.
- with_description() helper.
"""
import os
import tempfile
from unittest import TestCase
from odmlib.builder import ODMBuilder


class TestODMBuilderMinimal(TestCase):
    """Tests for the most basic builder usage."""

    def test_build_returns_odm_object(self):
        """build() returns an object with the expected file attributes."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .build())
        self.assertEqual(odm.FileOID, "F.001")
        self.assertEqual(odm.FileType, "Snapshot")

    def test_build_with_no_studies(self):
        """build() works even with no studies added."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.EMPTY", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .build())
        self.assertEqual(odm.Study, [])

    def test_add_study_creates_one_study(self):
        """add_study() adds exactly one Study with GlobalVariables."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="Test Study",
                          study_description="A test", protocol_name="P.001")
               .build())
        self.assertEqual(len(odm.Study), 1)
        self.assertEqual(odm.Study[0].OID, "S.001")

    def test_global_variables_populated(self):
        """GlobalVariables is correctly populated by add_study()."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="My Study",
                          study_description="Desc", protocol_name="PROT-001")
               .build())
        gv = odm.Study[0].GlobalVariables
        self.assertEqual(gv.StudyName._content, "My Study")
        self.assertEqual(gv.StudyDescription._content, "Desc")
        self.assertEqual(gv.ProtocolName._content, "PROT-001")

    def test_add_multiple_studies(self):
        """Multiple calls to add_study() create multiple Study elements."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="Study 1",
                          study_description="D1", protocol_name="P1")
               .add_study(OID="S.002", study_name="Study 2",
                          study_description="D2", protocol_name="P2")
               .build())
        self.assertEqual(len(odm.Study), 2)
        self.assertEqual(odm.Study[1].OID, "S.002")


class TestODMBuilderMetaData(TestCase):
    """Tests for MetaDataVersion, ItemGroupDef, ItemRef, and ItemDef."""

    def _minimal_odm(self):
        return (ODMBuilder()
                .set_file(FileOID="F.001", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.001", study_name="Test",
                           study_description="Desc", protocol_name="P.001"))

    def test_add_metadata_version(self):
        """add_metadata_version() creates a MetaDataVersion in the Study."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="Version 1")
               .build())
        mdv = odm.Study[0].MetaDataVersion
        self.assertEqual(len(mdv), 1)
        self.assertEqual(mdv[0].OID, "MDV.001")
        self.assertEqual(mdv[0].Name, "Version 1")

    def test_add_item_group_def(self):
        """add_item_group_def() adds an ItemGroupDef to the current MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics",
                                   Repeating="No")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemGroupDef), 1)
        self.assertEqual(mdv.ItemGroupDef[0].OID, "IG.DM")

    def test_add_item_refs(self):
        """add_item_ref() appends ItemRefs to the current ItemGroupDef."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
               .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
               .build())
        igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertEqual(len(igd.ItemRef), 2)
        self.assertEqual(igd.ItemRef[0].ItemOID, "IT.SUBJID")
        self.assertEqual(igd.ItemRef[1].ItemOID, "IT.AGE")

    def test_item_refs_go_to_current_igd_only(self):
        """add_item_ref() only targets the most recently added ItemGroupDef."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes")
               .add_item_group_def(OID="IG.AE", Name="Adverse Events", Repeating="Yes")
               .add_item_ref(ItemOID="IT.AETRT", Mandatory="Yes")
               .add_item_ref(ItemOID="IT.AEDTC", Mandatory="No")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemGroupDef[0].ItemRef), 1)
        self.assertEqual(len(mdv.ItemGroupDef[1].ItemRef), 2)

    def test_add_item_def(self):
        """add_item_def() appends an ItemDef to the current MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemDef), 1)
        self.assertEqual(mdv.ItemDef[0].OID, "IT.AGE")
        self.assertEqual(mdv.ItemDef[0].DataType, "integer")

    def test_add_multiple_item_defs(self):
        """Multiple add_item_def() calls accumulate in the MDV."""
        odm = (self._minimal_odm()
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.SUBJID", Name="Subject ID", DataType="text")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.ItemDef), 2)


class TestODMBuilderCodeList(TestCase):
    """Tests for add_code_list()."""

    def _base_builder(self):
        return (ODMBuilder()
                .set_file(FileOID="F.001", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.001", study_name="T", study_description="D",
                           protocol_name="P")
                .add_metadata_version(OID="MDV.001", Name="V1"))

    def test_add_code_list_no_items(self):
        """add_code_list() with no items creates an empty CodeList."""
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(len(mdv.CodeList), 1)
        self.assertEqual(mdv.CodeList[0].OID, "CL.YN")
        self.assertEqual(mdv.CodeList[0].CodeListItem, [])

    def test_add_code_list_enumerated_items(self):
        """Items without Decode key create EnumeratedItems."""
        items = [{"CodedValue": "Y"}, {"CodedValue": "N"}]
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text",
                              items=items)
               .build())
        cl = odm.Study[0].MetaDataVersion[0].CodeList[0]
        self.assertEqual(len(cl.EnumeratedItem), 2)
        self.assertEqual(cl.EnumeratedItem[0].CodedValue, "Y")

    def test_add_code_list_coded_items(self):
        """Items with Decode key create CodeListItems."""
        items = [
            {"CodedValue": "Y", "Decode": "Yes"},
            {"CodedValue": "N", "Decode": "No"},
        ]
        odm = (self._base_builder()
               .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text",
                              items=items)
               .build())
        cl = odm.Study[0].MetaDataVersion[0].CodeList[0]
        self.assertEqual(len(cl.CodeListItem), 2)
        self.assertEqual(cl.CodeListItem[0].CodedValue, "Y")
        self.assertEqual(cl.CodeListItem[0].Decode.TranslatedText[0]._content, "Yes")


class TestODMBuilderDescription(TestCase):
    """Tests for the with_description() helper."""

    def test_with_description_on_item_group_def(self):
        """with_description() after add_item_group_def sets its Description."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="T", study_description="D",
                          protocol_name="P")
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
               .with_description("Demographic dataset", lang="en")
               .build())
        igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertIsNotNone(igd.Description)
        self.assertEqual(igd.Description.TranslatedText[0]._content,
                         "Demographic dataset")

    def test_with_description_on_item_def(self):
        """with_description() after add_item_def sets that ItemDef's Description."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.001", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.001", study_name="T", study_description="D",
                          protocol_name="P")
               .add_metadata_version(OID="MDV.001", Name="V1")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .with_description("Subject age in years")
               .build())
        item = odm.Study[0].MetaDataVersion[0].ItemDef[0]
        self.assertIsNotNone(item.Description)
        self.assertEqual(item.Description.TranslatedText[0]._content,
                         "Subject age in years")


class TestODMBuilderErrors(TestCase):
    """Tests for RuntimeError on out-of-order calls."""

    def test_add_metadata_version_before_study_raises(self):
        """add_metadata_version() before add_study() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            ODMBuilder().add_metadata_version(OID="MDV.001", Name="V1")

    def test_add_item_group_def_before_mdv_raises(self):
        """add_item_group_def() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No"))

    def test_add_item_ref_before_igd_raises(self):
        """add_item_ref() before add_item_group_def() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_metadata_version(OID="MDV.001", Name="V1")
             .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes"))

    def test_add_item_def_before_mdv_raises(self):
        """add_item_def() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_item_def(OID="IT.AGE", Name="Age", DataType="integer"))

    def test_add_code_list_before_mdv_raises(self):
        """add_code_list() before add_metadata_version() raises RuntimeError."""
        with self.assertRaises(RuntimeError):
            (ODMBuilder()
             .add_study(OID="S.001", study_name="T", study_description="D",
                        protocol_name="P")
             .add_code_list(OID="CL.YN", Name="Yes/No", DataType="text"))


class TestODMBuilderRoundTrip(TestCase):
    """Tests that builder-produced documents serialize and deserialize correctly."""

    def setUp(self):
        self.odm = (ODMBuilder()
                    .set_file(FileOID="F.BUILDER", FileType="Snapshot",
                              CreationDateTime="2024-01-01T00:00:00")
                    .add_study(OID="S.001", study_name="Builder Test",
                               study_description="Round-trip test",
                               protocol_name="P.001")
                    .add_metadata_version(OID="MDV.001", Name="Version 1")
                    .add_item_group_def(OID="IG.DM", Name="Demographics",
                                       Repeating="No")
                    .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes",
                                  OrderNumber=1)
                    .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
                    .add_item_def(OID="IT.SUBJID", Name="Subject ID",
                                  DataType="text")
                    .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
                    .build())

    def test_to_json_round_trip(self):
        """Builder document can be serialised to JSON and back to dict."""
        import json
        json_str = self.odm.to_json()
        d = json.loads(json_str)
        self.assertEqual(d["FileOID"], "F.BUILDER")
        self.assertEqual(len(d["Study"]), 1)
        self.assertEqual(d["Study"][0]["OID"], "S.001")

    def test_to_xml_round_trip(self):
        """Builder document can be serialised to XML."""
        import xml.etree.ElementTree as ET
        xml_elem = self.odm.to_xml()
        self.assertIsNotNone(xml_elem)
        elem_name = xml_elem.tag[xml_elem.tag.find("}") + 1:]
        self.assertEqual(elem_name, "ODM")

    def test_write_xml_file(self):
        """Builder document can be written to an XML file."""
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            out_path = f.name
        try:
            self.odm.write_xml(out_path)
            self.assertTrue(os.path.getsize(out_path) > 0)
            # Sanity-check: the file starts with an XML declaration
            with open(out_path, "rb") as fh:
                header = fh.read(5)
            self.assertEqual(header, b"<?xml")
        finally:
            os.unlink(out_path)

    def test_write_json_file(self):
        """Builder document can be written to a JSON file."""
        import json
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False) as f:
            out_path = f.name
        try:
            self.odm.write_json(out_path)
            with open(out_path) as fh:
                d = json.load(fh)
            self.assertEqual(d["FileOID"], "F.BUILDER")
        finally:
            os.unlink(out_path)


class TestODMBuilderAlternatePackage(TestCase):
    """Tests that ODMBuilder builds full documents for model_package='odm_2_0'.

    ODM 2.0 has a flatter Study (scalar StudyName/ProtocolName, no
    GlobalVariables) and an object-valued MetaDataVersion.Description; the
    builder must adapt to that shape automatically.
    """

    def _v2_namespaces(self):
        import odmlib.ns_registry as NS
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

    def _build_v2(self):
        return (ODMBuilder("odm_2_0")
                .set_file(FileOID="F.V2", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.V2", study_name="V2 Study",
                           study_description="ODM 2.0 round-trip test",
                           protocol_name="P.V2")
                .add_metadata_version(OID="MDV.V2", Name="Version 1")
                .with_description("Metadata for the V2 study")
                .add_item_group_def(OID="IG.DM", Name="Demographics",
                                    Repeating="No", Type="Dataset")
                .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes",
                              OrderNumber=1)
                .add_item_def(OID="IT.SUBJID", Name="Subject ID",
                              DataType="text")
                .add_code_list(OID="CL.SEX", Name="Sex", DataType="text",
                               items=[{"CodedValue": "M", "Decode": "Male"},
                                      {"CodedValue": "F", "Decode": "Female"}])
                .build())

    def test_minimal_file_only(self):
        """File-level build still works for odm_2_0 (no Study)."""
        self._v2_namespaces()
        odm = (ODMBuilder("odm_2_0")
               .set_file(FileOID="F.V2", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .build())
        self.assertEqual(odm.FileOID, "F.V2")

    def test_add_study_v2_shape(self):
        """add_study() builds the flat ODM 2.0 Study (no GlobalVariables)."""
        self._v2_namespaces()
        odm = self._build_v2()
        study = odm.Study[0]
        self.assertEqual(study.OID, "S.V2")
        self.assertEqual(study.StudyName, "V2 Study")
        self.assertEqual(study.ProtocolName, "P.V2")
        self.assertFalse(hasattr(study, "GlobalVariables")
                         and study.GlobalVariables is not None)
        # Study.Description is an object with TranslatedText in ODM 2.0
        self.assertEqual(study.Description.TranslatedText[0]._content,
                         "ODM 2.0 round-trip test")

    def test_mdv_description_is_object(self):
        """with_description() sets an object-valued MDV Description in v2.0."""
        self._v2_namespaces()
        odm = self._build_v2()
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.Description.TranslatedText[0]._content,
                         "Metadata for the V2 study")

    def test_full_document_structure(self):
        """A full v2.0 metadata tree is constructed under the MDV."""
        self._v2_namespaces()
        mdv = self._build_v2().Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.ItemGroupDef[0].OID, "IG.DM")
        self.assertEqual(mdv.ItemGroupDef[0].ItemRef[0].ItemOID, "IT.SUBJID")
        self.assertEqual(mdv.ItemDef[0].OID, "IT.SUBJID")
        self.assertEqual(mdv.CodeList[0].OID, "CL.SEX")
        self.assertEqual(len(mdv.CodeList[0].CodeListItem), 2)

    def test_v2_xml_round_trip(self):
        """Builder-produced v2.0 document serialises to XML."""
        self._v2_namespaces()
        xml_elem = self._build_v2().to_xml()
        self.assertIsNotNone(xml_elem)
        self.assertEqual(xml_elem.tag[xml_elem.tag.find("}") + 1:], "ODM")

    def test_v2_json_round_trip(self):
        """Builder-produced v2.0 document serialises to JSON."""
        import json
        self._v2_namespaces()
        d = json.loads(self._build_v2().to_json())
        self.assertEqual(d["FileOID"], "F.V2")
        self.assertEqual(d["Study"][0]["OID"], "S.V2")


class TestODMBuilderPhase2(TestCase):
    """Core ODM authoring elements: events/forms/methods/conditions/units."""

    def _base(self):
        return (ODMBuilder()
                .set_file(FileOID="F.P2", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.P2", study_name="Phase2",
                           study_description="desc", protocol_name="P.P2")
                .add_metadata_version(OID="MDV.P2", Name="V1"))

    def test_study_event_def_and_ref(self):
        odm = (self._base()
               .add_study_event_def(OID="SE.VISIT1", Name="Visit 1",
                                    Repeating="No", Type="Scheduled")
               .add_study_event_ref(StudyEventOID="SE.VISIT1",
                                    Mandatory="Yes", OrderNumber=1)
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.StudyEventDef[0].OID, "SE.VISIT1")
        self.assertIsNotNone(mdv.Protocol)
        self.assertEqual(mdv.Protocol.StudyEventRef[0].StudyEventOID,
                         "SE.VISIT1")

    def test_form_def_ref_item_group_ref(self):
        odm = (self._base()
               .add_study_event_def(OID="SE.V1", Name="V1",
                                    Repeating="No", Type="Scheduled")
               .add_form_ref(FormOID="F.DM", Mandatory="Yes", OrderNumber=1)
               .add_form_def(OID="F.DM", Name="Demographics Form",
                             Repeating="No")
               .add_item_group_ref(ItemGroupOID="IG.DM", Mandatory="Yes",
                                   OrderNumber=1)
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.StudyEventDef[0].FormRef[0].FormOID, "F.DM")
        self.assertEqual(mdv.FormDef[0].OID, "F.DM")
        self.assertEqual(mdv.FormDef[0].ItemGroupRef[0].ItemGroupOID, "IG.DM")

    def test_method_and_condition_def(self):
        odm = (self._base()
               .add_method_def(OID="MT.AGE", Name="Age Derivation",
                               Type="Computation",
                               description="Derive age from birth date",
                               formal_expression="(today - dob).years",
                               expression_context="Python")
               .add_condition_def(OID="CD.MALE", Name="Is Male",
                                  description="Subject is male",
                                  formal_expression="SEX == 'M'")
               .build())
        mdv = odm.Study[0].MetaDataVersion[0]
        md = mdv.MethodDef[0]
        self.assertEqual(md.OID, "MT.AGE")
        self.assertEqual(md.Description.TranslatedText[0]._content,
                         "Derive age from birth date")
        self.assertEqual(md.FormalExpression[0].Context, "Python")
        cd = mdv.ConditionDef[0]
        self.assertEqual(cd.OID, "CD.MALE")
        self.assertEqual(cd.FormalExpression[0]._content, "SEX == 'M'")

    def test_measurement_unit(self):
        odm = (self._base()
               .add_measurement_unit(OID="MU.KG", Name="Kilograms",
                                     symbol="kg")
               .build())
        bd = odm.Study[0].BasicDefinitions
        self.assertIsNotNone(bd)
        self.assertEqual(bd.MeasurementUnit[0].OID, "MU.KG")
        self.assertEqual(bd.MeasurementUnit[0].Symbol.TranslatedText[0]._content,
                         "kg")

    def test_item_def_enrichers(self):
        odm = (self._base()
               .add_item_group_def(OID="IG.DM", Name="DM", Repeating="No")
               .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
               .with_question("What is the age?")
               .with_codelist_ref("CL.AGEGRP")
               .with_measurement_unit_ref("MU.YR")
               .with_range_check("GE", [0, 120], soft_hard="Hard")
               .with_alias("SDTM", "AGE")
               .build())
        item = odm.Study[0].MetaDataVersion[0].ItemDef[0]
        self.assertEqual(item.Question.TranslatedText[0]._content,
                         "What is the age?")
        self.assertEqual(item.CodeListRef.CodeListOID, "CL.AGEGRP")
        self.assertEqual(item.MeasurementUnitRef[0].MeasurementUnitOID, "MU.YR")
        self.assertEqual(item.RangeCheck[0].Comparator, "GE")
        self.assertEqual([cv._content for cv in item.RangeCheck[0].CheckValue],
                         ["0", "120"])
        self.assertEqual(item.Alias[0].Name, "AGE")

    def test_enricher_before_item_def_raises(self):
        with self.assertRaises(RuntimeError):
            self._base().with_question("Q?")

    def test_v2_form_methods_guarded(self):
        b = (ODMBuilder("odm_2_0")
             .set_file(FileOID="F.V2", FileType="Snapshot",
                       CreationDateTime="2024-01-01T00:00:00")
             .add_study(OID="S.V2", study_name="S",
                        study_description="D", protocol_name="P")
             .add_metadata_version(OID="MDV.V2", Name="V1")
             .add_study_event_def(OID="SE.V1", Name="V1",
                                  Repeating="No", Type="Scheduled"))
        with self.assertRaises(RuntimeError):
            b.add_form_def(OID="F.X", Name="X", Repeating="No")
        with self.assertRaises(RuntimeError):
            b.add_form_ref(FormOID="F.X", Mandatory="Yes")

    def test_v2_item_group_ref_routes_to_study_event(self):
        odm = (ODMBuilder("odm_2_0")
               .set_file(FileOID="F.V2", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.V2", study_name="S",
                          study_description="D", protocol_name="P")
               .add_metadata_version(OID="MDV.V2", Name="V1")
               .add_study_event_def(OID="SE.V1", Name="V1",
                                    Repeating="No", Type="Scheduled")
               .add_item_group_ref(ItemGroupOID="IG.DM", Mandatory="Yes")
               .build())
        sed = odm.Study[0].MetaDataVersion[0].StudyEventDef[0]
        self.assertEqual(sed.ItemGroupRef[0].ItemGroupOID, "IG.DM")


class TestODMBuilderODM2Alignment(TestCase):
    """Builder output for odm_2_0 must satisfy the ODM 2.0 XSD (v0.2.1)."""

    def _v2_namespaces(self):
        import odmlib.ns_registry as NS
        NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

    def _v2(self):
        return (ODMBuilder("odm_2_0")
                .set_file(FileOID="F.V2", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00",
                          ODMVersion="2.0", Granularity="Metadata")
                .add_study(OID="S.V2", study_name="S",
                           study_description="D", protocol_name="P")
                .add_metadata_version(OID="MDV.V2", Name="V1")
                .add_item_group_def(OID="IG.DM", Name="DM", Repeating="No",
                                    Type="Dataset")
                .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1)
                .add_item_def(OID="IT.AGE", Name="Age", DataType="integer"))

    def test_v2_formal_expression_wrapped_in_code(self):
        """ODM 2.0 FormalExpression is element-based; text goes in Code."""
        self._v2_namespaces()
        odm = (self._v2()
               .add_method_def(OID="MT.1", Name="M", Type="Computation",
                               description="d",
                               formal_expression="today - birthdate")
               .build())
        md = odm.Study[0].MetaDataVersion[0].MethodDef[0]
        self.assertIsNone(getattr(md.FormalExpression[0], "_content", None))
        self.assertEqual(md.FormalExpression[0].Code._content,
                         "today - birthdate")

    def test_v1_formal_expression_stays_text(self):
        """ODM 1.3.2 keeps the text form — no behaviour change."""
        odm = (ODMBuilder()
               .set_file(FileOID="F.V1", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.V1", study_name="S",
                          study_description="D", protocol_name="P")
               .add_metadata_version(OID="MDV.V1", Name="V1")
               .add_method_def(OID="MT.1", Name="M", Type="Computation",
                               description="d", formal_expression="a + b")
               .build())
        md = odm.Study[0].MetaDataVersion[0].MethodDef[0]
        self.assertEqual(md.FormalExpression[0]._content, "a + b")

    def test_v2_method_def_emits_method_signature(self):
        """MethodSignature is minOccurs=1 on MethodDef in the ODM 2.0 XSD."""
        self._v2_namespaces()
        odm = (self._v2()
               .add_method_def(OID="MT.1", Name="M", Type="Computation",
                               description="d")
               .build())
        md = odm.Study[0].MetaDataVersion[0].MethodDef[0]
        self.assertIsNotNone(md.MethodSignature)

    def test_v2_condition_def_emits_description_and_signature(self):
        self._v2_namespaces()
        odm = (self._v2()
               .add_condition_def(OID="CND.1", Name="Adult",
                                  description="Subject is an adult",
                                  formal_expression="age >= 18")
               .build())
        cd = odm.Study[0].MetaDataVersion[0].ConditionDef[0]
        self.assertIsNotNone(cd.MethodSignature)
        self.assertEqual(cd.Description.TranslatedText[0]._content,
                         "Subject is an adult")
        self.assertEqual(cd.FormalExpression[0].Code._content, "age >= 18")

    def test_v2_condition_def_requires_description(self):
        self._v2_namespaces()
        with self.assertRaises(RuntimeError):
            self._v2().add_condition_def(OID="CND.1", Name="Adult")

    def test_v1_condition_def_description_still_optional(self):
        odm = (ODMBuilder()
               .set_file(FileOID="F.V1", FileType="Snapshot",
                         CreationDateTime="2024-01-01T00:00:00")
               .add_study(OID="S.V1", study_name="S",
                          study_description="D", protocol_name="P")
               .add_metadata_version(OID="MDV.V1", Name="V1")
               .add_condition_def(OID="CND.1", Name="Adult")
               .build())
        cd = odm.Study[0].MetaDataVersion[0].ConditionDef[0]
        self.assertEqual(cd.OID, "CND.1")

    def test_v2_study_event_ref_raises(self):
        """Protocol/StudyEventRef does not exist in the ODM 2.0 XSD."""
        self._v2_namespaces()
        with self.assertRaises(RuntimeError):
            self._v2().add_study_event_ref(StudyEventOID="SE.1",
                                           Mandatory="Yes")

    def test_v2_builder_output_validates_against_xsd(self):
        self._v2_namespaces()
        from odmlib.odm_parser import ODMSchemaValidator
        odm = (self._v2()
               .add_method_def(OID="MT.1", Name="M", Type="Computation",
                               description="d", formal_expression="a + b")
               .add_condition_def(OID="CND.1", Name="Adult",
                                  description="Adult",
                                  formal_expression="age >= 18")
               .build())
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "builder_v2.xml")
            odm.write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)


class TestODMBuilderEscapeHatch(TestCase):
    """attach()/attach_to_current() for elements without a dedicated method."""

    def _base(self):
        return (ODMBuilder()
                .set_file(FileOID="F.EH", FileType="Snapshot",
                          CreationDateTime="2024-01-01T00:00:00")
                .add_study(OID="S.EH", study_name="EH",
                           study_description="d", protocol_name="P.EH")
                .add_metadata_version(OID="MDV.EH", Name="V1"))

    def test_attach_to_current_routes_to_accepting_parent(self):
        import odmlib.odm_1_3_2.model as M
        # Presentation has no add_* method but is a valid MDV child.
        b = self._base()
        b.attach_to_current(M.Presentation(OID="PR.1", _content="bold"))
        odm = b.build()
        self.assertEqual(
            odm.Study[0].MetaDataVersion[0].Presentation[0].OID, "PR.1")

    def test_attach_explicit_parent_via_current(self):
        import odmlib.odm_1_3_2.model as M
        b = (self._base()
             .add_item_group_def(OID="IG.DM", Name="DM", Repeating="No"))
        b.attach(b.current["item_group_def"],
                 M.Alias(Context="SDTM", Name="DM"))
        odm = b.build()
        igd = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertEqual(igd.Alias[0].Name, "DM")

    def test_attach_non_odmelement_raises(self):
        b = self._base()
        with self.assertRaises(TypeError):
            b.attach_to_current({"not": "an element"})

    def test_attach_to_incompatible_parent_raises(self):
        import odmlib.odm_1_3_2.model as M
        b = (self._base()
             .add_item_group_def(OID="IG.DM", Name="DM", Repeating="No")
             .add_item_def(OID="IT.X", Name="X", DataType="text"))
        # ItemDef cannot hold a CodeList; explicit attach must reject it.
        with self.assertRaises(TypeError):
            b.attach(b.current["item_def"],
                     M.CodeList(OID="CL.1", Name="C", DataType="text"))

    def test_current_property_keys(self):
        b = self._base().add_item_group_def(OID="IG.DM", Name="DM",
                                            Repeating="No")
        cur = b.current
        self.assertEqual(cur["mdv"].OID, "MDV.EH")
        self.assertEqual(cur["item_group_def"].OID, "IG.DM")
        self.assertIsNone(cur["item_def"])
