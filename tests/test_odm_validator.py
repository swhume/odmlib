from unittest import TestCase
import os
import odmlib.odm_parser as P
import xmlschema as XSD


class TestODMValidator(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
        # set the file and path to point to the odm 1.3.2 schema on your system
        odm_schema_file = os.path.join(os.sep, 'home', 'sam', 'standards', 'odm1-3-2', 'ODM1-3-2.xsd')
        self.validator = P.ODMSchemaValidator(odm_schema_file)

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
        with self.assertRaises(XSD.validators.exceptions.XMLSchemaChildrenValidationError):
            self.validator.validate_file(odm_file)

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
