"""Regression tests for the ODM 2.0 load fixes made for crfutils (plan §4A).

Each test loads a small inline ODM 2.0 document through ``load_odm_string`` in strict
mode -- the way crfutils loads a CRF -- and, where output is involved, checks that the
re-serialized document is still valid against the bundled XSD.

- O1: an empty ``TranslatedText`` (and the other text-only elements) loads.
- O3: empty and whitespace-only ``CheckValue``/``Code`` load, and keep their value.
- O4: ``xsi:schemaLocation`` round-trips; other ``xsi:*`` attributes are ignored.
- O6: the ODM 2.0 OID checker resolves UnitsItemOID, PartOfOrganizationOID,
  ArchiveLocationID and SourceItem/@leafID.
- O8: workflow and timing references are checked against the element types the
  specification allows.
- O7: an ``xhtml:div`` inside ``TranslatedText`` round-trips through XML and JSON.

O2 (``TimepointTarget``) is covered in ``test_xsd_lexical_types.py`` and O5
(interleaved children) in ``test_interleaved_children.py``.
"""
import json
import unittest
import warnings
import xml.etree.ElementTree as ET

import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_2_0.model as ODM2
import odmlib.odm_loader as OL
from odmlib.exceptions import (OdmlibOIDError, OdmlibSerializationError, OdmlibTypeError,
                               OdmlibValidationError, OdmlibWarning)
from odmlib.mode import permissive, ValidationMode
from odmlib.odm_parser import ODMSchemaValidator
from odmlib.oid_generator import create_oid_checker

ODM_NS = "http://www.cdisc.org/ns/odm/v2.0"
XHTML_NS = "http://www.w3.org/1999/xhtml"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(prefix="odm", uri=ODM_NS, is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="xs", uri=XSI_NS)
    NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


def _document(mdv_body="", odm_attrs="", after_study=""):
    return (
        f'<ODM xmlns="{ODM_NS}" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'FileOID="F.1" FileType="Snapshot" CreationDateTime="2026-10-16T09:00:00" '
        f'ODMVersion="2.0" {odm_attrs}>'
        f'<Study OID="ST.1" StudyName="Study" ProtocolName="P-1">'
        f'<MetaDataVersion OID="MDV.1" Name="Version 1">{mdv_body}</MetaDataVersion>'
        f'</Study>{after_study}</ODM>'
    )


def _item_def(oid="IT.1", inner=""):
    return f'<ItemDef OID="{oid}" Name="{oid}" DataType="text">{inner}</ItemDef>'


def _load(xml):
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
    loader.load_odm_string(xml)
    return loader.root()


class _ODM2TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = ODMSchemaValidator(standard="odm", version="2.0")

    def setUp(self):
        _setup_odm2_namespaces()

    def assertSchemaValid(self, odm):
        """The serialized document is well-formed and valid against the ODM 2.0 XSD."""
        tree = ET.ElementTree(ET.fromstring(odm.to_xml_string()))
        self.assertTrue(self.validator.validate_tree(tree), odm.to_xml_string())

    @staticmethod
    def mdv(odm):
        return odm.Study[0].MetaDataVersion[0]


class TestEmptyTextContent(_ODM2TestCase):
    """O1: XSD text content is an unrestricted string, so an empty element is valid."""

    def test_empty_translated_text_loads_strictly(self):
        odm = _load(_document(_item_def(inner=(
            '<Description><TranslatedText xml:lang="en" Type="text/plain"/></Description>'
            '<Question><TranslatedText xml:lang="en" Type="text/plain"></TranslatedText>'
            '</Question>'))))
        item = self.mdv(odm).ItemDef[0]
        self.assertIsNone(item.Description.TranslatedText[0]._content)
        self.assertIsNone(item.Question.TranslatedText[0]._content)
        self.assertSchemaValid(odm)

    def test_empty_translated_text_writes_an_empty_element(self):
        tt = ODM2.TranslatedText(Type="text/plain", lang="en")
        elem = ET.fromstring(tt.to_xml_string())
        self.assertIsNone(elem.text)
        self.assertEqual(len(elem), 0)

    def test_every_text_only_class_constructs_empty(self):
        for name in ("CheckValue", "Code", "City", "Country", "FamilyName", "FullName",
                     "GivenName", "HouseNumber", "LegalReason", "Meaning", "OtherText",
                     "PostalCode", "Prefix", "StateProv", "StreetName", "Suffix",
                     "UserName"):
            with self.subTest(name=name):
                self.assertIsNone(getattr(ODM2, name)()._content)

    def test_empty_admin_data_text_loads(self):
        odm = _load(_document(after_study=(
            '<AdminData><User OID="U.1"><UserName/><GivenName></GivenName>'
            '<Address><City/></Address></User></AdminData>')))
        user = odm.AdminData[0].User[0]
        self.assertIsNone(user.UserName._content)
        self.assertIsNone(user.Address[0].City._content)
        self.assertSchemaValid(odm)


