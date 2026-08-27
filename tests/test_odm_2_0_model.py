"""ODM 2.0 model: construction, round-trip, and v0.2.0 safe-subset coverage.

Dedicated odm_2_0 element suite, begun with the v0.2.0 ODM 2.0 Model/XSD
remediation and extended through the v0.2.1 alignment phases (see
``ODM_XSD_ALIGNMENT.md``). Covers:

- ``TranslatedText.Type`` is required (XSD-aligned) + permissive escape.
- ``Arm`` / ``CheckValue`` de-duplication (descriptor-consistent).
- the newly-registered odm_2_0 value-set keys (accept + strict reject +
  permissive bypass), and the value sets that match the XSD exactly.
- general construction + XML/JSON/dict round-trip for the major classes.
- one section per alignment phase: shape, XSD child order, schema validity
  and loader round-trip for every class that phase changed.

The conftest autouse fixture resets the NamespaceRegistry before each test,
so every setUp re-registers the ODM 2.0 namespace set.
"""
import json
import os
import tempfile
from unittest import TestCase

import odmlib.odm_2_0.model as ODM2
import odmlib.ns_registry as NS
import odmlib.typed as T
from odmlib.mode import permissive, ValidationMode
from odmlib.exceptions import OdmlibRequiredAttributeError, OdmlibTypeError


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


def _tt(content="text", lang="en"):
    return ODM2.TranslatedText(_content=content, lang=lang, Type="text/plain")


# ---------------------------------------------------------------------------
# 3.6 -- TranslatedText.Type required
# ---------------------------------------------------------------------------

