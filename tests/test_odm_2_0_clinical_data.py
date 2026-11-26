"""ODM v2.0 ClinicalData, ReferenceData and Association (0.3.0 plan, P4).

Until 0.3.0 the ODM 2.0 model stopped at AdminData: loading a document dropped its
ClinicalData, ReferenceData and Association without a word. This module builds every
new class, serializes it, validates it against the bundled XSD and round-trips it,
and checks the parts the XSD alignment guard cannot see:

* the ItemGroupData/ItemData interleaving (``ItemGroupDataGroup``), which leg A of
  ``test_json_roundtrip.py`` also protects on the vendored Demographics_RACE example;
* that the containers stay truthy when they hold only nested or top-level groups;
* that none of the ODM 1.3.2 shapes the plan lists was copied into 2.0;
* the loader accessors ``ODMLoader.ClinicalData()`` and ``ReferenceData()``.
"""
import json
import os
import tempfile
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.define_loader as DLD
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_1_3_2.model as ODM1
import odmlib.odm_2_0.model as ODM2
import odmlib.odm_loader as OL
from odmlib import create_oid_checker
from odmlib.exceptions import (OdmlibLoaderStateError, OdmlibRequiredAttributeError,
                               OdmlibTypeError, OdmlibValidationError)
from odmlib.odm_parser import ODMSchemaValidator

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
ODM_V2_DIR = os.path.join(DATA_DIR, "odm_v2")
ODM20 = "http://www.cdisc.org/ns/odm/v2.0"

#: The classes P4 added, in model order.
NEW_CLASSES = (
    "UserRef", "DateTimeStamp", "ReasonForChange", "SourceID", "AuditRecord", "Value",
    "Query", "SignatureRef", "Signature", "Comment", "FlagValue", "FlagType", "Flag",
    "Annotation", "InvestigatorRef", "SiteRef", "ItemData", "ItemGroupData",
    "StudyEventData", "SubjectData", "ClinicalData", "ReferenceData", "KeySet",
    "Association",
)


# ---------------------------------------------------------------------------
# A document that uses every new class, with every reference resolvable
# ---------------------------------------------------------------------------

def _text(text):
    return [ODM2.TranslatedText(_content=text, lang="en", Type="text/plain")]


def _audit(when, reason=None, source=None, **attrs):
    record = ODM2.AuditRecord(
        UserRef=ODM2.UserRef(UserOID="USR.1"),
        LocationRef=ODM2.LocationRef(LocationOID="LOC.1"),
        DateTimeStamp=ODM2.DateTimeStamp(_content=when), **attrs)
    if reason:
        record.ReasonForChange = ODM2.ReasonForChange(_content=reason)
    if source:
        record.SourceID = ODM2.SourceID(_content=source)
    return record


def _signature(signature_id):
    return ODM2.Signature(
        ID=signature_id,
        UserRef=ODM2.UserRef(UserOID="USR.1"),
        LocationRef=ODM2.LocationRef(LocationOID="LOC.1"),
        SignatureRef=ODM2.SignatureRef(SignatureOID="SIG.1"),
        DateTimeStamp=ODM2.DateTimeStamp(_content="2026-03-01T10:00:00Z"))


def _annotation(seq, **attrs):
    annotation = ODM2.Annotation(SeqNum=seq, **attrs)
    annotation.Comment = ODM2.Comment(SponsorOrSite="Site", TranslatedText=_text("Checked"))
    annotation.Coding = [ODM2.Coding(Code="10019211", System="https://www.meddra.org")]
    annotation.Flag = [ODM2.Flag(FlagValue=ODM2.FlagValue(CodeListOID="CL.FLAG", _content="REVIEWED"),
                                 FlagType=ODM2.FlagType(CodeListOID="CL.FLAGTYPE", _content="STATUS"))]
    return annotation


def _query(oid, text, **attrs):
    query = ODM2.Query(OID=oid, Source="Data Management", State="Open", Type="Manual",
                       LastUpdateDatetime="2026-03-02T09:00:00", Name="Q", **attrs)
    query.Value = ODM2.Value(_content=text)
    query.AuditRecord = [_audit("2026-03-02T09:00:00", reason="Raised")]
    return query