class TestWhitespaceTextContent(_ODM2TestCase):
    """O3: whitespace is a real value in a text-only element, indentation elsewhere."""

    def _range_check(self, check_values):
        return _item_def(inner=f'<RangeCheck Comparator="EQ" SoftHard="Soft">{check_values}'
                               f'</RangeCheck>')

    def test_whitespace_check_value_is_kept(self):
        odm = _load(_document(self._range_check('<CheckValue> </CheckValue><CheckValue/>')))
        values = self.mdv(odm).ItemDef[0].RangeCheck[0].CheckValue
        self.assertEqual(values[0]._content, " ")
        self.assertIsNone(values[1]._content)
        out = ET.fromstring(odm.to_xml_string())
        written = out.findall(f".//{{{ODM_NS}}}CheckValue")
        self.assertEqual([v.text for v in written], [" ", None])
        self.assertSchemaValid(odm)

    def test_empty_code_loads(self):
        odm = _load(_document(
            '<MethodDef OID="MT.1" Name="M" Type="Computation"><Description>'
            '<TranslatedText xml:lang="en" Type="text/plain">Derive</TranslatedText>'
            '</Description><MethodSignature/>'
            '<FormalExpression Context="Python"><Code/></FormalExpression>'
            '</MethodDef>'))
        self.assertIsNone(self.mdv(odm).MethodDef[0].FormalExpression[0].Code._content)
        self.assertSchemaValid(odm)

    def test_indentation_before_a_child_is_not_content(self):
        odm = _load(_document(_item_def(inner=(
            '<Description>\n  <TranslatedText xml:lang="en" Type="text/html">\n    '
            '<div xmlns="http://www.w3.org/1999/xhtml"><p>Hi</p></div>\n  </TranslatedText>'
            '\n</Description>'))))
        tt = self.mdv(odm).ItemDef[0].Description.TranslatedText[0]
        self.assertIsNone(tt._content)
        self.assertIsNotNone(tt.div)


class TestXsiAttributes(_ODM2TestCase):
    """O4: xsi:* attributes are allowed on any element."""

    SCHEMA_LOCATION = "http://www.cdisc.org/ns/odm/v2.0 ODM.xsd"

    def test_schema_location_round_trips(self):
        odm = _load(_document(odm_attrs=(
            f'xmlns:xsi="{XSI_NS}" xsi:schemaLocation="{self.SCHEMA_LOCATION}"')))
        self.assertEqual(odm.schemaLocation, self.SCHEMA_LOCATION)
        out = ET.fromstring(odm.to_xml_string())
        self.assertEqual(out.get(f"{{{XSI_NS}}}schemaLocation"), self.SCHEMA_LOCATION)
        self.assertSchemaValid(odm)

    def test_other_xsi_attributes_are_ignored(self):
        odm = _load(_document(
            _item_def(inner='<Alias Context="SDTM" Name="AGE" xsi:type="x"/>'),
            odm_attrs=f'xmlns:xsi="{XSI_NS}" xsi:noNamespaceSchemaLocation="ODM.xsd"'))
        self.assertEqual(self.mdv(odm).ItemDef[0].Alias[0].Name, "AGE")
        self.assertNotIn("noNamespaceSchemaLocation", odm.__dict__)
        self.assertSchemaValid(odm)

    def test_unknown_foreign_attribute_still_raises(self):
        """Only the XSI namespace is exempt; other unmodelled attributes still fail."""
        with self.assertRaises(OdmlibTypeError):
            _load(_document(odm_attrs='xmlns:v="urn:vendor" v:extra="1"'))


