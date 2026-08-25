"""Regression guards for the ODM 2.0 structural model/XSD alignment.

Each test asserts the XSD-aligned shape of an odm_2_0 model class. Every
one of these started life as an ``xfail(strict=True)`` pinning a gap the
v0.2.1 ODM 2.0 alignment work closed; the markers came off as each gap was
fixed, and the assertions stay behind so the alignment cannot regress.

See ``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`` §3.1-§3.5 and §6 for the gaps,
and §3.7 for the ItemDef attribute set (closed earlier in v0.2.1).
"""
from unittest import TestCase

import odmlib.odm_2_0.model as ODM2
import odmlib.ns_registry as NS


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True, is_reset=True,
    )


class TestODM2StructuralAlignment(TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_conditiondef_has_methodsignature(self):
        # Closed in v0.2.1, alignment plan §3.1: the XSD requires a MethodSignature
        # child on ConditionDef.
        self.assertIn("MethodSignature", ODM2.ConditionDef._elems)

    def test_formalexpression_is_element_based(self):
        # Closed in v0.2.1, alignment plan §3.2: the XSD models the expression as a
        # choice of Code | ExternalCodeLib, not as element text.
        self.assertNotIn("_content", ODM2.FormalExpression._fields)
        self.assertTrue(hasattr(ODM2, "Code"))
        self.assertTrue(hasattr(ODM2, "ExternalCodeLib"))

    def test_protocol_matches_xsd(self):
        # Closed in v0.2.1, alignment plan §3.3: Protocol reaches study events through
        # StudyEventGroupRef; the XSD has no Protocol/StudyEventRef.
        self.assertNotIn("StudyEventRef", ODM2.Protocol._elems)
        self.assertIn("StudyEventGroupRef", ODM2.Protocol._elems)

    def test_mdv_has_no_studytiming(self):
        # Closed in v0.2.1, alignment plan §3.4: timing lives under
        # Protocol/StudyTimings, not on MetaDataVersion.
        self.assertNotIn("StudyTiming", ODM2.MetaDataVersion._elems)

    def test_studyeventgroupdef_has_required_group(self):
        # Closed in v0.2.1, alignment plan §3.5: the XSD's required
        # (StudyEventGroupRef?, StudyEventRef?) group had no model equivalent.
        elems = ODM2.StudyEventGroupDef._elems
        self.assertTrue(
            "StudyEventGroupRef" in elems or "StudyEventRef" in elems)

    def test_itemdef_attribute_set_matches_xsd(self):
        # Closed in v0.2.1, alignment plan §3.7: the ItemDef attribute set was aligned
        # with the ODM 2.0 XSD. See CHANGELOG and UPDATE_ODM20_ITEMDEF.md.
        fields = set(ODM2.ItemDef._fields)
        self.assertNotIn("FractionDigits", fields)
        self.assertNotIn("DatasetVarName", fields)
        self.assertNotIn("SDSVarName", fields)
        self.assertIn("DisplayFormat", fields)
        self.assertIn("VariableSet", fields)
