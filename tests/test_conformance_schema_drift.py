"""Regression tests: cerberus schemas must match the model classes.

Covers two drift directions found in review:
- ``Presentation`` existed in the MetaDataVersion model but not in the
  cerberus schema, so spec-valid documents were rejected as "unknown field".
- ``Repeating`` is required by the model (and the ODM 1.3.2 spec) on
  StudyEventDef/FormDef/ItemGroupDef but the schemas accepted its absence.
"""
from unittest import TestCase

import odmlib.odm_1_3_2.rules.metadata_schema as ODM_SCHEMA
from odmlib.exceptions import OdmlibConformanceError


class TestConformanceSchemaDrift(TestCase):
    def setUp(self):
        self.checker = ODM_SCHEMA.MetadataSchema()

    def test_mdv_with_presentation_passes(self):
        mdv = {
            "OID": "MDV.001",
            "Name": "Test MDV",
            "Presentation": [{"OID": "PR.001", "lang": "en", "_content": "layout"}],
        }
        self.assertTrue(self.checker.check_conformance(mdv, "MetaDataVersion"))

    def test_item_group_def_missing_repeating_rejected(self):
        igd = {"OID": "IG.DM", "Name": "Demographics"}
        with self.assertRaises(OdmlibConformanceError):
            self.checker.check_conformance(igd, "ItemGroupDef")

    def test_form_def_missing_repeating_rejected(self):
        fd = {"OID": "F.DM", "Name": "Demographics"}
        with self.assertRaises(OdmlibConformanceError):
            self.checker.check_conformance(fd, "FormDef")

    def test_study_event_def_with_repeating_passes(self):
        sed = {"OID": "SE.V1", "Name": "Visit 1", "Repeating": "No"}
        self.assertTrue(self.checker.check_conformance(sed, "StudyEventDef"))
