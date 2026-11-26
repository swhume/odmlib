from unittest import TestCase
import os
import odmlib.odm_parser as P
from odmlib.exceptions import OdmlibTypeError


class TestODMValidator(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        # Use packaged ODM 1.3.2 schema bundled with odmlib
        self.validator = P.ODMSchemaValidator(standard="odm", version="1.3.2")

    def test_validate_tree_valid(self):
        self.parser = P.ODMParser(self.odm_file)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertTrue(is_valid)

    def test_validate_file(self):
        # validate file raises an exception if validation fails
        self.assertIsNone(self.validator.validate_file(self.odm_file))

    def test_validate_file_invalid(self):
        odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test-invalid.xml')
        # with self.assertRaises(XSD.validators.exceptions.XMLSchemaChildrenValidationError):
        with self.assertRaises(P.OdmlibSchemaValidationError):
            self.validator.validate_file(odm_file)

    def test_validate_file_invalid_msg(self):
        odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test-invalid.xml')
        try:
            self.validator.validate_file(odm_file)
        except P.OdmlibSchemaValidationError as ex:
            # print(ex)
            self.assertIn("failed validating", ex.args[0].msg)

    def test_validate_tree_invalid(self):
        odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test-invalid.xml')
        self.parser = P.ODMParser(odm_file)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertFalse(is_valid)

    def test_validate_string_tree_valid(self):
        with open(self.odm_file, "r", encoding="utf-8") as f:
            self.odm_string = f.read()
        self.parser = P.ODMStringParser(self.odm_string)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertTrue(is_valid)


class TestODMv20Validator(TestCase):
    """End-to-end ODM v2.0 schema validation against the bundled XSD.

    Validates that ODM v2.0 documents can be checked through the same
    public API as v1.3.2: ODMSchemaValidator(standard="odm", version="2.0").
    Both fixtures were confirmed to validate cleanly against the bundled
    odmlib/schemas/odm/2.0/ODM.xsd at the time this suite was introduced;
    if either later fails, treat it as a regression in either the fixture
    or the bundled XSD, not in the validator itself.
    """

    def setUp(self):
        self.validator = P.ODMSchemaValidator(standard="odm", version="2.0")
        data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
        self.example_file = os.path.join(data_dir, "odmv2_example.xml")
        self.cdash_file = os.path.join(data_dir, "cdash_demo_v20.xml")

    def test_constructor_resolves_v20_schema(self):
        self.assertIsNotNone(self.validator.xsd)
        self.assertEqual(self.validator.xsd.target_namespace,
                         "http://www.cdisc.org/ns/odm/v2.0")

    def test_validate_file_odmv2_example(self):
        self.assertIsNone(self.validator.validate_file(self.example_file))

    def test_validate_file_cdash_demo(self):
        self.assertIsNone(self.validator.validate_file(self.cdash_file))

    def test_validate_tree_odmv2_example(self):
        parser = P.ODMParser(self.example_file)
        tree = parser.parse_tree()
        self.assertTrue(self.validator.validate_tree(tree))

    def test_validate_tree_v13_document_against_v20_schema_fails(self):
        # An ODM 1.3.2 document must NOT silently pass v2.0 validation —
        # this is the reason the explicit-schema constructor contract exists.
        odm_v13 = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data", "cdash-odm-test.xml",
        )
        parser = P.ODMParser(odm_v13)
        tree = parser.parse_tree()
        self.assertFalse(self.validator.validate_tree(tree))

    def test_itemdef_displayformat_variableset_xsd_valid(self):
        """ItemDef DisplayFormat/VariableSet serialize to schema-valid ODM 2.0.

        v0.2.1 aligned the ODM 2.0 ItemDef attribute set with the XSD
        (added DisplayFormat/VariableSet). This proves the alignment
        end-to-end: take the known-valid odmv2_example.xml fixture, set
        the two new attributes on an ItemDef, re-serialize, and re-validate
        against the bundled ODM 2.0 XSD.
        """
        import tempfile
        from odmlib import odm_loader as OL, loader as LO
        import odmlib.ns_registry as NS

        nsr = NS.NamespaceRegistry(
            prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0",
            is_default=True, is_reset=True,
        )
        NS.NamespaceRegistry(prefix="xs",    uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml",   uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

        loader = LO.ODMLoader(OL.XMLODMLoader(
            model_package="odm_2_0",
            ns_uri="http://www.cdisc.org/ns/odm/v2.0",
            local_model=False,
            nsr=nsr,
        ))
        loader.open_odm_document(self.example_file)
        odm = loader.root()
        mdv = loader.MetaDataVersion()
        self.assertGreaterEqual(len(mdv.ItemDef), 1)

        mdv.ItemDef[0].DisplayFormat = "9.2"
        mdv.ItemDef[0].VariableSet = "VS1"

        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "odmv2_displayformat.xml")
            odm.write_xml(out)
            self.assertIsNone(self.validator.validate_file(out))