class TestTranslatedTextV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_type_is_required(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM2.TranslatedText(_content="Subject Age", lang="en")

    def test_with_type_constructs_and_serializes(self):
        tt = _tt("Subject Age")
        self.assertEqual(tt.Type, "text/plain")
        self.assertEqual(tt.to_xml().attrib["Type"], "text/plain")
        self.assertEqual(json.loads(tt.to_json())["Type"], "text/plain")

    def test_permissive_skip_required_allows_missing_type(self):
        # Construction must not raise under SKIP_REQUIRED; the required-check
        # also fires on *access*, so read Type while still permissive.
        with permissive(ValidationMode.SKIP_REQUIRED):
            tt = ODM2.TranslatedText(_content="x", lang="en")
            self.assertIsNone(tt.Type)
        self.assertEqual(tt._content, "x")

    def test_description_round_trip(self):
        desc = ODM2.Description(TranslatedText=[_tt("Hello")])
        data = json.loads(desc.to_json())
        self.assertEqual(data["TranslatedText"][0]["_content"], "Hello")
        self.assertEqual(data["TranslatedText"][0]["Type"], "text/plain")


# ---------------------------------------------------------------------------
# 3.8 -- Arm / CheckValue de-duplication
# ---------------------------------------------------------------------------

class TestArmCheckValueDedup(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_descriptor_classes_are_consistent(self):
        self.assertIs(ODM2.Arm,
                       ODM2.StudyStructure._elems["Arm"].element_class)
        self.assertIs(ODM2.CheckValue,
                       ODM2.RangeCheck._elems["CheckValue"].element_class)

    def test_single_class_definition(self):
        import inspect
        src = inspect.getsource(ODM2)
        self.assertEqual(src.count("class Arm(OE.ODMElement):"), 1)
        self.assertEqual(src.count("class CheckValue(OE.ODMElement):"), 1)

    def test_range_check_builds_with_check_value(self):
        rc = ODM2.RangeCheck(Comparator="GE",
                              CheckValue=[ODM2.CheckValue(_content="0")])
        self.assertEqual(rc.CheckValue[0]._content, "0")
        self.assertIsInstance(rc.CheckValue[0], ODM2.CheckValue)

    def test_study_structure_builds_with_arm(self):
        ss = ODM2.StudyStructure(
            Arm=[ODM2.Arm(OID="ARM.A", Name="Arm A")])
        self.assertEqual(ss.Arm[0].OID, "ARM.A")
        self.assertIsInstance(ss.Arm[0], ODM2.Arm)


# ---------------------------------------------------------------------------
# 3.9 -- the 12 newly-registered odm_2_0 value-set keys
# ---------------------------------------------------------------------------

class TestValueSetKeysV2(TestCase):
    """Each newly-registered key: a valid value constructs; an invalid value
    raises OdmlibTypeError in strict mode and is accepted under SKIP_VALUESET.
    """

    def setUp(self):
        _setup_odm2_namespaces()

    def _accept(self, factory):
        obj = factory()
        self.assertIsNotNone(obj)

    def _reject_strict_accept_permissive(self, factory):
        with self.assertRaises(OdmlibTypeError):
            factory()
        with permissive(ValidationMode.SKIP_VALUESET):
            self.assertIsNotNone(factory())

    def test_item_ref_core(self):
        self._accept(lambda: ODM2.ItemRef(ItemOID="I1", Mandatory="Yes", Core="Req"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.ItemRef(ItemOID="I1", Mandatory="Yes", Core="BOGUS"))

    def test_item_ref_repeat_other_isnonstandard_hasnodata(self):
        for attr in ("Repeat", "Other", "IsNonStandard", "HasNoData"):
            self._accept(lambda a=attr: ODM2.ItemRef(
                ItemOID="I1", Mandatory="Yes", **{a: "Yes"}))
            self._reject_strict_accept_permissive(lambda a=attr: ODM2.ItemRef(
                ItemOID="I1", Mandatory="Yes", **{a: "No"}))

    def test_item_group_def_isnonstandard_hasnodata(self):
        for attr in ("IsNonStandard", "HasNoData"):
            self._accept(lambda a=attr: ODM2.ItemGroupDef(
                OID="IG1", Name="G", Repeating="No", Type="Dataset",
                **{a: "Yes"}))
            self._reject_strict_accept_permissive(lambda a=attr: ODM2.ItemGroupDef(
                OID="IG1", Name="G", Repeating="No", Type="Dataset",
                **{a: "No"}))

    def test_code_list_isnonstandard(self):
        self._accept(lambda: ODM2.CodeList(
            OID="CL1", Name="C", DataType="text", IsNonStandard="Yes"))
        self._reject_strict_accept_permissive(lambda: ODM2.CodeList(
            OID="CL1", Name="C", DataType="text", IsNonStandard="No"))

    def test_code_list_item_other(self):
        self._accept(lambda: ODM2.CodeListItem(CodedValue="C", Other="Yes"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.CodeListItem(CodedValue="C", Other="No"))

    def test_telecom_type(self):
        self._accept(lambda: ODM2.Telecom(TelecomType="Email", Value="a@b.c"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.Telecom(TelecomType="Smoke", Value="a@b.c"))

    def test_odm_context(self):
        self._accept(lambda: ODM2.ODM(
            FileOID="F1", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", Context="Submission"))
        self._reject_strict_accept_permissive(lambda: ODM2.ODM(
            FileOID="F1", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", Context="Nope"))

    def test_return_value_data_type(self):
        self._accept(lambda: ODM2.ReturnValue(Name="rv", DataType="integer"))
        self._reject_strict_accept_permissive(
            lambda: ODM2.ReturnValue(Name="rv", DataType="bogus"))


# ---------------------------------------------------------------------------
# General construction + round-trip
# ---------------------------------------------------------------------------

class TestRoundTripV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_item_def_xml_json_dict(self):
        item = ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer",
                            Description=ODM2.Description(
                                TranslatedText=[_tt("Subject Age")]))
        self.assertEqual(item.to_xml().attrib["OID"], "IT.AGE")
        self.assertEqual(json.loads(item.to_json())["DataType"], "integer")
        self.assertEqual(item.to_dict()["Name"], "Age")
        self.assertEqual(
            item.Description.TranslatedText[0]._content, "Subject Age")

    def test_item_group_def_round_trip(self):
        igd = ODM2.ItemGroupDef(OID="IG.AE", Name="AE", Repeating="No",
                                Type="Dataset")
        igd.ItemRef.append(ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes",
                                        Core="Req"))
        data = json.loads(igd.to_json())
        self.assertEqual(data["OID"], "IG.AE")
        self.assertEqual(data["ItemRef"][0]["Core"], "Req")

    def test_minimal_odm_document_round_trip(self):
        odm = ODM2.ODM(FileOID="F.TEST", FileType="Snapshot",
                       CreationDateTime="2026-01-01T00:00:00",
                       Context="Submission")
        study = ODM2.Study(OID="S.TEST", StudyName="S", ProtocolName="P",
                           Description=ODM2.Description(
                               TranslatedText=[_tt("A study")]))
        odm.Study.append(study)
        data = json.loads(odm.to_json())
        self.assertEqual(data["FileOID"], "F.TEST")
        self.assertEqual(data["Context"], "Submission")
        self.assertEqual(data["Study"][0]["OID"], "S.TEST")
        self.assertEqual(
            data["Study"][0]["Description"]["TranslatedText"][0]["Type"],
            "text/plain")


# ---------------------------------------------------------------------------
# v0.2.1 ODM 2.0 Model/XSD alignment -- round-trip for the changed classes
#
# Shape assertions live in test_odm_2_0_known_gaps.py; these cover behaviour:
# construction, serialization order, XML/JSON round-trip, and (for the whole
# document) validation against the bundled ODM 2.0 XSD.
# ---------------------------------------------------------------------------

class TestAlignmentRoundTripV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_formal_expression_code_round_trip(self):
        """A2: the expression lives in a Code child, not in element text."""
        fe = ODM2.FormalExpression(Context="Python",
                                   Code=ODM2.Code(_content="age >= 18"))
        self.assertEqual([e.tag for e in fe.to_xml()], ["Code"])
        self.assertEqual(json.loads(fe.to_json())["Code"]["_content"],
                         "age >= 18")

    def test_formal_expression_external_code_lib_round_trip(self):
        """A2: the other arm of the XSD choice."""
        fe = ODM2.FormalExpression(
            Context="SAS",
            ExternalCodeLib=ODM2.ExternalCodeLib(Library="sdtm-macros",
                                                 Method="AGECHK", Version="1.2"))
        data = json.loads(fe.to_json())
        self.assertEqual(data["ExternalCodeLib"]["Library"], "sdtm-macros")
        self.assertEqual(data["ExternalCodeLib"]["Method"], "AGECHK")

    def test_formal_expression_rejects_content(self):
        """A2: the removed text form is a hard error, not a silent no-op."""
        with self.assertRaises(OdmlibTypeError):
            ODM2.FormalExpression(Context="Python", _content="age >= 18")

    def test_condition_def_children_in_xsd_order(self):
        """A1: Description, MethodSignature, FormalExpression, Alias."""
        cd = ODM2.ConditionDef(
            OID="CND.1", Name="Adult",
            Description=ODM2.Description(TranslatedText=[_tt("Adult")]),
            MethodSignature=ODM2.MethodSignature(
                Parameter=[ODM2.Parameter(Name="age", DataType="integer")]),
            FormalExpression=[ODM2.FormalExpression(
                Context="Python", Code=ODM2.Code(_content="age >= 18"))])
        self.assertEqual([e.tag for e in cd.to_xml()],
                         ["Description", "MethodSignature", "FormalExpression"])
        data = json.loads(cd.to_json())
        self.assertEqual(data["MethodSignature"]["Parameter"][0]["Name"], "age")

    def test_protocol_children_in_xsd_order(self):
        """A3/A4: StudyStructure, StudyTimings, StudyEventGroupRef, WorkflowRef."""
        proto = ODM2.Protocol(
            Description=ODM2.Description(TranslatedText=[_tt("Protocol")]),
            StudyStructure=ODM2.StudyStructure(
                Arm=[ODM2.Arm(OID="ARM.A", Name="A")],
                Epoch=[ODM2.Epoch(OID="EP.1", Name="Screening",
                                  SequenceNumber=1)]),
            StudyTimings=ODM2.StudyTimings(
                StudyTiming=[ODM2.StudyTiming(OID="ST.1", Name="Main")]),
            StudyEventGroupRef=[ODM2.StudyEventGroupRef(
                StudyEventGroupOID="SEG.1", OrderNumber=1, Mandatory="Yes")],
            WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"))
        self.assertEqual([e.tag for e in proto.to_xml()],
                         ["Description", "StudyStructure", "StudyTimings",
                          "StudyEventGroupRef", "WorkflowRef"])
        data = json.loads(proto.to_json())
        self.assertEqual(data["StudyTimings"]["StudyTiming"][0]["OID"], "ST.1")

    def test_study_event_group_def_round_trip(self):
        """A5: the child group, plus optional ArmOID/EpochOID and CommentOID."""
        seg = ODM2.StudyEventGroupDef(
            OID="SEG.1", Name="Group", CommentOID="COM.1",
            StudyEventGroupRef=[ODM2.StudyEventGroupRef(
                StudyEventGroupOID="SEG.2", Mandatory="No")],
            StudyEventRef=[ODM2.StudyEventRef(StudyEventOID="SE.1",
                                              Mandatory="Yes")],
            WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"),
            Coding=[ODM2.Coding(Code="C1", System="http://example.org/ct")])
        self.assertIsNone(seg.ArmOID)
        self.assertIsNone(seg.EpochOID)
        self.assertEqual([e.tag for e in seg.to_xml()],
                         ["StudyEventGroupRef", "StudyEventRef", "WorkflowRef",
                          "Coding"])
        data = json.loads(seg.to_json())
        self.assertEqual(data["CommentOID"], "COM.1")

    def test_comment_def_and_leaf_round_trip(self):
        """CommentDef takes several DocumentRefs; DocumentRef uses LeafID."""
        cd = ODM2.CommentDef(
            OID="COM.1",
            Description=ODM2.Description(TranslatedText=[_tt("A comment")]),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1"),
                         ODM2.DocumentRef(LeafID="LF.2")])
        self.assertEqual([d.LeafID for d in cd.DocumentRef], ["LF.1", "LF.2"])
        leaf = ODM2.Leaf(ID="LF.1", href="crf.pdf",
                         Title=ODM2.Title(_content="CRF"))
        self.assertEqual(json.loads(leaf.to_json())["Title"]["_content"], "CRF")

    def test_source_item_resource_selection_round_trip(self):
        """SourceItem carries Resource elements, not flattened attributes."""
        si = ODM2.SourceItem(
            ItemOID="IT.AGE", MetaDataVersionOID="MDV.1", StudyOID="S.1",
            leafID="LF.1", Name="age source",
            Resource=[ODM2.Resource(
                Type="EHR", Name="demographics", Attribute="birth_date",
                Selection=[ODM2.Selection(Path="/patient/birthDate")])])
        self.assertEqual([e.tag for e in si.to_xml()], ["Resource"])
        data = json.loads(si.to_json())
        self.assertEqual(data["Resource"][0]["Selection"][0]["Path"],
                         "/patient/birthDate")

    def test_source_item_rejects_removed_attributes(self):
        """The four non-XSD attributes are gone, not silently accepted."""
        for attr in ("Attribute", "Path", "Label"):
            with self.assertRaises(OdmlibTypeError):
                ODM2.SourceItem(**{attr: "x"})

    def test_metadata_version_has_no_study_timing(self):
        """A4: timing moved to Protocol/StudyTimings."""
        with self.assertRaises(OdmlibTypeError):
            ODM2.MetaDataVersion(OID="MDV.1", Name="V1",
                                 StudyTiming=ODM2.StudyTiming(OID="ST.1",
                                                              Name="Main"))


class TestAlignmentSchemaValidV2(TestCase):
    """A document exercising every changed class must satisfy the ODM 2.0 XSD."""

    def setUp(self):
        _setup_odm2_namespaces()

    @staticmethod
    def _build():
        proto = ODM2.Protocol(
            StudyStructure=ODM2.StudyStructure(
                Arm=[ODM2.Arm(OID="ARM.A", Name="A")],
                Epoch=[ODM2.Epoch(OID="EP.1", Name="Screening",
                                  SequenceNumber=1)]),
            StudyTimings=ODM2.StudyTimings(StudyTiming=[
                ODM2.StudyTiming(OID="ST.1", Name="Main",
                                 AbsoluteTimingConstraint=[
                                     ODM2.AbsoluteTimingConstraint(
                                         OID="ATC.1", Name="Window",
                                         StudyEventOID="SE.1",
                                         TimepointTarget="2024-01-01T00:00:00",
                                         TimepointPreWindow="P1W",
                                         TimepointPostWindow="P1W")])]),
            StudyEventGroupRef=[ODM2.StudyEventGroupRef(
                StudyEventGroupOID="SEG.1", OrderNumber=1, Mandatory="Yes")])
        seg = ODM2.StudyEventGroupDef(
            OID="SEG.1", Name="Group", ArmOID="ARM.A", EpochOID="EP.1",
            CommentOID="COM.1",
            StudyEventRef=[ODM2.StudyEventRef(
                StudyEventOID="SE.1", OrderNumber=1, Mandatory="Yes",
                CollectionExceptionConditionOID="CND.1")])
        cond = ODM2.ConditionDef(
            OID="CND.1", Name="Adult",
            Description=ODM2.Description(TranslatedText=[_tt("Adult")]),
            MethodSignature=ODM2.MethodSignature(
                ReturnValue=[ODM2.ReturnValue(Name="r", DataType="boolean")]),
            FormalExpression=[
                ODM2.FormalExpression(Context="Python",
                                      Code=ODM2.Code(_content="age >= 18")),
                ODM2.FormalExpression(
                    Context="SAS",
                    ExternalCodeLib=ODM2.ExternalCodeLib(Library="macros"))])
        si = ODM2.SourceItem(
            ItemOID="IT.AGE", leafID="LF.1", Name="src",
            Resource=[ODM2.Resource(Type="EHR", Name="demographics",
                                    Selection=[ODM2.Selection(Path="/age")])])
        ir = ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1,
                          Origin=[ODM2.Origin(
                              Type="Collected",
                              SourceItems=ODM2.SourceItems(SourceItem=[si]))])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1", Protocol=proto,
            StudyEventGroupDef=[seg],
            StudyEventDef=[ODM2.StudyEventDef(
                OID="SE.1", Name="Visit", Repeating="No", Type="Scheduled",
                ItemGroupRef=[ODM2.ItemGroupRef(ItemGroupOID="IG.DM",
                                                Mandatory="Yes",
                                                OrderNumber=1)])],
            ItemGroupDef=[ODM2.ItemGroupDef(OID="IG.DM", Name="DM",
                                            Repeating="No", Type="Dataset",
                                            ItemRef=[ir])],
            ItemDef=[ODM2.ItemDef(OID="IT.AGE", Name="Age",
                                  DataType="integer")],
            ConditionDef=[cond],
            CommentDef=[ODM2.CommentDef(
                OID="COM.1",
                Description=ODM2.Description(TranslatedText=[_tt("Comment")]),
                DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])],
            Leaf=[ODM2.Leaf(ID="LF.1", href="crf.pdf",
                            Title=ODM2.Title(_content="CRF"))])
        return ODM2.ODM(
            FileOID="F.ALIGN", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", ODMVersion="2.0",
            Granularity="Metadata", Originator="odmlib",
            Study=[ODM2.Study(OID="S.1", StudyName="S", ProtocolName="P",
                              MetaDataVersion=[mdv])])

    def test_document_validates_against_xsd(self):
        from odmlib.odm_parser import ODMSchemaValidator
        odm = self._build()
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_alignment.xml")
            odm.write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)

    def test_document_oid_references_resolve(self):
        from odmlib import create_oid_checker
        self._build().verify_oids(create_oid_checker("odm_2_0"))

    def test_document_round_trips_through_loader(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_alignment.xml")
            self._build().write_xml(out)
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
            loader.open_odm_document(out)
            mdv = loader.MetaDataVersion()
        self.assertEqual(
            mdv.Protocol.StudyEventGroupRef[0].StudyEventGroupOID, "SEG.1")
        self.assertEqual(mdv.Protocol.StudyTimings.StudyTiming[0].OID, "ST.1")
        self.assertEqual(mdv.StudyEventGroupDef[0].StudyEventRef[0].StudyEventOID,
                         "SE.1")
        self.assertEqual(mdv.ConditionDef[0].FormalExpression[0].Code._content,
                         "age >= 18")
        self.assertEqual(
            mdv.ConditionDef[0].FormalExpression[1].ExternalCodeLib.Library,
            "macros")
        self.assertEqual(mdv.CommentDef[0].DocumentRef[0].LeafID, "LF.1")
        self.assertEqual(mdv.Leaf[0].Title._content, "CRF")
        src = mdv.ItemGroupDef[0].ItemRef[0].Origin[0].SourceItems.SourceItem[0]
        self.assertEqual(src.Resource[0].Selection[0].Path, "/age")


# ---------------------------------------------------------------------------
# Phase 1 of ODM_XSD_ALIGNMENT.md -- members that made output schema-invalid
# ---------------------------------------------------------------------------

class TestPhase1AlignmentV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_telecom_value_is_capitalised(self):
        """TelecomAttributeDefinition spells it Value, not value."""
        tel = ODM2.Telecom(TelecomType="Email", Value="a@example.org")
        self.assertEqual(tel.to_xml().attrib["Value"], "a@example.org")
        with self.assertRaises(OdmlibTypeError):
            ODM2.Telecom(TelecomType="Email", value="a@example.org")

    def test_workflow_end_carries_text(self):
        """WorkflowEnd is xs:simpleContent over text."""
        end = ODM2.WorkflowEnd(EndOID="SE.1", _content="trial complete")
        self.assertEqual(end.to_xml().text, "trial complete")

    def test_odm_has_no_archival_attribute(self):
        """Archival is not in ODMAttributeDefinition."""
        with self.assertRaises(OdmlibTypeError):
            ODM2.ODM(FileOID="F.1", FileType="Snapshot",
                     CreationDateTime="2026-01-01T00:00:00", Archival="Yes")

    def test_origin_children_in_xsd_order(self):
        """XSD sequence is Description, SourceItems, DocumentRef."""
        origin = ODM2.Origin(
            Type="Collected",
            Description=ODM2.Description(TranslatedText=[_tt("From the CRF")]),
            SourceItems=ODM2.SourceItems(SourceItem=[ODM2.SourceItem(
                Resource=[ODM2.Resource(Type="EHR", Name="demographics")])]),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])
        self.assertEqual([e.tag for e in origin.to_xml()],
                         ["Description", "SourceItems", "DocumentRef"])

    def test_relative_timing_constraint_oids(self):
        """The XSD names PredecessorOID/SuccessorOID, not the four-way split."""
        rtc = ODM2.RelativeTimingConstraint(
            OID="RTC.1", Name="Gap", PredecessorOID="SE.1", SuccessorOID="SE.2",
            Type="FinishToStart", TimepointRelativeTarget="P1W",
            TimepointPreWindow="P1W", TimepointPostWindow="P1W")
        self.assertEqual(rtc.PredecessorOID, "SE.1")
        for removed in ("PredecessorStudyEventOID", "SuccessorStudyEventGroupOID"):
            with self.assertRaises(OdmlibTypeError):
                ODM2.RelativeTimingConstraint(
                    OID="RTC.2", Name="X", TimepointRelativeTarget="P1W",
                    TimepointPreWindow="P1W", TimepointPostWindow="P1W",
                    **{removed: "SE.1"})

    def test_transition_timing_constraint_target(self):
        """TimepointRelativeTarget -> TimepointTarget, and Type was missing."""
        ttc = ODM2.TransitionTimingConstraint(
            OID="TTC.1", Name="Gap", TransitionOID="TR.1", Type="StartToStart",
            TimepointTarget="P2W", TimepointPreWindow="P1W",
            TimepointPostWindow="P1W")
        self.assertEqual(ttc.TimepointTarget, "P2W")
        self.assertEqual(ttc.Type, "StartToStart")
        with self.assertRaises(OdmlibTypeError):
            ODM2.TransitionTimingConstraint(
                OID="TTC.2", Name="X", TransitionOID="TR.1",
                TimepointRelativeTarget="P2W", TimepointPreWindow="P1W",
                TimepointPostWindow="P1W")

    def test_timing_windows_accept_general_iso8601_durations(self):
        """durationDatetime is a union including the full xs:duration form."""
        atc = ODM2.AbsoluteTimingConstraint(
            OID="ATC.1", Name="Window", StudyEventOID="SE.1",
            TimepointTarget="2024-01-01T00:00:00",
            TimepointPreWindow="P3D", TimepointPostWindow="PT12H")
        self.assertEqual((atc.TimepointPreWindow, atc.TimepointPostWindow),
                         ("P3D", "PT12H"))

    def test_user_prefix_suffix_are_elements(self):
        """The XSD models Prefix/Suffix as User children, not attributes."""
        user = ODM2.User(OID="U.1", UserType="Investigator",
                         Prefix=ODM2.Prefix(_content="Dr"),
                         Suffix=ODM2.Suffix(_content="PhD"),
                         UserName=ODM2.UserName(_content="jsmith"))
        self.assertEqual([e.tag for e in user.to_xml()],
                         ["UserName", "Prefix", "Suffix"])
        with self.assertRaises(OdmlibTypeError):
            ODM2.User(OID="U.2", Prefix="Dr")

    def test_user_has_no_display_name(self):
        """DisplayName is not part of the ODM 2.0 XSD."""
        self.assertFalse(hasattr(ODM2, "DisplayName"))
        self.assertNotIn("DisplayName", ODM2.User._elems)

    def test_organization_is_an_admindata_element(self):
        """Organization was a text leaf carried over from ODM 1.3.2."""
        org = ODM2.Organization(
            OID="ORG.1", Name="Acme CRO", Type="CRO", Role="Data management",
            Telecom=[ODM2.Telecom(TelecomType="Email", Value="ops@acme.org")])
        self.assertEqual([e.tag for e in org.to_xml()], ["Telecom"])
        self.assertIn("Organization", ODM2.AdminData._elems)
        with self.assertRaises(OdmlibTypeError):
            ODM2.Organization(_content="Acme CRO")

    def test_organization_type_is_value_set_checked(self):
        with self.assertRaises(OdmlibTypeError):
            ODM2.Organization(OID="ORG.1", Name="Acme", Type="NotAnOrgType")

    def test_document_ref_leafid_resolves_to_leaf(self):
        """LeafID -> Leaf/@ID is checked like any other reference."""
        from odmlib import create_oid_checker
        comment = ODM2.CommentDef(
            OID="COM.1",
            Description=ODM2.Description(TranslatedText=[_tt("A comment")]),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1", CommentDef=[comment],
            ItemGroupDef=[ODM2.ItemGroupDef(OID="IG.1", Name="IG",
                                            Repeating="No", Type="Dataset")],
            Leaf=[ODM2.Leaf(ID="LF.1", href="crf.pdf",
                            Title=ODM2.Title(_content="CRF"))])
        mdv.verify_oids(create_oid_checker("odm_2_0"))

    def test_dangling_leafid_is_rejected(self):
        from odmlib import create_oid_checker
        from odmlib.exceptions import OdmlibOIDError
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            ItemGroupDef=[ODM2.ItemGroupDef(OID="IG.1", Name="IG",
                                            Repeating="No", Type="Dataset")],
            CommentDef=[ODM2.CommentDef(
                OID="COM.1",
                Description=ODM2.Description(TranslatedText=[_tt("c")]),
                DocumentRef=[ODM2.DocumentRef(LeafID="LF.MISSING")])])
        with self.assertRaises(OdmlibOIDError):
            mdv.verify_oids(create_oid_checker("odm_2_0"))


class TestPhase1SchemaValidV2(TestCase):
    """An AdminData document exercising every Phase 1 class must satisfy the XSD."""

    def setUp(self):
        _setup_odm2_namespaces()

    @staticmethod
    def _build():
        user = ODM2.User(
            OID="U.1", UserType="Investigator", OrganizationOID="ORG.1",
            UserName=ODM2.UserName(_content="jsmith"),
            Prefix=ODM2.Prefix(_content="Dr"),
            Suffix=ODM2.Suffix(_content="PhD"),
            GivenName=ODM2.GivenName(_content="Jane"),
            FamilyName=ODM2.FamilyName(_content="Smith"),
            Telecom=[ODM2.Telecom(TelecomType="Email", Value="jane@example.org")])
        org = ODM2.Organization(
            OID="ORG.1", Name="Acme CRO", Type="CRO",
            Telecom=[ODM2.Telecom(TelecomType="Phone", Value="+1-555-0100")])
        admin = ODM2.AdminData(StudyOID="S.1", User=[user], Organization=[org])
        wf = ODM2.WorkflowDef(
            OID="WF.1", Name="Main",
            WorkflowStart=ODM2.WorkflowStart(StartOID="SE.1"),
            WorkflowEnd=[ODM2.WorkflowEnd(EndOID="SE.1",
                                          _content="trial complete")])
        timings = ODM2.StudyTimings(StudyTiming=[ODM2.StudyTiming(
            OID="ST.1", Name="Main",
            RelativeTimingConstraint=[ODM2.RelativeTimingConstraint(
                OID="RTC.1", Name="Gap", PredecessorOID="SE.1",
                SuccessorOID="SE.1", Type="FinishToStart",
                TimepointRelativeTarget="P3D", TimepointPreWindow="P1D",
                TimepointPostWindow="P1D")],
            TransitionTimingConstraint=[ODM2.TransitionTimingConstraint(
                OID="TTC.1", Name="Gap", TransitionOID="TR.1",
                Type="StartToStart", TimepointTarget="PT12H",
                TimepointPreWindow="PT1H", TimepointPostWindow="PT1H")])])
        origin = ODM2.Origin(
            Type="Collected",
            Description=ODM2.Description(TranslatedText=[_tt("From the CRF")]),
            SourceItems=ODM2.SourceItems(SourceItem=[ODM2.SourceItem(
                ItemOID="IT.AGE",
                Resource=[ODM2.Resource(Type="EHR", Name="demographics")])]),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])
        igd = ODM2.ItemGroupDef(
            OID="IG.DM", Name="DM", Repeating="No", Type="Dataset",
            ItemRef=[ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes",
                                  OrderNumber=1, Origin=[origin])])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            Protocol=ODM2.Protocol(StudyTimings=timings),
            WorkflowDef=[wf], ItemGroupDef=[igd],
            ItemDef=[ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer")],
            Leaf=[ODM2.Leaf(ID="LF.1", href="crf.pdf",
                            Title=ODM2.Title(_content="CRF"))])
        return ODM2.ODM(
            FileOID="F.PHASE1", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", ODMVersion="2.0",
            Granularity="All", Originator="odmlib",
            Study=[ODM2.Study(OID="S.1", StudyName="S", ProtocolName="P",
                              MetaDataVersion=[mdv])],
            AdminData=[admin])

    def test_document_validates_against_xsd(self):
        from odmlib.odm_parser import ODMSchemaValidator
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase1.xml")
            self._build().write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)

    def test_document_round_trips_through_loader(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase1.xml")
            self._build().write_xml(out)
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
            loader.open_odm_document(out)
            odm = loader.root()
        admin = odm.AdminData[0]
        self.assertEqual(admin.Organization[0].Name, "Acme CRO")
        self.assertEqual(admin.User[0].Prefix._content, "Dr")
        self.assertEqual(admin.User[0].Telecom[0].Value, "jane@example.org")
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.WorkflowDef[0].WorkflowEnd[0]._content,
                         "trial complete")
        timing = mdv.Protocol.StudyTimings.StudyTiming[0]
        self.assertEqual(timing.RelativeTimingConstraint[0].PredecessorOID, "SE.1")
        self.assertEqual(timing.TransitionTimingConstraint[0].TimepointTarget,
                         "PT12H")


