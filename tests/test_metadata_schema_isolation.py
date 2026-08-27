"""Regression tests: MetadataSchema instances must not share cerberus schemas.

Previously all MetadataSchema classes registered their schemas into the
process-global ``cerberus.schema_registry`` under the same names ("ODM",
"Study", "ItemDef", ...), so the last checker instantiated silently
overwrote the schemas used by every other checker in the process.
"""
from unittest import TestCase

import odmlib.odm_1_3_2.rules.metadata_schema as ODM_SCHEMA
import odmlib.define_2_0.rules.metadata_schema as DEFINE_20_SCHEMA
import odmlib.define_2_1.rules.metadata_schema as DEFINE_21_SCHEMA
from odmlib.exceptions import OdmlibConformanceError

# valid against the ODM 1.3.2 "ODM" schema, invalid against the Define-XML
# ones (no Context/ODMVersion/Study; FileType="Transactional" is not allowed)
ODM_132_DOC = {
    "FileOID": "ODM.TEST.001",
    "FileType": "Transactional",
    "CreationDateTime": "2026-07-08T00:00:00",
}


class TestMetadataSchemaIsolation(TestCase):
    def test_odm_checker_unaffected_by_define_checker(self):
        odm_checker = ODM_SCHEMA.MetadataSchema()
        DEFINE_21_SCHEMA.MetadataSchema()
        DEFINE_20_SCHEMA.MetadataSchema()
        self.assertTrue(odm_checker.check_conformance(ODM_132_DOC, "ODM"))

    def test_define_checker_unaffected_by_odm_checker(self):
        define_checker = DEFINE_21_SCHEMA.MetadataSchema()
        ODM_SCHEMA.MetadataSchema()
        with self.assertRaises(OdmlibConformanceError):
            define_checker.check_conformance(ODM_132_DOC, "ODM")

    def test_registries_are_independent(self):
        odm_checker = ODM_SCHEMA.MetadataSchema()
        define_checker = DEFINE_21_SCHEMA.MetadataSchema()
        self.assertNotIn("Context", odm_checker._registry.get("ODM"))
        self.assertIn("Context", define_checker._registry.get("ODM"))