class TestODMValidatorConstructorContract(TestCase):
    """Lock in the contract: silent fallback to ODM 1.3.2 is no longer allowed.

    Pre-fix, ``ODMSchemaValidator()`` with no arguments silently selected
    the ODM 1.3.2 schema, which could quietly validate (e.g.) a Define-XML
    2.1 document against the wrong schema. The constructor now requires an
    explicit choice: either ``xsd_file`` or both ``standard`` and ``version``.
    """

    def test_no_args_raises(self):
        """No xsd_file, no standard, no version -> OdmlibTypeError, not silent ODM 1.3.2."""
        with self.assertRaises(OdmlibTypeError) as cm:
            P.ODMSchemaValidator()
        self.assertIn("xsd_file", str(cm.exception))
        self.assertIn("standard", str(cm.exception))
        self.assertIn("version", str(cm.exception))

    def test_no_args_hint_mentions_custom_schema_path(self):
        """The hint must point custom-schema users at xsd_file=, not just standard/version.

        Users with local models whose XSD isn't bundled with odmlib (i.e. not
        in ``schema_manager._MAIN_SCHEMA``) need the ``xsd_file=`` escape
        hatch. The error message has to say so explicitly, otherwise a user
        may follow the hint, pass ``standard='odm'``, and silently validate
        against the wrong schema again.
        """
        with self.assertRaises(OdmlibTypeError) as cm:
            P.ODMSchemaValidator()
        msg = str(cm.exception)
        self.assertIn("xsd_file=", msg)
        self.assertIn("custom", msg.lower())

    def test_only_standard_raises(self):
        """Partial info (standard without version) is also rejected."""
        with self.assertRaises(OdmlibTypeError):
            P.ODMSchemaValidator(standard="odm")

    def test_only_version_raises(self):
        """Partial info (version without standard) is also rejected."""
        with self.assertRaises(OdmlibTypeError):
            P.ODMSchemaValidator(version="1.3.2")

    def test_explicit_standard_and_version_works(self):
        """Both standard and version is the supported lookup path."""
        validator = P.ODMSchemaValidator(standard="odm", version="1.3.2")
        self.assertIsNotNone(validator.xsd)

    def test_explicit_odm_v20_works(self):
        """ODM v2.0 is now a registered (standard, version) combination."""
        validator = P.ODMSchemaValidator(standard="odm", version="2.0")
        self.assertIsNotNone(validator.xsd)
        self.assertEqual(validator.xsd.target_namespace,
                         "http://www.cdisc.org/ns/odm/v2.0")

    def test_explicit_xsd_file_works(self):
        """An explicit xsd_file path works without standard/version."""
        import odmlib.schema_manager as SM
        xsd_path = SM.get_schema_path("odm", "1.3.2")
        validator = P.ODMSchemaValidator(xsd_file=xsd_path)
        self.assertIsNotNone(validator.xsd)

    def test_xsd_file_takes_precedence(self):
        """When xsd_file is provided, standard/version aren't required."""
        import odmlib.schema_manager as SM
        xsd_path = SM.get_schema_path("odm", "1.3.2")
        # No error despite standard=None, version=None — xsd_file wins.
        validator = P.ODMSchemaValidator(xsd_file=xsd_path)
        self.assertIsNotNone(validator.xsd)

    def test_custom_out_of_tree_xsd_works(self):
        """Custom/local schemas not bundled with odmlib must work via xsd_file=.

        Simulates the case where a user with a local model has an XSD that is
        *not* registered in :data:`odmlib.schema_manager._MAIN_SCHEMA`. We
        copy a bundled XSD to a temp location to exercise the same code path
        a custom schema would take, without depending on any user-supplied
        file. The point is that ``xsd_file=`` accepts an arbitrary path and
        doesn't consult the packaged schema registry.
        """
        import shutil
        import tempfile
        import odmlib.schema_manager as SM

        bundled_xsd_dir = os.path.dirname(SM.get_schema_path("odm", "1.3.2"))
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_xsd = os.path.join(tmpdir, "my_custom_schema.xsd")
            # Copy the entire schema tree so xs:include/xs:import resolve.
            for entry in os.listdir(bundled_xsd_dir):
                src = os.path.join(bundled_xsd_dir, entry)
                if os.path.isfile(src):
                    shutil.copy(src, tmpdir)
            shutil.move(
                os.path.join(tmpdir, os.path.basename(SM.get_schema_path("odm", "1.3.2"))),
                dest_xsd,
            )
            validator = P.ODMSchemaValidator(xsd_file=dest_xsd)
            self.assertIsNotNone(validator.xsd)