# ---------------------------------------------------------------------------
# Phase 2 of ODM_XSD_ALIGNMENT.md -- required flags and cardinality
# ---------------------------------------------------------------------------

class TestPhase2AlignmentV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    # -- model was stricter than the XSD: these no longer raise -------------

    def test_formal_expression_context_is_optional(self):
        fe = ODM2.FormalExpression(Code=ODM2.Code(_content="x > 1"))
        self.assertIsNone(fe.Context)

    def test_method_def_type_is_optional(self):
        md = ODM2.MethodDef(
            OID="MT.1", Name="M",
            Description=ODM2.Description(TranslatedText=[_tt("d")]))
        self.assertIsNone(md.Type)

    def test_target_transition_condition_is_optional(self):
        tt = ODM2.TargetTransition(TargetTransitionOID="TR.1")
        self.assertIsNone(tt.ConditionOID)

    def test_timing_windows_are_optional(self):
        """All four timing constraints mark their windows use="optional"."""
        atc = ODM2.AbsoluteTimingConstraint(
            OID="ATC.1", Name="W", TimepointTarget="2024-01-01T00:00:00")
        rtc = ODM2.RelativeTimingConstraint(
            OID="RTC.1", Name="W", TimepointRelativeTarget="P1W")
        ttc = ODM2.TransitionTimingConstraint(
            OID="TTC.1", Name="W", TransitionOID="TR.1", TimepointTarget="P1W")
        dtc = ODM2.DurationTimingConstraint(
            OID="DTC.1", Name="W", StructuralElementOID="SE.1",
            DurationTarget="P1W")
        for obj, attr in ((atc, "TimepointPreWindow"), (rtc, "TimepointPostWindow"),
                          (ttc, "TimepointPreWindow"), (dtc, "DurationPostWindow")):
            self.assertIsNone(getattr(obj, attr))

    # -- model was looser than the XSD: these are now required --------------

    def test_standard_status_is_required(self):
        """Status is use="required" in StandardAttributeDefinition."""
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM2.Standard(OID="STD.1", Name="SDTMIG", Type="IG", Version="3.4")
        std = ODM2.Standard(OID="STD.1", Name="SDTMIG", Type="IG",
                            Version="3.4", Status="Final")
        self.assertEqual(std.Status, "Final")

    def test_required_child_elements_are_declared(self):
        """Element requiredness is declarative -- it does not raise on build."""
        self.assertTrue(ODM2.Leaf._elems["Title"].required)
        self.assertTrue(ODM2.MethodDef._elems["MethodSignature"].required)
        self.assertTrue(ODM2.Study._elems["MetaDataVersion"].required)

    # -- cardinality --------------------------------------------------------

    def test_annotated_crf_takes_several_document_refs(self):
        """DocumentRef is maxOccurs="unbounded" on AnnotatedCRF and SupplementalDoc."""
        for cls in (ODM2.AnnotatedCRF, ODM2.SupplementalDoc):
            obj = cls(DocumentRef=[ODM2.DocumentRef(LeafID="LF.1"),
                                   ODM2.DocumentRef(LeafID="LF.2")])
            self.assertEqual([d.LeafID for d in obj.DocumentRef], ["LF.1", "LF.2"])

    def test_study_timing_takes_several_transition_constraints(self):
        timing = ODM2.StudyTiming(
            OID="ST.1", Name="Main",
            TransitionTimingConstraint=[
                ODM2.TransitionTimingConstraint(OID="TTC.1", Name="A",
                                                TransitionOID="TR.1",
                                                TimepointTarget="P1W"),
                ODM2.TransitionTimingConstraint(OID="TTC.2", Name="B",
                                                TransitionOID="TR.2",
                                                TimepointTarget="P2W")])
        self.assertEqual([t.OID for t in timing.TransitionTimingConstraint],
                         ["TTC.1", "TTC.2"])

    def test_workflow_ref_is_single_where_the_xsd_says_so(self):
        """maxOccurs=1 on ItemGroupDef, StudyEventDef and StudyStructure."""
        igd = ODM2.ItemGroupDef(OID="IG.1", Name="IG", Repeating="No",
                                Type="Dataset",
                                WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"))
        sed = ODM2.StudyEventDef(OID="SE.1", Name="V", Repeating="No",
                                 Type="Scheduled",
                                 WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"))
        ss = ODM2.StudyStructure(WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"))
        for obj in (igd, sed, ss):
            self.assertEqual(obj.WorkflowRef.WorkflowOID, "WF.1")
        # The descriptor kind is what changed. ODMObject.__set__ still
        # tolerates a list (see typed.py), so odmlib does not enforce the
        # cardinality at assignment -- XSD validation is what catches it.
        for cls in (ODM2.ItemGroupDef, ODM2.StudyEventDef, ODM2.StudyStructure):
            self.assertNotIsInstance(cls._elems["WorkflowRef"], T.ODMListObject)

    def test_address_street_name_is_single(self):
        addr = ODM2.Address(StreetName=ODM2.StreetName(_content="1 Main St"))
        self.assertEqual(addr.StreetName._content, "1 Main St")

    def test_metadata_version_standards_is_single(self):
        """Standards is maxOccurs=1; the several Standard entries live inside it."""
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            Standards=ODM2.Standards(Standard=[
                ODM2.Standard(OID="STD.1", Name="SDTMIG", Type="IG",
                              Version="3.4", Status="Final"),
                ODM2.Standard(OID="STD.2", Name="CDISC/NCI", Type="CT",
                              Version="2024-03-29", Status="Final")]))
        self.assertEqual([s.OID for s in mdv.Standards.Standard],
                         ["STD.1", "STD.2"])

    def test_phase2_document_validates_and_round_trips(self):
        """Standards and repeated transition constraints in a real document."""
        from odmlib.odm_parser import ODMSchemaValidator
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        timings = ODM2.StudyTimings(StudyTiming=[ODM2.StudyTiming(
            OID="ST.1", Name="Main",
            TransitionTimingConstraint=[
                ODM2.TransitionTimingConstraint(OID="TTC.1", Name="A",
                                                TransitionOID="TR.1",
                                                TimepointTarget="P1W"),
                ODM2.TransitionTimingConstraint(OID="TTC.2", Name="B",
                                                TransitionOID="TR.2",
                                                TimepointTarget="P2W")])])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            Standards=ODM2.Standards(Standard=[
                ODM2.Standard(OID="STD.1", Name="SDTMIG", Type="IG",
                              Version="3.4", Status="Final")]),
            Protocol=ODM2.Protocol(StudyTimings=timings),
            ItemGroupDef=[ODM2.ItemGroupDef(OID="IG.DM", Name="DM",
                                            Repeating="No", Type="Dataset",
                                            StandardOID="STD.1")],
            ItemDef=[ODM2.ItemDef(OID="IT.AGE", Name="Age", DataType="integer")])
        odm = ODM2.ODM(
            FileOID="F.PHASE2", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", ODMVersion="2.0",
            Granularity="Metadata", Originator="odmlib",
            Study=[ODM2.Study(OID="S.1", StudyName="S", ProtocolName="P",
                              MetaDataVersion=[mdv])])
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase2.xml")
            odm.write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
            loader.open_odm_document(out)
            rt = loader.MetaDataVersion()
        self.assertEqual(rt.Standards.Standard[0].Status, "Final")
        self.assertEqual(
            [t.OID for t in rt.Protocol.StudyTimings.StudyTiming[0]
             .TransitionTimingConstraint], ["TTC.1", "TTC.2"])


# ---------------------------------------------------------------------------
# Phase 3 of ODM_XSD_ALIGNMENT.md -- missing members and the small new classes
# ---------------------------------------------------------------------------

class TestPhase3AlignmentV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_new_attributes_are_accepted(self):
        self.assertEqual(
            ODM2.Include(StudyOID="S.1", MetaDataVersionOID="MDV.1",
                         href="other.xml").href, "other.xml")
        self.assertEqual(
            ODM2.PDFPageRef(Type="PhysicalRef", Title="CRF page").Title,
            "CRF page")
        self.assertEqual(
            ODM2.ItemGroupRef(ItemGroupOID="IG.1", Mandatory="Yes",
                              MethodOID="MT.1").MethodOID, "MT.1")
        self.assertEqual(
            ODM2.Location(OID="L.1", Name="Site 1",
                          OrganizationOID="ORG.1").OrganizationOID, "ORG.1")
        igd = ODM2.ItemGroupDef(OID="IG.1", Name="IG", Repeating="No",
                                Type="Dataset", Structure="One record per subject",
                                ArchiveLocationID="LF.1")
        self.assertEqual(igd.Structure, "One record per subject")
        self.assertEqual(igd.ArchiveLocationID, "LF.1")

    def test_code_list_item_extended_value_is_value_set_checked(self):
        """The CodeListItem.ExtendedValue key was dead until the attribute landed."""
        self.assertEqual(
            ODM2.CodeListItem(CodedValue="C", ExtendedValue="Yes").ExtendedValue,
            "Yes")
        with self.assertRaises(OdmlibTypeError):
            ODM2.CodeListItem(CodedValue="C", ExtendedValue="Maybe")

    def test_class_and_subclass(self):
        """ODM 2.0 models the dataset class as an element, not an attribute."""
        cls = ODM2.Class(Name="FINDINGS", SubClass=[
            ODM2.SubClass(Name="TIME-TO-EVENT", ParentClass="FINDINGS")])
        self.assertEqual([e.tag for e in cls.to_xml()], ["SubClass"])
        self.assertEqual(cls.SubClass[0].ParentClass, "FINDINGS")
        with self.assertRaises(OdmlibTypeError):
            ODM2.Class(Name="NOT A CLASS")
        with self.assertRaises(OdmlibTypeError):
            ODM2.ItemGroupDef(OID="IG.1", Name="IG", Repeating="No",
                              Type="Dataset", Class="FINDINGS")

    def test_item_group_def_children_in_xsd_order(self):
        igd = ODM2.ItemGroupDef(
            OID="IG.1", Name="IG", Repeating="No", Type="Dataset",
            Description=ODM2.Description(TranslatedText=[_tt("d")]),
            Class=ODM2.Class(Name="EVENTS"),
            ItemRef=[ODM2.ItemRef(ItemOID="IT.1", Mandatory="Yes")],
            Coding=[ODM2.Coding(Code="C1", System="http://example.org")],
            WorkflowRef=ODM2.WorkflowRef(WorkflowOID="WF.1"),
            Leaf=ODM2.Leaf(ID="LF.1", href="ig.pdf",
                           Title=ODM2.Title(_content="IG")))
        self.assertEqual([e.tag for e in igd.to_xml()],
                         ["Description", "Class", "ItemRef", "Coding",
                          "WorkflowRef", "Leaf"])

    def test_value_list_ref_on_item_def(self):
        item = ODM2.ItemDef(OID="IT.1", Name="I", DataType="text",
                            ValueListRef=ODM2.ValueListRef(ValueListOID="VL.1"))
        self.assertEqual(item.ValueListRef.ValueListOID, "VL.1")

    def test_range_check_item_oid_and_method_signature(self):
        rc = ODM2.RangeCheck(
            Comparator="EQ", SoftHard="Hard", ItemOID="IT.1",
            MethodSignature=ODM2.MethodSignature(
                Parameter=[ODM2.Parameter(Name="v", DataType="text")]),
            FormalExpression=[ODM2.FormalExpression(
                Context="Python", Code=ODM2.Code(_content="v == 'Y'"))])
        self.assertEqual([e.tag for e in rc.to_xml()],
                         ["MethodSignature", "FormalExpression"])
        self.assertEqual(rc.ItemOID, "IT.1")

    def test_coding_children_added(self):
        for obj, tag in (
            (ODM2.Origin(Type="Collected",
                         Coding=[ODM2.Coding(Code="C", System="s")]), "Coding"),
            (ODM2.SourceItems(
                SourceItem=[ODM2.SourceItem(
                    Resource=[ODM2.Resource(Type="EHR", Name="r")])],
                Coding=[ODM2.Coding(Code="C", System="s")]), "Coding"),
            (ODM2.StudyEventDef(OID="SE.1", Name="V", Repeating="No",
                                Type="Scheduled",
                                Coding=[ODM2.Coding(Code="C", System="s")]),
             "Coding"),
        ):
            self.assertIn(tag, [e.tag for e in obj.to_xml()])

    def test_method_def_document_ref(self):
        md = ODM2.MethodDef(
            OID="MT.1", Name="M", Type="Computation",
            Description=ODM2.Description(TranslatedText=[_tt("d")]),
            MethodSignature=ODM2.MethodSignature(),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])
        self.assertEqual([e.tag for e in md.to_xml()][-1], "DocumentRef")

    def test_address_house_number_and_geo_position(self):
        addr = ODM2.Address(
            StreetName=ODM2.StreetName(_content="Main St"),
            HouseNumber=ODM2.HouseNumber(_content="42"),
            GeoPosition=ODM2.GeoPosition(Longitude=-0.1276, Latitude=51.5072))
        self.assertEqual([e.tag for e in addr.to_xml()],
                         ["StreetName", "HouseNumber", "GeoPosition"])
        self.assertEqual(addr.GeoPosition.Latitude, 51.5072)

    def test_location_children(self):
        loc = ODM2.Location(
            OID="L.1", Name="Site 1", OrganizationOID="ORG.1",
            Description=ODM2.Description(TranslatedText=[_tt("A site")]),
            MetaDataVersionRef=[ODM2.MetaDataVersionRef(
                StudyOID="S.1", MetaDataVersionOID="MDV.1",
                EffectiveDate="2026-01-01")],
            Address=[ODM2.Address(City=ODM2.City(_content="London"))],
            Telecom=[ODM2.Telecom(TelecomType="Phone", Value="+44-20-0000")])
        self.assertEqual([e.tag for e in loc.to_xml()],
                         ["Description", "MetaDataVersionRef", "Address", "Telecom"])

    def test_metadata_version_document_and_value_list_children(self):
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            AnnotatedCRF=ODM2.AnnotatedCRF(
                DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")]),
            SupplementalDoc=ODM2.SupplementalDoc(
                DocumentRef=[ODM2.DocumentRef(LeafID="LF.2")]),
            ValueListDef=[ODM2.ValueListDef(OID="VL.1")],
            WhereClauseDef=[ODM2.WhereClauseDef(
                OID="WC.1",
                RangeCheck=[ODM2.RangeCheck(Comparator="EQ", ItemOID="IT.1")])])
        self.assertEqual([e.tag for e in mdv.to_xml()][:4],
                         ["AnnotatedCRF", "SupplementalDoc", "ValueListDef",
                          "WhereClauseDef"])