class TestOidCheckerMappings(_ODM2TestCase):
    """O6: four ODM 2.0 reference attributes were never checked."""

    def test_mappings(self):
        ref_def = create_oid_checker("odm_2_0").ref_def
        self.assertEqual(ref_def["UnitsItemOID"], "ItemDef")
        self.assertEqual(ref_def["PartOfOrganizationOID"], "Organization")
        self.assertEqual(ref_def["ArchiveLocationID"], "Leaf")
        self.assertEqual(ref_def["leafID"], "Leaf")

    def test_define_xml_still_maps_to_lower_case_leaf(self):
        ref_def = create_oid_checker("define_2_1").ref_def
        self.assertEqual(ref_def["leafID"], "leaf")
        self.assertEqual(ref_def["ArchiveLocationID"], "leaf")

    def _check(self, odm):
        return [str(e).splitlines()[0] for e in
                odm.validate(collect_errors=True, oid_checker=create_oid_checker("odm_2_0"))]

    def _units_document(self, units_oid):
        return _document(
            '<ItemGroupDef OID="IG.VS" Name="VS" Repeating="No" Type="Form">'
            f'<ItemRef ItemOID="IT.WEIGHT" Mandatory="No" UnitsItemOID="{units_oid}"/>'
            '<ItemRef ItemOID="IT.UNIT" Mandatory="No"/></ItemGroupDef>'
            + _item_def("IT.WEIGHT") + _item_def("IT.UNIT"))

    def test_units_item_oid_is_checked(self):
        self.assertEqual(self._check(_load(self._units_document("IT.UNIT"))), [])
        errors = self._check(_load(self._units_document("IT.MISSING")))
        self.assertEqual(errors, ["OID IT.MISSING referenced in attribute UnitsItemOID is not found."])

    def test_units_item_oid_must_name_an_item_def(self):
        errors = self._check(_load(self._units_document("IG.VS")))
        self.assertEqual(len(errors), 1)
        self.assertIn("UnitsItemOID", errors[0])

    def test_leaf_references_are_checked(self):
        def document(leaf_id):
            return _document(
                f'<ItemGroupDef OID="IG.DM" Name="DM" Repeating="No" Type="Form" '
                f'ArchiveLocationID="{leaf_id}"><ItemRef ItemOID="IT.1" Mandatory="No">'
                f'<Origin Type="Collected"><SourceItems><SourceItem leafID="{leaf_id}">'
                '<Resource Type="Other" Name="EHR"/></SourceItem></SourceItems></Origin>'
                '</ItemRef></ItemGroupDef>'
                + _item_def()
                + '<Leaf ID="LF.ACRF" xlink:href="acrf.pdf"><Title>aCRF</Title></Leaf>')
        self.assertEqual(self._check(_load(document("LF.ACRF"))), [])
        errors = self._check(_load(document("LF.NONE")))
        self.assertEqual(sorted(e.split(" referenced in attribute ")[1] for e in errors),
                         ["ArchiveLocationID is not found.", "leafID is not found."])

    def test_part_of_organization_oid_is_checked(self):
        def document(parent):
            return _document(after_study=(
                '<AdminData><Organization OID="ORG.1" Name="Sponsor" Type="Sponsor"/>'
                f'<Organization OID="ORG.2" Name="CRO" Type="CRO" '
                f'PartOfOrganizationOID="{parent}"/></AdminData>'))
        self.assertEqual(self._check(_load(document("ORG.1"))), [])
        errors = self._check(_load(document("ORG.9")))
        self.assertEqual(errors,
                         ["OID ORG.9 referenced in attribute PartOfOrganizationOID is not found."])

    def test_dangling_reference_raises_in_fail_fast_mode(self):
        with self.assertRaises(OdmlibOIDError):
            _load(self._units_document("IT.MISSING")).verify_oids(create_oid_checker("odm_2_0"))