def _metadata():
    mdv = ODM2.MetaDataVersion(OID="MDV.1", Name="Metadata")
    sed = ODM2.StudyEventDef(OID="SE.1", Name="Screening", Repeating="No", Type="Scheduled")
    sed.ItemGroupRef = [ODM2.ItemGroupRef(ItemGroupOID="IG.FORM", Mandatory="Yes")]
    mdv.StudyEventDef = [sed]
    form = ODM2.ItemGroupDef(OID="IG.FORM", Name="Form", Repeating="No", Type="Form")
    form.ItemRef = [ODM2.ItemRef(ItemOID="IT.A", Mandatory="No")]
    form.ItemGroupRef = [ODM2.ItemGroupRef(ItemGroupOID="IG.ROW", Mandatory="No")]
    row = ODM2.ItemGroupDef(OID="IG.ROW", Name="Row", Repeating="Simple", Type="Section")
    row.ItemRef = [ODM2.ItemRef(ItemOID="IT.B", Mandatory="No")]
    lab = ODM2.ItemGroupDef(OID="IG.LAB", Name="Ranges", Repeating="Simple", Type="Dataset",
                            IsReferenceData="Yes")
    lab.ItemRef = [ODM2.ItemRef(ItemOID="IT.LOW", Mandatory="No")]
    mdv.ItemGroupDef = [form, row, lab]
    mdv.ItemDef = [ODM2.ItemDef(OID=oid, Name=oid, DataType="text")
                   for oid in ("IT.A", "IT.B", "IT.LOW")]
    mdv.CodeList = [
        ODM2.CodeList(OID="CL.FLAG", Name="Flag values", DataType="text",
                      CodeListItem=[ODM2.CodeListItem(CodedValue="REVIEWED")]),
        ODM2.CodeList(OID="CL.FLAGTYPE", Name="Flag types", DataType="text",
                      CodeListItem=[ODM2.CodeListItem(CodedValue="STATUS")]),
    ]
    return ODM2.Study(OID="ST.1", StudyName="Study", ProtocolName="P-1", MetaDataVersion=[mdv])


def _admin_data():
    location = ODM2.Location(OID="LOC.1", Name="Site 1")
    location.MetaDataVersionRef = [ODM2.MetaDataVersionRef(
        StudyOID="ST.1", MetaDataVersionOID="MDV.1", EffectiveDate="2026-01-01")]
    location.Query = [_query("Q.LOC", "Confirm the site address")]
    signature_def = ODM2.SignatureDef(
        OID="SIG.1", Methodology="Electronic",
        Meaning=ODM2.Meaning(_content="Approval"),
        LegalReason=ODM2.LegalReason(_content="I approve these data"))
    return ODM2.AdminData(StudyOID="ST.1", User=[ODM2.User(OID="USR.1")],
                          Location=[location], SignatureDef=[signature_def])


def _row(repeat, value):
    group = ODM2.ItemGroupData(ItemGroupOID="IG.ROW", ItemGroupRepeatKey=str(repeat))
    group.ItemData = [ODM2.ItemData(ItemOID="IT.B", Value=[ODM2.Value(_content=value)])]
    return group


def _form():
    """IT.A, then two nested rows, then a null IT.A: ItemData on both sides of the groups."""
    form = ODM2.ItemGroupData(ItemGroupOID="IG.FORM", TransactionType="Insert",
                              ItemGroupDataSeq=1)
    first = ODM2.ItemData(ItemOID="IT.A", TransactionType="Insert")
    first.Value = [ODM2.Value(SeqNum=2, _content="second"), ODM2.Value(SeqNum=1, _content="first")]
    first.AuditRecord = _audit("2026-03-01T09:00:00", reason="Entered", source="CRF p1",
                               EditPoint="DataManagement", UsedMethod="No")
    first.Signature = _signature("SIGN.ITEM")
    first.Annotation = [_annotation(1, TransactionType="Insert", ID="ANN.1")]
    first.Query = [_query("Q.IT", "Please confirm")]
    form.ItemData.append(first)
    form.ItemGroupData.append(_row(1, "x"))
    form.ItemGroupData.append(_row(2, "y"))
    form.ItemData.append(ODM2.ItemData(ItemOID="IT.A", IsNull="Yes"))
    form.AuditRecord = _audit("2026-03-01T09:30:00")
    form.Annotation = [_annotation(1)]
    return form


