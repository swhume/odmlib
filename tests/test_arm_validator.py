"""XSD schema validation tests for ARM (Analysis Results Metadata) 1.0.

odmlib bundles two ARM 1.0 schema sets, because ARM layers onto Define-XML and
the two Define-XML versions are not interchangeable:

- ``("arm", "1.0")``            -- ARM 1.0 over Define-XML 2.0 (the CDISC original)
- ``("arm", "1.0-define2.1")``  -- ARM 1.0 over Define-XML 2.1 (odmlib-derived)

The 2.1 pairing is the one that matches ``odmlib.arm_1_0.model`` and the
``definev21-adam.xml`` fixture; the 2.0 pairing is the schema CDISC published.
Both are exercised here, including the cross-version negative case that proves
they are not interchangeable.
"""
import os
import tempfile
from unittest import TestCase

import xmlschema

import odmlib.odm_parser as P
import odmlib.arm_loader as ARM
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.schema_manager as SM
from odmlib.exceptions import OdmlibValidationError

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
ARM_NS = "http://www.cdisc.org/ns/arm/v1.0"


class TestARMDefine21Validator(TestCase):
    """ARM 1.0 over Define-XML 2.1 -- the pairing odmlib's model targets."""

    def setUp(self) -> None:
        self.validator = P.ODMSchemaValidator(standard="arm", version="1.0-define2.1")
        self.adam_file = os.path.join(DATA_DIR, "definev21-adam.xml")
        self.invalid_file = os.path.join(DATA_DIR, "definev21-adam-invalid.xml")

    def test_constructor_resolves_arm_schema(self):
        self.assertIsNotNone(self.validator.xsd)
        # The root schema targets the ODM namespace -- ARM is an extension
        # embedded in a Define-XML document, not a standalone document type.
        self.assertEqual(self.validator.xsd.target_namespace,
                         "http://www.cdisc.org/ns/odm/v1.3")

    def test_arm_namespace_is_resolved(self):
        # Guards against the schema compiling with an unresolved arm: import,
        # which would silently skip every ARM element during validation.
        self.assertIn(ARM_NS, self.validator.xsd.maps.namespaces)

    def test_validate_file_adam(self):
        # validate_file returns None and raises on failure
        self.assertIsNone(self.validator.validate_file(self.adam_file))

    def test_validate_tree_adam(self):
        parser = P.ODMParser(self.adam_file)
        tree = parser.parse_tree()
        self.assertTrue(self.validator.validate_tree(tree))

    def test_validate_file_invalid_arm(self):
        """The invalid fixture drops a required arm:AnalysisResult attribute."""
        try:
            self.validator.validate_file(self.invalid_file)
        except xmlschema.validators.exceptions.XMLSchemaValidatorError as ex:
            self.assertIn("missing required attribute", ex.reason)
            self.assertIn("AnalysisReason", ex.reason)
        else:
            self.fail("Expected the ARM XSD to reject definev21-adam-invalid.xml")

    def test_plain_define21_still_validates(self):
        """The ARM root schema is a superset of define2-1-0.xsd.

        An ARM-free Define-XML 2.1 document must still validate, otherwise the
        ARM schema would be unusable as a general Define-XML 2.1 validator.
        """
        define_file = os.path.join(DATA_DIR, "defineV21-SDTM.xml")
        self.assertIsNone(self.validator.validate_file(define_file))

    def test_arm_roundtrip_output_is_schema_valid(self):
        """odmlib's own ARM serialization round-trips to a schema-valid document.

        This is the end-to-end guarantee: load the ARM fixture through the ARM
        model, write it back out, and re-validate against the bundled XSD.
        """
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
                             is_default=True, is_reset=True)
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
        NS.NamespaceRegistry(prefix="arm", uri=ARM_NS)
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

        loader = LD.ODMLoader(ARM.XMLArmLoader())
        loader.open_odm_document(self.adam_file)
        odm = loader.load_odm()

        # Sanity-check that ARM content actually survived the load, so a silent
        # drop cannot make this test pass vacuously.
        mdv = odm.Study.MetaDataVersion
        self.assertGreater(len(mdv.AnalysisResultDisplays), 0)

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "arm_roundtrip.xml")
            odm.write_xml(out)
            self.assertIsNone(self.validator.validate_file(out))