class TestWorkflowReferences(_ODM2TestCase):
    """O8: workflow and timing references are checked against the types the spec allows.

    Target sets from the ODM v2.0 specification as transcribed in the
    DataExchange-ODM-LinkML model. Each case changes one reference in a valid document.
    """

    VALID = (
        '<Protocol><StudyStructure><Epoch OID="EP.SCR" Name="Screening" SequenceNumber="1"/>'
        '</StudyStructure><StudyTimings><StudyTiming OID="TIM.1" Name="Timing">'
        '<RelativeTimingConstraint OID="RTC.1" Name="Gap" PredecessorOID="SE.SCR" '
        'SuccessorOID="SEG.FU" TimepointRelativeTarget="P7D"/>'
        '<DurationTimingConstraint OID="DTC.1" Name="Length" StructuralElementOID="EP.SCR" '
        'DurationTarget="P14D"/></StudyTiming></StudyTimings></Protocol>'
        '<WorkflowDef OID="WF.1" Name="Flow"><WorkflowStart StartOID="SE.SCR"/>'
        '<Transition OID="TR.1" Name="T1" SourceOID="SE.SCR" TargetOID="BR.1"/>'
        '<Branching OID="BR.1" Name="Eligible?" Type="Exclusive">'
        '<TargetTransition TargetTransitionOID="TR.2" ConditionOID="CD.ELIG"/>'
        '<DefaultTransition TargetTransitionOID="TR.3"/></Branching>'
        '<Transition OID="TR.2" Name="T2" SourceOID="BR.1" TargetOID="IG.RAND"/>'
        '<Transition OID="TR.3" Name="T3" SourceOID="BR.1" TargetOID="SEG.FU"/>'
        '<WorkflowEnd EndOID="IG.RAND"/></WorkflowDef>'
        '<StudyEventGroupDef OID="SEG.FU" Name="Follow-up">'
        '<StudyEventRef StudyEventOID="SE.SCR" Mandatory="Yes"/></StudyEventGroupDef>'
        '<StudyEventDef OID="SE.SCR" Name="Screening" Repeating="No" Type="Scheduled"/>'
        '<ItemGroupDef OID="IG.RAND" Name="Randomization" Repeating="No" Type="Form">'
        '<ItemRef ItemOID="IT.1" Mandatory="No"/></ItemGroupDef>'
        + _item_def()
        + '<ConditionDef OID="CD.ELIG" Name="Eligible"/>'
    )

    def _errors(self, old=None, new=None):
        if old is not None:
            self.assertIn(old, self.VALID)          # the case really changes the document
        body = self.VALID if old is None else self.VALID.replace(old, new)
        odm = _load(_document(body))
        return [str(e).splitlines()[0] for e in
                odm.validate(collect_errors=True, oid_checker=create_oid_checker("odm_2_0"))]

    def test_valid_workflow_has_no_errors(self):
        self.assertEqual(self._errors(), [])

    def test_start_oid_may_not_name_a_branching(self):
        errors = self._errors('StartOID="SE.SCR"', 'StartOID="BR.1"')
        self.assertEqual(len(errors), 1)
        self.assertIn("StartOID must point at one of StudyEventGroupDef, StudyEventDef, "
                      "ItemGroupDef, ItemDef; OID BR.1 is defined on a Branching", errors[0])

    def test_dangling_source_oid_is_not_found(self):
        self.assertEqual(self._errors('SourceOID="SE.SCR"', 'SourceOID="SE.NONE"'),
                         ["OID SE.NONE referenced in attribute SourceOID is not found."])

    def test_structural_element_oid_accepts_study_and_epoch(self):
        self.assertEqual(self._errors('StructuralElementOID="EP.SCR"',
                                      'StructuralElementOID="ST.1"'), [])

    def test_structural_element_oid_rejects_a_transition(self):
        errors = self._errors('StructuralElementOID="EP.SCR"', 'StructuralElementOID="TR.1"')
        self.assertEqual(len(errors), 1)
        self.assertIn("defined on a Transition", errors[0])

    def test_default_transition_must_name_a_transition(self):
        """The mistake in DataExchange-ODM's Inclusion_Exclusion_Simple_Workflow.xml."""
        errors = self._errors('<DefaultTransition TargetTransitionOID="TR.3"/>',
                              '<DefaultTransition TargetTransitionOID="SEG.FU"/>')
        self.assertEqual(errors, ["OID reference for attribute TargetTransitionOID element "
                                  "types do not match: Transition and StudyEventGroupDef"])

    def test_end_oid_may_not_name_a_branching(self):
        errors = self._errors('EndOID="IG.RAND"', 'EndOID="BR.1"')
        self.assertEqual(len(errors), 1)
        self.assertIn("EndOID must point at one of", errors[0])

    def test_dangling_reference_raises_in_fail_fast_mode(self):
        odm = _load(_document(self.VALID.replace('TargetOID="BR.1"', 'TargetOID="BR.NONE"')))
        with self.assertRaises(OdmlibOIDError):
            odm.verify_oids(create_oid_checker("odm_2_0"))