def _clinical_data():
    clinical = ODM2.ClinicalData(StudyOID="ST.1", MetaDataVersionOID="MDV.1")
    subject = ODM2.SubjectData(SubjectKey="001", TransactionType="Insert")
    subject.InvestigatorRef = ODM2.InvestigatorRef(UserOID="USR.1")
    subject.SiteRef = ODM2.SiteRef(LocationOID="LOC.1")
    event = ODM2.StudyEventData(StudyEventOID="SE.1", StudyEventRepeatKey="1")
    event.ItemGroupData = [_form()]
    event.Signature = _signature("SIGN.EVENT")
    subject.StudyEventData = [event]
    subject.AuditRecord = _audit("2026-03-01T08:00:00")
    clinical.SubjectData = [subject]
    clinical.ItemGroupData = [_row(9, "site-level")]
    clinical.Query = [_query("Q.CD", "Transfer incomplete")]
    return clinical


def _reference_data():
    reference = ODM2.ReferenceData(StudyOID="ST.1", MetaDataVersionOID="MDV.1")
    lab = ODM2.ItemGroupData(ItemGroupOID="IG.LAB", ItemGroupRepeatKey="1")
    lab.ItemData = [ODM2.ItemData(ItemOID="IT.LOW", Value=[ODM2.Value(_content="3.5")])]
    reference.ItemGroupData = [lab]
    reference.Annotation = [_annotation(1)]
    return reference


def _association():
    return ODM2.Association(
        StudyOID="ST.1", MetaDataVersionOID="MDV.1",
        KeySet=[ODM2.KeySet(StudyOID="ST.1", SubjectKey="001", MetaDataVersionOID="MDV.1",
                            StudyEventOID="SE.1", StudyEventRepeatKey="1",
                            ItemGroupOID="IG.FORM", ItemOID="IT.A"),
                ODM2.KeySet(StudyOID="ST.1", MetaDataVersionOID="MDV.1",
                            ItemGroupOID="IG.LAB", ItemGroupRepeatKey="1", ItemOID="IT.LOW")],
        Annotation=_annotation(1))


def full_document():
    """An ODM 2.0 document that uses each of the 24 new classes at least once."""
    return ODM2.ODM(
        FileType="Snapshot", Granularity="All", FileOID="ODM.P4.1", ODMVersion="2.0",
        CreationDateTime="2026-03-03T12:00:00",
        Study=[_metadata()], AdminData=[_admin_data()], ReferenceData=[_reference_data()],
        ClinicalData=[_clinical_data()], Association=[_association()])


def _first_instances(root):
    """``{class name: first instance}`` for every element in the tree, depth first."""
    found, stack = {}, [root]
    while stack:
        element = stack.pop()
        found.setdefault(type(element).__name__, element)
        for value in reversed(list(vars(element).values())):
            if isinstance(value, list):
                stack.extend(reversed([v for v in value if isinstance(v, ODM2.OE.ODMElement)]))
            elif isinstance(value, ODM2.OE.ODMElement):
                stack.append(value)
    return found


def _load_xml_string(xml, key=None):
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
    return loader.create_odmlib(loader.load_odm_string(xml), key)


def _load_json_string(text, key):
    loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_2_0"))
    return loader.create_odmlib(loader.load_odm_string(text), key)


def _xsd_errors(validator, source):
    return [str(e).splitlines()[0] for e in validator.xsd.iter_errors(source)]