class TestARMDefine20Validator(TestCase):
    """ARM 1.0 over Define-XML 2.0 -- the schema set CDISC published."""

    def setUp(self) -> None:
        self.validator = P.ODMSchemaValidator(standard="arm", version="1.0")

    def test_constructor_resolves_arm_schema(self):
        self.assertIsNotNone(self.validator.xsd)
        self.assertEqual(self.validator.xsd.target_namespace,
                         "http://www.cdisc.org/ns/odm/v1.3")

    def test_arm_namespace_is_resolved(self):
        self.assertIn(ARM_NS, self.validator.xsd.maps.namespaces)

    def test_plain_define20_validates(self):
        """An ARM-free Define-XML 2.0 document validates (ARM elements are optional)."""
        define_file = os.path.join(DATA_DIR, "define2-0-0-sdtm-test.xml")
        self.assertIsNone(self.validator.validate_file(define_file))


class TestARMSchemaVersionsAreNotInterchangeable(TestCase):
    """The two ARM pairings must not silently accept each other's documents."""

    def test_define21_document_fails_against_arm10(self):
        """A def/v2.1 document must NOT pass the Define-XML 2.0 ARM schema.

        This is the reason two schema sets are bundled rather than one: the
        def: namespace URI differs between Define-XML 2.0 and 2.1, so the
        wrong pairing rejects the document on the first def:-prefixed
        attribute it meets.
        """
        validator = P.ODMSchemaValidator(standard="arm", version="1.0")
        adam_file = os.path.join(DATA_DIR, "definev21-adam.xml")
        try:
            validator.validate_file(adam_file)
        except xmlschema.validators.exceptions.XMLSchemaValidatorError as ex:
            self.assertIn("def/v2.1", str(ex.reason))
        else:
            self.fail("Expected a Define-XML 2.1 document to fail the arm/1.0 schema")

    def test_define20_document_fails_against_arm10_define21(self):
        validator = P.ODMSchemaValidator(standard="arm", version="1.0-define2.1")
        define_file = os.path.join(DATA_DIR, "define2-0-0-sdtm-test.xml")
        parser = P.ODMParser(define_file)
        tree = parser.parse_tree()
        self.assertFalse(validator.validate_tree(tree))


class TestARMSchemaRegistration(TestCase):
    """Both ARM pairings are registered in schema_manager._MAIN_SCHEMA."""

    def test_arm_10_path_resolves_to_existing_file(self):
        path = SM.get_schema_path("arm", "1.0")
        self.assertTrue(path.endswith("arm1-0-0.xsd"), f"got: {path}")
        self.assertTrue(os.path.isfile(path), f"ARM 1.0 schema missing at {path}")

    def test_arm_10_define21_path_resolves_to_existing_file(self):
        path = SM.get_schema_path("arm", "1.0-define2.1")
        self.assertTrue(path.endswith("arm1-0-0.xsd"), f"got: {path}")
        self.assertTrue(os.path.isfile(path), f"ARM 2.1 schema missing at {path}")

    def test_the_two_pairings_resolve_to_different_files(self):
        # Same filename, different directory -- a copy/paste error in
        # _MAIN_SCHEMA that pointed both keys at one directory would
        # otherwise go unnoticed.
        self.assertNotEqual(SM.get_schema_path("arm", "1.0"),
                            SM.get_schema_path("arm", "1.0-define2.1"))

    def test_unknown_arm_version_raises(self):
        with self.assertRaises(OdmlibValidationError):
            SM.get_schema_path("arm", "9.9")

    def test_supporting_schema_files_are_present(self):
        """The root schema is useless without its two included/imported files."""
        for version in ("1.0", "1.0-define2.1"):
            schema_dir = SM.get_schema_dir("arm", version)
            for filename in ("arm-ns.xsd", "arm-extension.xsd", "arm1-0-0.xsd"):
                self.assertTrue(
                    os.path.isfile(os.path.join(schema_dir, filename)),
                    f"missing {filename} in arm/{version}",
                )