class TestXhtmlTranslatedText(_ODM2TestCase):
    """O7: the xhtml:div child of TranslatedText is kept instead of silently dropped."""

    MARKUP = ('<div xmlns="http://www.w3.org/1999/xhtml" class="note"><p>Measure '
              '<b>seated</b>,<br/>after 5 minutes.</p><p xml:lang="fr">Assis.</p></div>')

    def _translated_text(self, inner):
        return _item_def(inner=f'<Question><TranslatedText xml:lang="en" '
                               f'Type="application/xhtml+xml">{inner}</TranslatedText>'
                               '</Question>')

    def _source_div(self, xml):
        return ET.fromstring(xml).find(f".//{{{XHTML_NS}}}div")

    def test_div_round_trips_through_xml(self):
        xml = _document(self._translated_text(self.MARKUP))
        odm = _load(xml)
        out_div = ET.fromstring(odm.to_xml_string()).find(f".//{{{XHTML_NS}}}div")
        self.assertIsNotNone(out_div)
        self.assertEqual(ET.canonicalize(ET.tostring(out_div)),
                         ET.canonicalize(ET.tostring(self._source_div(xml))))
        self.assertSchemaValid(odm)

    def test_text_around_the_div_is_kept(self):
        xml = _document(self._translated_text(f"Before {self.MARKUP} after"))
        tt = self.mdv(_load(xml)).ItemDef[0].Question.TranslatedText[0]
        self.assertEqual(tt._content, "Before ")
        self.assertTrue(tt.div.endswith("</div> after"))
        written = ET.fromstring(tt.to_xml_string())
        self.assertEqual(written.text, "Before ")
        self.assertEqual(written[0].tail, " after")

    def test_div_survives_json(self):
        odm = _load(_document(self._translated_text(self.MARKUP)))
        data = json.loads(odm.to_json())
        tt = data["Study"][0]["MetaDataVersion"][0]["ItemDef"][0]["Question"]["TranslatedText"][0]
        self.assertTrue(tt["div"].startswith(f'<div xmlns="{XHTML_NS}"'))
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_2_0"))
        loader.load_odm_string(json.dumps(data))
        self.assertEqual(loader.root().to_xml_string(), odm.to_xml_string())

    def test_markup_without_a_namespace_is_placed_in_xhtml(self):
        tt = ODM2.TranslatedText(Type="text/html", div="<div><p>Hi <i>there</i></p></div>")
        self.assertEqual(tt.div, f'<div xmlns="{XHTML_NS}"><p>Hi <i>there</i></p></div>')
        out = ET.fromstring(tt.to_xml_string())
        self.assertEqual([e.tag for e in out.iter()][1:],
                         [f"{{{XHTML_NS}}}div", f"{{{XHTML_NS}}}p", f"{{{XHTML_NS}}}i"])

    def test_serialization_does_not_depend_on_the_namespace_registry(self):
        """The v0.2.1 opaque div failed when 'xhtml' was not registered."""
        tt = ODM2.TranslatedText(Type="text/html", div=self.MARKUP)
        NS.NamespaceRegistry(prefix="odm", uri=ODM_NS, is_default=True, is_reset=True)
        out = ET.fromstring(tt.to_xml_string())
        self.assertEqual(out[0].tag, f"{{{XHTML_NS}}}div")

    def test_invalid_markup_is_rejected(self):
        for markup in ("<p>not a div</p>", "<div>unclosed", "<div/><div/>", "text <div/>",
                       '<!DOCTYPE div [<!ENTITY e "x">]><div>&e;</div>', "<x:div xmlns:x='urn:x'/>"):
            with self.subTest(markup=markup):
                with self.assertRaises(OdmlibValidationError):
                    ODM2.TranslatedText(Type="text/html", div=markup)

    def test_invalid_markup_kept_in_permissive_mode_cannot_be_written(self):
        with permissive(ValidationMode.SKIP_FORMAT):
            tt = ODM2.TranslatedText(Type="text/html", div="<p>broken")
        with self.assertRaises(OdmlibSerializationError):
            tt.to_xml_string()

    def test_unsupported_children_warn(self):
        xml = _document(self._translated_text("<div xmlns='http://www.w3.org/1999/xhtml'/>"
                                              "<div xmlns='http://www.w3.org/1999/xhtml'/>"))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            _load(xml)
        messages = [str(w.message) for w in caught if issubclass(w.category, OdmlibWarning)]
        self.assertEqual(len(messages), 1)
        self.assertIn("TranslatedText: dropped 1 child element", messages[0])


if __name__ == "__main__":
    unittest.main()