class _ODM20(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.validator = ODMSchemaValidator(standard="odm", version="2.0")

    def setUp(self):
        NS.NamespaceRegistry(prefix="odm", uri=ODM20, is_default=True, is_reset=True)


# ---------------------------------------------------------------------------
# Build, serialize, validate, round-trip
# ---------------------------------------------------------------------------

class TestEveryClass(_ODM20):
    """Each new class builds, serializes, validates and round-trips through XML and JSON."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NS.NamespaceRegistry(prefix="odm", uri=ODM20, is_default=True, is_reset=True)
        cls.document = full_document()
        cls.instances = _first_instances(cls.document)

    def test_full_document_uses_every_new_class(self):
        self.assertEqual(sorted(set(NEW_CLASSES) - set(self.instances)), [])
        self.assertEqual(len(NEW_CLASSES), 24)

    def test_full_document_validates_against_the_xsd(self):
        self.assertEqual(_xsd_errors(self.validator, self.document.to_xml_string()), [])

    def test_full_document_passes_verify_oids(self):
        self.assertTrue(self.document.verify_oids(create_oid_checker("odm_2_0")))

    def test_each_class_validates_on_its_own(self):
        """Every new element is a global XSD element, so each can be validated as a root."""
        for name in NEW_CLASSES:
            with self.subTest(element=name):
                xml = self.instances[name].to_xml_string()
                self.assertEqual(ET.fromstring(xml).tag, f"{{{ODM20}}}{name}")
                self.assertEqual(_xsd_errors(self.validator, xml), [])

    def test_each_class_round_trips_through_xml(self):
        for name in NEW_CLASSES:
            with self.subTest(element=name):
                element = self.instances[name]
                reloaded = _load_xml_string(element.to_xml_string())
                self.assertIs(type(reloaded), type(element))
                self.assertEqual(reloaded.to_dict(), element.to_dict())
                self.assertEqual(reloaded.to_xml_string(), element.to_xml_string())

    def test_each_class_round_trips_through_json(self):
        for name in NEW_CLASSES:
            with self.subTest(element=name):
                element = self.instances[name]
                reloaded = _load_json_string(element.to_json(), name)
                self.assertEqual(reloaded.to_dict(), element.to_dict())

    def test_full_document_round_trips_through_a_file(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = os.path.join(folder.name, "p4.xml")
        self.document.write_xml(path)
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(path)
        self.assertEqual(loader.root().to_dict(), self.document.to_dict())
        self.assertEqual(_xsd_errors(self.validator, path), [])


class TestInterleaving(_ODM20):
    """ItemGroupData and ItemData children may alternate (the ItemGroupDataGroup)."""

    def test_itemdata_before_nested_itemgroupdata_round_trips(self):
        """The Demographics_RACE order: items, nested groups, then more items."""
        form = _form()
        order = [type(c).__name__ for c in form.children("ItemGroupData", "ItemData")]
        self.assertEqual(order, ["ItemData", "ItemGroupData", "ItemGroupData", "ItemData"])
        xml = form.to_xml_string()
        written = [child.tag.split("}")[1] for child in ET.fromstring(xml)]
        self.assertEqual(written[:4], order)
        reloaded = _load_xml_string(xml)
        self.assertEqual([type(c).__name__ for c in reloaded.children("ItemGroupData", "ItemData")],
                         order)
        self.assertEqual(reloaded.to_xml_string(), xml)

    def test_json_keeps_one_array_per_type(self):
        """ODM 2.0 JSON cannot carry the interleaving: groups come back before items."""
        reloaded = _load_json_string(_form().to_json(), "ItemGroupData")
        self.assertEqual([type(c).__name__ for c in reloaded.children("ItemGroupData", "ItemData")],
                         ["ItemGroupData", "ItemGroupData", "ItemData", "ItemData"])

    def test_nested_group_is_an_item_group_data(self):
        """``T.SELF`` resolved: the nested list holds ItemGroupData."""
        descriptor = ODM2.ItemGroupData._elems["ItemGroupData"]
        self.assertIs(descriptor.element_class, ODM2.ItemGroupData)
        self.assertEqual(ODM2.ItemGroupData._groups,
                         {"ItemGroupDataGroup": ("ItemGroupData", "ItemData")})

    def test_vendored_demographics_race_keeps_its_order(self):
        path = os.path.join(ODM_V2_DIR, "github", "Demographics_RACE",
                            "Demographics_RACE_check_all_that_apply.xml")
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(path)
        demographics = loader.ClinicalData()[0][0][0].ItemGroupData[0]
        kinds = [type(c).__name__ for c in demographics.children("ItemGroupData", "ItemData")]
        self.assertEqual(kinds[:4], ["ItemData", "ItemData", "ItemData", "ItemGroupData"])


class TestReferenceDataAndAssociation(_ODM20):
    """No vendored fixture has either, so these are built by hand."""

    def _document(self):
        return ODM2.ODM(FileType="Snapshot", FileOID="ODM.P4.2", ODMVersion="2.0",
                        CreationDateTime="2026-03-03T12:00:00", Study=[_metadata()],
                        AdminData=[_admin_data()], ReferenceData=[_reference_data()],
                        Association=[_association()])

    def test_reference_data_and_association_validate_against_xsd(self):
        document = self._document()
        self.assertEqual(_xsd_errors(self.validator, document.to_xml_string()), [])
        self.assertTrue(document.verify_oids(create_oid_checker("odm_2_0")))

    def test_reference_data_and_association_round_trip(self):
        document = self._document()
        xml = document.to_xml_string()
        self.assertEqual(_load_xml_string(xml).to_xml_string(), xml)
        self.assertEqual(_load_json_string(document.to_json(), "ODM").to_dict(), document.to_dict())

    def test_association_keyset_count_is_not_enforced(self):
        """The XSD wants exactly two KeySets; the model holds a list (rule X02 is P5's)."""
        association = _association()
        association.KeySet.append(ODM2.KeySet(StudyOID="ST.1"))
        self.assertEqual(len(association.KeySet), 3)
        self.assertNotEqual(_xsd_errors(self.validator, association.to_xml_string()), [])


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------

class TestContainers(_ODM20):
    """ClinicalData -> SubjectData -> StudyEventData -> ItemGroupData -> ItemData."""

    def test_container_truthy_when_only_nested_groups(self):
        clinical = ODM2.ClinicalData(StudyOID="ST.1", MetaDataVersionOID="MDV.1")
        clinical.ItemGroupData = [_row(1, "x")]
        self.assertEqual(len(clinical), 0)
        self.assertTrue(clinical)
        outer = ODM2.ItemGroupData(ItemGroupOID="IG.FORM")
        outer.ItemGroupData.append(_row(1, "x"))
        self.assertEqual(len(outer), 0)
        self.assertTrue(outer)
        for empty in (ODM2.SubjectData(SubjectKey="1"), ODM2.StudyEventData(StudyEventOID="SE.1"),
                      ODM2.ItemGroupData(ItemGroupOID="IG.1"), clinical):
            with self.subTest(container=type(empty).__name__):
                self.assertTrue(empty)

    def test_containers_iterate_one_level_down(self):
        clinical = _clinical_data()
        subject = clinical[0]
        event = subject[0]
        form = event[0]
        self.assertEqual([type(x).__name__ for x in (subject, event, form, form[0])],
                         ["SubjectData", "StudyEventData", "ItemGroupData", "ItemData"])
        self.assertEqual((len(clinical), len(subject), len(event), len(form)), (1, 1, 1, 2))
        self.assertEqual([item.ItemOID for item in form], ["IT.A", "IT.A"])
        self.assertEqual([s.SubjectKey for s in clinical], ["001"])
        self.assertEqual([e.StudyEventOID for e in subject], ["SE.1"])
        self.assertEqual([g.ItemGroupOID for g in event], ["IG.FORM"])

    def test_text_content_that_the_xsd_requires(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            ODM2.DateTimeStamp()
        for build in (lambda: ODM2.DateTimeStamp(_content="2026-02-30T00:00:00"),
                      lambda: ODM2.DateTimeStamp(_content=""),
                      lambda: ODM2.FlagValue(CodeListOID="CL.1", _content=""),
                      lambda: ODM2.FlagType(CodeListOID="CL.1", _content="")):
            with self.assertRaises(OdmlibValidationError):
                build()
        self.assertEqual(ODM2.Value().to_dict(), {})
        self.assertEqual(ODM2.ReasonForChange(_content="").to_dict(), {"_content": ""})

    def test_enumerated_attributes_are_checked(self):
        """The 12 new value sets are live (a value set violation is an OdmlibTypeError)."""
        cases = [
            (ODM2.ItemData, "TransactionType", "Delete"),
            (ODM2.ItemData, "IsNull", "No"),
            (ODM2.AuditRecord, "EditPoint", "Review"),
            (ODM2.Comment, "SponsorOrSite", "Investigator"),
            (ODM2.Query, "Source", "Investigator"),
        ]
        for cls, attr, value in cases:
            with self.subTest(element=cls.__name__, attribute=attr):
                instance = cls.__new__(cls)
                with self.assertRaises(OdmlibTypeError):
                    setattr(instance, attr, value)
        record = ODM2.AuditRecord.__new__(ODM2.AuditRecord)
        record.EditPoint = "DBAudit"
        self.assertEqual(record.EditPoint, "DBAudit")

    def test_keys_and_sequence_numbers(self):
        for build in (lambda: ODM2.SubjectData(SubjectKey=""),
                      lambda: ODM2.ItemGroupData(ItemGroupOID="IG.1", ItemGroupRepeatKey=""),
                      lambda: ODM2.Value(SeqNum=0),
                      lambda: ODM2.Annotation(SeqNum="1.5")):
            with self.assertRaises((OdmlibValidationError, OdmlibTypeError)):
                build()
        self.assertEqual(ODM2.Value(SeqNum="3").SeqNum, 3)

    def test_odm_1_3_2_shapes_were_not_copied(self):
        """The plan's list of 1.3.2 shapes that ODM 2.0 does not have."""
        self.assertFalse(hasattr(ODM2, "FormData"))
        self.assertIn("Value", ODM2.ItemData._elems)                 # a child, not an attribute
        self.assertNotIn("MeasurementUnitRef", ODM2.ItemData._elems)
        self.assertNotIn("Value", ODM2.ItemData._attrs)
        self.assertIn("Value", ODM1.ItemData._attrs)
        for name in ("SubjectData", "StudyEventData", "ItemGroupData", "ItemData"):
            with self.subTest(container=name):
                elems = list(getattr(ODM2, name)._elems)
                # AuditRecord, Signature, Annotation follow the data, then Query
                self.assertEqual(elems[-4:], ["AuditRecord", "Signature", "Annotation", "Query"])
        for name in ("AuditRecords", "Signatures", "Annotations"):
            self.assertFalse(hasattr(ODM2, name))
        self.assertIn("UsedMethod", ODM2.AuditRecord._attrs)
        self.assertNotIn("UsedImputationMethod", ODM2.AuditRecord._attrs)
        self.assertNotIn("ID", ODM2.AuditRecord._attrs)
        self.assertFalse(ODM2.Signature._attrs["ID"].required)
        self.assertNotIn("_content", ODM2.Comment._attrs)
        self.assertIn("TranslatedText", ODM2.Comment._elems)
        self.assertNotIn("FormOID", ODM2.KeySet._attrs)
        self.assertIn("MetaDataVersionOID", ODM2.KeySet._attrs)

    def test_location_holds_queries_and_odm_holds_the_data_layer(self):
        self.assertEqual(list(ODM2.Location._elems)[-1], "Query")
        self.assertEqual(list(ODM2.ODM._elems),
                         ["Description", "Study", "AdminData", "ReferenceData",
                          "ClinicalData", "Association"])


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _vendored_clinical_documents():
    with open(os.path.join(ODM_V2_DIR, "MANIFEST.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    for fixture in manifest["fixtures"]:
        if fixture["has_clinical_data"]:
            xml = next(f["path"] for f in fixture["files"] if f["path"].endswith(".xml"))
            yield xml, os.path.join(ODM_V2_DIR, xml)


class TestLoadingVendoredClinicalData(_ODM20):
    """ClinicalData is no longer dropped on load."""

    DATA_TAGS = ("ClinicalData", "SubjectData", "StudyEventData", "ItemGroupData", "ItemData",
                 "Value", "AuditRecord", "Query", "Signature", "Annotation")

    def test_clinical_data_is_loaded_not_dropped(self):
        documents = list(_vendored_clinical_documents())
        self.assertEqual(len(documents), 12)
        for name, path in documents:
            with self.subTest(file=name):
                loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
                loader.open_odm_document(path)
                written = ET.fromstring(loader.root().to_xml_string())
                source = ET.parse(path).getroot()
                for tag in self.DATA_TAGS:
                    self.assertEqual(len(written.findall(f".//{{{ODM20}}}{tag}")),
                                     len(source.findall(f".//{{{ODM20}}}{tag}")), tag)

    def test_written_clinical_data_validates_against_the_xsd(self):
        for name, path in _vendored_clinical_documents():
            with self.subTest(file=name):
                loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
                loader.open_odm_document(path)
                self.assertEqual(_xsd_errors(self.validator, loader.root().to_xml_string()), [])


class TestLoaderAccessors(_ODM20):
    """``ODMLoader.ClinicalData()`` / ``ReferenceData()`` and the loader methods behind them."""

    TRANSACTIONAL = os.path.join(ODM_V2_DIR, "templates", "clinical-data-transactional")

    def _xml_loader(self, path, model_package="odm_2_0"):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package=model_package))
        loader.open_odm_document(path)
        return loader

    def test_clinical_data_from_xml_and_json_agree(self):
        from_xml = self._xml_loader(self.TRANSACTIONAL + ".xml").ClinicalData()
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(self.TRANSACTIONAL + ".json")
        from_json = loader.ClinicalData()
        self.assertIsInstance(from_xml, ODM2.ClinicalData)
        self.assertEqual([s.SubjectKey for s in from_xml], ["SITE01-002", "SITE01-001"])
        self.assertEqual(from_json.to_dict(), from_xml.to_dict())

    def test_accessor_binds_the_document_namespaces(self):
        """Opening another document later does not change how this one is written."""
        loader = self._xml_loader(self.TRANSACTIONAL + ".xml")
        clinical = loader.ClinicalData()
        self._xml_loader(os.path.join(DATA_DIR, "test_clinical_data_01.xml"), "odm_1_3_2")
        self.assertIn(f'xmlns="{ODM20}"', clinical.to_xml_string())
        NS.NamespaceRegistry.reset()
        self.assertEqual(_xsd_errors(self.validator, clinical.to_xml_string()), [])

    def test_index_selects_among_several(self):
        document = full_document()
        document.ClinicalData.append(ODM2.ClinicalData(StudyOID="ST.2", MetaDataVersionOID="MDV.2"))
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.load_odm_string(document.to_xml_string())
        self.assertEqual(loader.ClinicalData(1).StudyOID, "ST.2")
        self.assertEqual(loader.ClinicalData(-1).StudyOID, "ST.2")
        self.assertEqual(loader.ReferenceData().StudyOID, "ST.1")
        with self.assertRaisesRegex(IndexError, "has 2 ClinicalData"):
            loader.ClinicalData(2)

    def test_missing_data_is_an_index_error(self):
        loader = self._xml_loader(self.TRANSACTIONAL + ".xml")
        with self.assertRaisesRegex(IndexError, "has 0 ReferenceData"):
            loader.ReferenceData()

    def test_odm_1_3_2_clinical_and_reference_data(self):
        """The accessors are not ODM 2.0 only."""
        clinical = self._xml_loader(os.path.join(DATA_DIR, "test_clinical_data_01.xml"),
                                    "odm_1_3_2").ClinicalData()
        self.assertIsInstance(clinical, ODM1.ClinicalData)
        self.assertTrue(clinical.SubjectData)
        reference = self._xml_loader(os.path.join(DATA_DIR, "test_referece_data_01.xml"),
                                     "odm_1_3_2").ReferenceData()
        self.assertIsInstance(reference, ODM1.ReferenceData)

    def test_dataset_xml_single_clinical_data(self):
        """Dataset-XML's one ClinicalData is a JSON object, not a list."""
        import odmlib.dataset_1_0_1.model as DSX
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
                             is_default=True, is_reset=True)
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")
        clinical = DSX.ClinicalData(StudyOID="S.1", MetaDataVersionOID="MDV.1")
        clinical.ItemGroupData = [DSX.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="1")]
        document = DSX.ODM(FileType="Snapshot", FileOID="F.1", CreationDateTime="2026-01-01T00:00:00",
                           ODMVersion="1.3.2", DatasetXMLVersion="1.0.1", ClinicalData=clinical)
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="dataset_1_0_1"))
        loader.load_odm_string(document.to_json())
        self.assertEqual(loader.ClinicalData().StudyOID, "S.1")
        with self.assertRaises(IndexError):
            loader.ClinicalData(1)

    def test_before_a_document_is_opened(self):
        for loader in (OL.XMLODMLoader(model_package="odm_2_0"),
                       OL.JSONODMLoader(model_package="odm_2_0")):
            for method in ("ClinicalData", "ReferenceData"):
                with self.subTest(loader=type(loader).__name__, method=method):
                    with self.assertRaises(OdmlibLoaderStateError):
                        getattr(LD.ODMLoader(loader), method)()

    def test_loaders_without_clinical_data(self):
        loader = LD.ODMLoader(DLD.XMLDefineLoader(model_package="define_2_1"))
        for method in ("ClinicalData", "ReferenceData"):
            with self.subTest(method=method):
                with self.assertRaisesRegex(OdmlibTypeError, "XMLDefineLoader cannot load"):
                    getattr(loader, method)()

    def test_accessors_are_not_part_of_the_document_loader_interface(self):
        """Third-party DocumentLoader subclasses must not break (plan P4c)."""
        import odmlib.document_loader as DL
        self.assertFalse(hasattr(DL.DocumentLoader, "load_clinicaldata"))
        self.assertFalse(hasattr(DL.DocumentLoader, "load_referencedata"))