class TestPhase3SchemaValidV2(TestCase):
    """A document exercising every Phase 3 member must satisfy the XSD."""

    def setUp(self):
        _setup_odm2_namespaces()

    @staticmethod
    def _build():
        igd = ODM2.ItemGroupDef(
            OID="IG.DM", Name="DM", Repeating="No", Type="Dataset",
            Structure="One record per subject", ArchiveLocationID="LF.1",
            Class=ODM2.Class(Name="FINDINGS", SubClass=[
                ODM2.SubClass(Name="TIME-TO-EVENT", ParentClass="FINDINGS")]),
            ItemRef=[ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes",
                                  OrderNumber=1,
                                  Origin=[ODM2.Origin(
                                      Type="Collected",
                                      Coding=[ODM2.Coding(Code="C1",
                                                          System="http://x")])])],
            Coding=[ODM2.Coding(Code="C2", System="http://x")],
            Leaf=ODM2.Leaf(ID="LF.2", href="ig.pdf",
                           Title=ODM2.Title(_content="IG")))
        itd = ODM2.ItemDef(
            OID="IT.AGE", Name="Age", DataType="integer",
            RangeCheck=[ODM2.RangeCheck(
                Comparator="GE", SoftHard="Hard", ItemOID="IT.AGE",
                MethodSignature=ODM2.MethodSignature(
                    Parameter=[ODM2.Parameter(Name="v", DataType="integer")]),
                FormalExpression=[ODM2.FormalExpression(
                    Context="Python", Code=ODM2.Code(_content="v >= 0"))])],
            ValueListRef=ODM2.ValueListRef(ValueListOID="VL.1"))
        method = ODM2.MethodDef(
            OID="MT.1", Name="Derive", Type="Computation",
            Description=ODM2.Description(TranslatedText=[_tt("d")]),
            MethodSignature=ODM2.MethodSignature(),
            DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1",
            Include=ODM2.Include(StudyOID="S.0", MetaDataVersionOID="MDV.0",
                                 href="prior.xml"),
            AnnotatedCRF=ODM2.AnnotatedCRF(DocumentRef=[
                ODM2.DocumentRef(LeafID="LF.1", PDFPageRef=[ODM2.PDFPageRef(
                    Type="PhysicalRef", PageRefs="1", Title="Page one")])]),
            SupplementalDoc=ODM2.SupplementalDoc(
                DocumentRef=[ODM2.DocumentRef(LeafID="LF.1")]),
            ValueListDef=[ODM2.ValueListDef(
                OID="VL.1",
                ItemRef=[ODM2.ItemRef(ItemOID="IT.AGE", Mandatory="Yes")])],
            WhereClauseDef=[ODM2.WhereClauseDef(
                OID="WC.1",
                RangeCheck=[ODM2.RangeCheck(
                    Comparator="EQ", ItemOID="IT.AGE",
                    CheckValue=[ODM2.CheckValue(_content="18")])])],
            StudyEventDef=[ODM2.StudyEventDef(
                OID="SE.1", Name="V", Repeating="No", Type="Scheduled",
                ItemGroupRef=[ODM2.ItemGroupRef(ItemGroupOID="IG.DM",
                                                Mandatory="Yes", OrderNumber=1,
                                                MethodOID="MT.1")],
                Coding=[ODM2.Coding(Code="C3", System="http://x")])],
            ItemGroupDef=[igd], ItemDef=[itd], MethodDef=[method],
            CodeList=[ODM2.CodeList(
                OID="CL.1", Name="Sex", DataType="text",
                CodeListItem=[ODM2.CodeListItem(CodedValue="M",
                                                ExtendedValue="Yes")])],
            Leaf=[ODM2.Leaf(ID="LF.1", href="crf.pdf",
                            Title=ODM2.Title(_content="CRF"))])
        admin = ODM2.AdminData(
            StudyOID="S.1",
            Location=[ODM2.Location(
                OID="L.1", Name="Site 1", OrganizationOID="ORG.1",
                Description=ODM2.Description(TranslatedText=[_tt("A site")]),
                MetaDataVersionRef=[ODM2.MetaDataVersionRef(
                    StudyOID="S.1", MetaDataVersionOID="MDV.1",
                    EffectiveDate="2026-01-01")],
                Address=[ODM2.Address(
                    StreetName=ODM2.StreetName(_content="Main St"),
                    HouseNumber=ODM2.HouseNumber(_content="42"),
                    GeoPosition=ODM2.GeoPosition(Longitude=-0.1276,
                                                 Latitude=51.5072))],
                Telecom=[ODM2.Telecom(TelecomType="Phone",
                                      Value="+44-20-0000")])],
            Organization=[ODM2.Organization(OID="ORG.1", Name="Acme",
                                            Type="CRO")])
        return ODM2.ODM(
            FileOID="F.PHASE3", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", ODMVersion="2.0",
            Granularity="All", Originator="odmlib",
            Study=[ODM2.Study(OID="S.1", StudyName="S", ProtocolName="P",
                              MetaDataVersion=[mdv])],
            AdminData=[admin])

    def test_document_validates_against_xsd(self):
        from odmlib.odm_parser import ODMSchemaValidator
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase3.xml")
            self._build().write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)

    def test_document_round_trips_through_loader(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase3.xml")
            self._build().write_xml(out)
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
            loader.open_odm_document(out)
            odm = loader.root()
        mdv = odm.Study[0].MetaDataVersion[0]
        self.assertEqual(mdv.Include.href, "prior.xml")
        self.assertEqual(mdv.AnnotatedCRF.DocumentRef[0].PDFPageRef[0].Title,
                         "Page one")
        self.assertEqual(mdv.ValueListDef[0].OID, "VL.1")
        self.assertEqual(mdv.WhereClauseDef[0].RangeCheck[0].ItemOID, "IT.AGE")
        self.assertEqual(mdv.ItemGroupDef[0].Class.SubClass[0].Name,
                         "TIME-TO-EVENT")
        self.assertEqual(mdv.ItemGroupDef[0].Structure, "One record per subject")
        self.assertEqual(mdv.ItemDef[0].ValueListRef.ValueListOID, "VL.1")
        self.assertEqual(mdv.MethodDef[0].DocumentRef[0].LeafID, "LF.1")
        self.assertEqual(mdv.CodeList[0].CodeListItem[0].ExtendedValue, "Yes")
        loc = odm.AdminData[0].Location[0]
        self.assertEqual(loc.Address[0].HouseNumber._content, "42")
        self.assertEqual(loc.Address[0].GeoPosition.Latitude, 51.5072)
        self.assertEqual(loc.Telecom[0].Value, "+44-20-0000")


# ---------------------------------------------------------------------------
# Phase 4 of ODM_XSD_ALIGNMENT.md -- the Protocol study-design subtree
# ---------------------------------------------------------------------------

class TestPhase4AlignmentV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_protocol_children_in_xsd_order(self):
        """All nine study-design children sit at their XSD sequence positions."""
        self.assertEqual(
            list(ODM2.Protocol._elems),
            ["Description", "StudySummary", "StudyStructure", "TrialPhase",
             "StudyTimings", "StudyIndications", "StudyInterventions",
             "StudyObjectives", "StudyEndPoints", "StudyTargetPopulation",
             "StudyEstimands", "InclusionExclusionCriteria",
             "StudyEventGroupRef", "WorkflowRef", "Alias"])

    def test_study_summary_parameters(self):
        summary = ODM2.StudySummary(StudyParameter=[ODM2.StudyParameter(
            OID="SP.1", Term="Trial Blinding Schema", ShortName="Blinding",
            ParameterValue=ODM2.ParameterValue(
                Value="Double Blind",
                Coding=[ODM2.Coding(Code="C15228", System="http://ncit")]))])
        self.assertEqual(summary.StudyParameter[0].ParameterValue.Value,
                         "Double Blind")
        self.assertEqual([e.tag for e in summary.StudyParameter[0].to_xml()],
                         ["ParameterValue"])

    def test_trial_phase_value_is_an_extensible_vocabulary(self):
        """TrialPhaseType is a union of an enumeration with xs:string."""
        import odmlib.valueset as VS
        self.assertEqual(ODM2.TrialPhase(Value="PHASE III TRIAL").Value,
                         "PHASE III TRIAL")
        # a term outside the CT list is schema-valid and must be accepted
        self.assertEqual(ODM2.TrialPhase(Value="PHASE XI TRIAL").Value,
                         "PHASE XI TRIAL")
        self.assertIn("PHASE III TRIAL",
                      VS.ValueSet.describe("TrialPhase.Value", version="odm_2_0"))

    def test_objective_and_endpoint_levels_are_value_set_checked(self):
        """StudyObjective.Level was unvalidated -- its key was truncated."""
        desc = ODM2.Description(TranslatedText=[_tt("d")])
        self.assertEqual(
            ODM2.StudyObjective(OID="OBJ.1", Name="O", Level="Primary").Level,
            "Primary")
        with self.assertRaises(OdmlibTypeError):
            ODM2.StudyObjective(OID="OBJ.2", Name="O", Level="Tertiary")
        with self.assertRaises(OdmlibTypeError):
            ODM2.StudyEndPoint(OID="EP.1", Name="E", Description=desc,
                               Level="Tertiary")
        with self.assertRaises(OdmlibTypeError):
            ODM2.StudyEndPoint(OID="EP.2", Name="E", Description=desc,
                               Type="Complicated")

    def test_indications_and_interventions(self):
        desc = ODM2.Description(TranslatedText=[_tt("d")])
        ind = ODM2.StudyIndications(StudyIndication=[
            ODM2.StudyIndication(OID="IND.1", Description=desc)])
        itv = ODM2.StudyInterventions(StudyIntervention=[
            ODM2.StudyIntervention(OID="ITV.1", Description=desc)])
        self.assertEqual(ind.StudyIndication[0].OID, "IND.1")
        self.assertEqual(itv.StudyIntervention[0].OID, "ITV.1")

    def test_estimand_children_in_xsd_order(self):
        desc = ODM2.Description(TranslatedText=[_tt("d")])
        est = ODM2.StudyEstimand(
            OID="EST.1", Name="Primary estimand", Level="Primary",
            Description=desc,
            StudyTargetPopulationRef=ODM2.StudyTargetPopulationRef(
                StudyTargetPopulationOID="TP.1"),
            StudyInterventionRef=ODM2.StudyInterventionRef(
                StudyInterventionOID="ITV.1"),
            StudyEndPointRef=ODM2.StudyEndPointRef(StudyEndPointOID="EP.1"),
            IntercurrentEvent=[ODM2.IntercurrentEvent(Description=desc)],
            SummaryMeasure=ODM2.SummaryMeasure(Description=desc))
        self.assertEqual([e.tag for e in est.to_xml()],
                         ["Description", "StudyTargetPopulationRef",
                          "StudyInterventionRef", "StudyEndPointRef",
                          "IntercurrentEvent", "SummaryMeasure"])

    def test_inclusion_exclusion_criteria(self):
        crit = ODM2.Criterion(OID="CR.1", Name="Adult", ConditionOID="CND.1")
        iec = ODM2.InclusionExclusionCriteria(
            InclusionCriteria=ODM2.InclusionCriteria(Criterion=[crit]),
            ExclusionCriteria=ODM2.ExclusionCriteria(Criterion=[
                ODM2.Criterion(OID="CR.2", Name="Pregnant",
                               ConditionOID="CND.2")]))
        self.assertEqual([e.tag for e in iec.to_xml()],
                         ["InclusionCriteria", "ExclusionCriteria"])
        self.assertEqual(iec.InclusionCriteria.Criterion[0].ConditionOID,
                         "CND.1")


class TestValueSetsMatchTheXSDV2(TestCase):
    """Value sets must permit exactly what the XSD type permits.

    ``tests/test_odm_2_0_xsd_alignment.py`` asserts this exhaustively against
    the schema; these pin the specific corrections so a regression names itself.
    """

    def setUp(self):
        _setup_odm2_namespaces()
        # the loader caches per process; every valueset test resets it. The
        # sentinel is None -- an empty dict looks "already loaded" and leaves
        # _version_map unbuilt.
        import odmlib.valueset as VS
        VS.ValueSetLoader._cache = None
        VS.ValueSetLoader._version_map = None
        VS.ValueSet._compiled_regex_cache.clear()

    def test_method_def_type_matches_odm_2_0(self):
        """ODM 2.0 replaced `Other` with `Preload`; the list was copied from 1.3.2."""
        self.assertEqual(
            ODM2.MethodDef(OID="MT.1", Name="m", Type="Preload").Type, "Preload")
        with self.assertRaises(OdmlibTypeError):
            ODM2.MethodDef(OID="MT.2", Name="m", Type="Other")

    def test_user_type_has_all_nine_values(self):
        """ODM 2.0 added Subject, Monitor, Data analyst, Care provider, Assessor."""
        for value in ("Subject", "Monitor", "Data analyst", "Care provider",
                      "Assessor"):
            self.assertEqual(ODM2.User(OID="U.1", UserType=value).UserType, value)
        with self.assertRaises(OdmlibTypeError):
            ODM2.User(OID="U.2", UserType="Bystander")

    def test_odm_version_is_a_pattern(self):
        """ODMVersion is an XSD pattern, not the single literal "2.0"."""
        def build(version):
            return ODM2.ODM(FileOID="F.1", FileType="Snapshot",
                            CreationDateTime="2026-01-01T00:00:00",
                            ODMVersion=version)
        for good in ("2.0", "2.0.1", "2.0-draft"):
            self.assertEqual(build(good).ODMVersion, good)
        for bad in ("3.0", "1.3.2", "two"):
            with self.assertRaises(OdmlibTypeError):
                build(bad)

    def test_extensible_vocabularies_accept_extension_values(self):
        """ItemGroupTypeType / TrialPhaseType / StandardStatus union with xs:string."""
        import odmlib.valueset as VS
        igd = ODM2.ItemGroupDef(OID="IG.1", Name="n", Repeating="No",
                                Type="SponsorCustom")
        self.assertEqual(igd.Type, "SponsorCustom")
        self.assertEqual(ODM2.TrialPhase(Value="PHASE XI TRIAL").Value,
                         "PHASE XI TRIAL")
        std = ODM2.Standard(OID="STD.1", Name="SDTMIG", Type="IG",
                            Version="3.4", Status="SponsorDraft")
        self.assertEqual(std.Status, "SponsorDraft")
        # the defined terms survive as documentation
        self.assertIn("Dataset",
                      VS.ValueSet.describe("ItemGroupDef.Type", version="odm_2_0"))

    def test_standard_closed_attributes_are_checked(self):
        """Name/Type/PublishingSet are closed enumerations, unchecked until now."""
        base = dict(OID="STD.1", Name="SDTMIG", Type="IG", Version="3.4",
                    Status="Final")
        self.assertEqual(ODM2.Standard(**base).Name, "SDTMIG")
        for attr, bad in (("Name", "NotAStandard"), ("Type", "XX"),
                          ("PublishingSet", "ZZ")):
            with self.assertRaises(OdmlibTypeError):
                ODM2.Standard(**{**base, attr: bad})

    def test_value_sets_are_not_borrowed_from_another_version(self):
        """These keys must live in the odm_2_0 block, not be reached by fallback.

        ``_FALLBACK_VERSIONS`` tries ``define_2_1`` first on a miss, and it is a
        superset of ``odm_1_3_2`` -- so a mistyped key resolves to Define-XML's
        values instead of raising. Checking the raw block states that directly;
        an identity comparison cannot, because the fallback also runs in the
        other direction for keys only ``odm_2_0`` has.
        """
        import json
        import odmlib.valueset as VS
        block = VS.ValueSetLoader.load_valuesets()["odm_2_0"]
        for key in ("MethodDef.Type", "User.UserType", "ODM.ODMVersion",
                    "ItemGroupDef.Type", "TrialPhase.Value", "Standard.Name",
                    "Standard.Type", "Standard.PublishingSet", "Standard.Status"):
            self.assertIn(key, block,
                          f"{key} is missing from the odm_2_0 block and would "
                          f"be resolved by cross-version fallback")


class TestPhase4SchemaValidV2(TestCase):
    """A Protocol carrying the whole study-design subtree must satisfy the XSD."""

    def setUp(self):
        _setup_odm2_namespaces()

    @staticmethod
    def _build():
        desc = lambda t: ODM2.Description(TranslatedText=[_tt(t)])
        cond = lambda oid, name: ODM2.ConditionDef(
            OID=oid, Name=name, Description=desc(name),
            MethodSignature=ODM2.MethodSignature(),
            FormalExpression=[ODM2.FormalExpression(
                Context="Python", Code=ODM2.Code(_content="True"))])
        proto = ODM2.Protocol(
            Description=desc("Study protocol"),
            StudySummary=ODM2.StudySummary(StudyParameter=[
                ODM2.StudyParameter(OID="SP.1", Term="Trial Blinding Schema",
                                    ParameterValue=ODM2.ParameterValue(
                                        Value="Double Blind"))]),
            StudyStructure=ODM2.StudyStructure(
                Arm=[ODM2.Arm(OID="ARM.A", Name="A")],
                Epoch=[ODM2.Epoch(OID="EP.SCR", Name="Screening",
                                  SequenceNumber=1)]),
            TrialPhase=ODM2.TrialPhase(Value="PHASE III TRIAL",
                                       Description=desc("Confirmatory")),
            StudyIndications=ODM2.StudyIndications(StudyIndication=[
                ODM2.StudyIndication(OID="IND.1", Description=desc("Hypertension"))]),
            StudyInterventions=ODM2.StudyInterventions(StudyIntervention=[
                ODM2.StudyIntervention(OID="ITV.1", Description=desc("Drug X"))]),
            StudyObjectives=ODM2.StudyObjectives(StudyObjective=[
                ODM2.StudyObjective(OID="OBJ.1", Name="Primary objective",
                                    Level="Primary", Description=desc("Efficacy"),
                                    StudyEndPointRef=[ODM2.StudyEndPointRef(
                                        StudyEndPointOID="EP.1", OrderNumber=1)])]),
            StudyEndPoints=ODM2.StudyEndPoints(StudyEndPoint=[
                ODM2.StudyEndPoint(OID="EP.1", Name="Change in BP",
                                   Type="Simple", Level="Primary",
                                   Description=desc("Change from baseline"),
                                   FormalExpression=[ODM2.FormalExpression(
                                       Context="Python",
                                       Code=ODM2.Code(_content="bp - base"))])]),
            StudyTargetPopulation=ODM2.StudyTargetPopulation(
                OID="TP.1", Name="Adults", Description=desc("Adults 18+"),
                Coding=[ODM2.Coding(Code="C1", System="http://ncit")]),
            StudyEstimands=ODM2.StudyEstimands(StudyEstimand=[
                ODM2.StudyEstimand(
                    OID="EST.1", Name="Primary estimand", Level="Primary",
                    Description=desc("Treatment effect"),
                    StudyTargetPopulationRef=ODM2.StudyTargetPopulationRef(
                        StudyTargetPopulationOID="TP.1"),
                    StudyInterventionRef=ODM2.StudyInterventionRef(
                        StudyInterventionOID="ITV.1"),
                    StudyEndPointRef=ODM2.StudyEndPointRef(
                        StudyEndPointOID="EP.1"),
                    IntercurrentEvent=[ODM2.IntercurrentEvent(
                        Description=desc("Rescue medication"))],
                    SummaryMeasure=ODM2.SummaryMeasure(
                        Description=desc("Difference in means")))]),
            InclusionExclusionCriteria=ODM2.InclusionExclusionCriteria(
                InclusionCriteria=ODM2.InclusionCriteria(Criterion=[
                    ODM2.Criterion(OID="CR.1", Name="Adult",
                                   ConditionOID="CND.1",
                                   Description=desc("Aged 18 or over"))]),
                ExclusionCriteria=ODM2.ExclusionCriteria(Criterion=[
                    ODM2.Criterion(OID="CR.2", Name="Pregnant",
                                   ConditionOID="CND.2")])),
            StudyEventGroupRef=[ODM2.StudyEventGroupRef(
                StudyEventGroupOID="SEG.1", OrderNumber=1, Mandatory="Yes")])
        mdv = ODM2.MetaDataVersion(
            OID="MDV.1", Name="V1", Protocol=proto,
            StudyEventGroupDef=[ODM2.StudyEventGroupDef(
                OID="SEG.1", Name="G", ArmOID="ARM.A", EpochOID="EP.SCR",
                StudyEventRef=[ODM2.StudyEventRef(StudyEventOID="SE.1",
                                                  Mandatory="Yes")])],
            StudyEventDef=[ODM2.StudyEventDef(OID="SE.1", Name="V",
                                              Repeating="No", Type="Scheduled")],
            ItemGroupDef=[ODM2.ItemGroupDef(OID="IG.1", Name="IG",
                                            Repeating="No", Type="Dataset")],
            ConditionDef=[cond("CND.1", "Adult"), cond("CND.2", "Pregnant")])
        return ODM2.ODM(
            FileOID="F.PHASE4", FileType="Snapshot",
            CreationDateTime="2026-01-01T00:00:00", ODMVersion="2.0",
            Granularity="Metadata", Originator="odmlib",
            Study=[ODM2.Study(OID="S.1", StudyName="S", ProtocolName="P",
                              MetaDataVersion=[mdv])])

    def test_document_validates_against_xsd(self):
        from odmlib.odm_parser import ODMSchemaValidator
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase4.xml")
            self._build().write_xml(out)
            ODMSchemaValidator(standard="odm", version="2.0").validate_file(out)

    def test_document_oid_references_resolve(self):
        from odmlib import create_oid_checker
        self._build().verify_oids(create_oid_checker("odm_2_0"))

    def test_document_round_trips_through_loader(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = os.path.join(tmp_dir, "odm20_phase4.xml")
            self._build().write_xml(out)
            loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
            loader.open_odm_document(out)
            proto = loader.MetaDataVersion().Protocol
        self.assertEqual(
            proto.StudySummary.StudyParameter[0].ParameterValue.Value,
            "Double Blind")
        self.assertEqual(proto.TrialPhase.Value, "PHASE III TRIAL")
        self.assertEqual(proto.StudyIndications.StudyIndication[0].OID, "IND.1")
        self.assertEqual(
            proto.StudyObjectives.StudyObjective[0].StudyEndPointRef[0]
            .StudyEndPointOID, "EP.1")
        self.assertEqual(proto.StudyEndPoints.StudyEndPoint[0].Type, "Simple")
        self.assertEqual(proto.StudyTargetPopulation.Name, "Adults")
        est = proto.StudyEstimands.StudyEstimand[0]
        self.assertEqual(est.SummaryMeasure.Description.TranslatedText[0]._content,
                         "Difference in means")
        self.assertEqual(est.IntercurrentEvent[0].Description
                         .TranslatedText[0]._content, "Rescue medication")
        self.assertEqual(
            proto.InclusionExclusionCriteria.ExclusionCriteria.Criterion[0].Name,
            "Pregnant")


# ---------------------------------------------------------------------------
# Phase 5 of ODM_XSD_ALIGNMENT.md -- deliberate approximations
#
# These pin the *documented* behaviour of the three XSD constructs odmlib's
# descriptor model cannot express. Each waiver is recorded in the class
# docstring, in README.md and in docs/source/guides/model_reference.rst; if
# one is ever closed, these tests fail and those three places must be updated
# together.
# ---------------------------------------------------------------------------

class TestPhase5WaiversV2(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_formal_expression_choice_is_not_enforced(self):
        """The XSD requires exactly one of Code | ExternalCodeLib."""
        neither = ODM2.FormalExpression(Context="Python")
        both = ODM2.FormalExpression(
            Context="Python", Code=ODM2.Code(_content="x"),
            ExternalCodeLib=ODM2.ExternalCodeLib(Library="lib"))
        # odmlib builds both happily; only the XSD rejects them
        self.assertEqual([e.tag for e in neither.to_xml()], [])
        self.assertEqual([e.tag for e in both.to_xml()],
                         ["Code", "ExternalCodeLib"])
        self.assertIn("Known approximation", ODM2.FormalExpression.__doc__)

    def test_study_event_group_def_cannot_interleave_refs(self):
        """The XSD group permits interleaving; parallel lists cannot."""
        seg = ODM2.StudyEventGroupDef(
            OID="SEG.1", Name="G",
            StudyEventGroupRef=[ODM2.StudyEventGroupRef(
                StudyEventGroupOID="SEG.2", Mandatory="No")],
            StudyEventRef=[ODM2.StudyEventRef(StudyEventOID="SE.1",
                                              Mandatory="Yes")])
        # always grouped, never interleaved
        self.assertEqual([e.tag for e in seg.to_xml()],
                         ["StudyEventGroupRef", "StudyEventRef"])
        self.assertIn("Known approximation", ODM2.StudyEventGroupDef.__doc__)

    def test_translated_text_is_text_only(self):
        """The XSD is mixed content with an optional xhtml:div child.

        An opaque text-only div was tried in v0.2.1 and withdrawn: it could
        not carry markup either, since element text is XML-escaped on write.
        """
        self.assertFalse(hasattr(ODM2, "div"))
        self.assertEqual(list(ODM2.TranslatedText._elems), [])
        tt = _tt("plain text")
        self.assertEqual(tt.to_xml().text, "plain text")
        self.assertEqual(list(tt.to_xml()), [])
        self.assertIn("Known approximation", ODM2.TranslatedText.__doc__)

    def test_every_model_class_is_an_odm_2_0_xsd_element(self):
        """The ODM 1.3.2 carry-over classes were removed in Phase 5.

        ``tests/test_odm_2_0_xsd_alignment.py`` asserts this exhaustively;
        this names the seven that went, so the removal is not undone quietly.
        """
        for name in ("ArchiveLayout", "DisplayName", "Email", "ExceptionEvent",
                     "Fax", "Pager", "Phone", "Picture"):
            self.assertFalse(hasattr(ODM2, name),
                             f"{name} is not an ODM 2.0 XSD element")
        # what ODM 2.0 uses instead
        self.assertTrue(hasattr(ODM2, "Telecom"))
        self.assertTrue(hasattr(ODM2, "Image"))
