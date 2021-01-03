from unittest import TestCase
import os
import odmlib.odm_parser as P
import xmlschema as XSD


class TestODMValidator(TestCase):
    def setUp(self) -> None:
        self.odm_file = os.path.dirname(os.path.realpath(__file__)) + '\\data\\cdash-odm-test.xml'
        self.validator = P.ODMSchemaValidator("C:\\Users\\shume\\Dropbox\\04. XML Tech\\ODM\\odm1_3_2\\ODM1-3-2.xsd")

    def test_validate_tree_valid(self):
        self.parser = P.ODMParser(self.odm_file)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertTrue(is_valid)

    def test_validate_file(self):
        # validate file raises an exception if validation fails
        self.assertIsNone(self.validator.validate_file(self.odm_file))

    def test_validate_file_invalid(self):
        odm_file = os.path.dirname(os.path.realpath(__file__)) + '\\data\\cdash-odm-test-invalid.xml'
        with self.assertRaises(XSD.validators.exceptions.XMLSchemaChildrenValidationError):
            self.validator.validate_file(odm_file)

    def test_validate_tree_invalid(self):
        odm_file = os.path.dirname(os.path.realpath(__file__)) + '\\data\\cdash-odm-test-invalid.xml'
        self.parser = P.ODMParser(odm_file)
        tree = self.parser.parse_tree()
        is_valid = self.validator.validate_tree(tree)
        self.assertFalse(is_valid)
