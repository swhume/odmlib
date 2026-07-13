"""Regression tests: malformed input surfaces odmlib exceptions.

Previously malformed XML raised a raw xml.etree ParseError, malformed
JSON raised a raw json.JSONDecodeError, and an element unknown to the
model raised a bare AttributeError from getattr deep in the recursive
load.  All must surface as OdmlibParsingError.
"""
import os
import tempfile
from unittest import TestCase

import odmlib.loader as LD
import odmlib.odm_loader as OL
from odmlib.exceptions import OdmlibParsingError

UNKNOWN_ROOT_DOC = """<?xml version="1.0"?>
<NotAnOdmElement xmlns="http://www.cdisc.org/ns/odm/v1.3" Name="x"/>
"""


class TestLoaderRobustness(TestCase):
    def _write_tmp(self, content, suffix):
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        self.addCleanup(os.unlink, path)
        return path

    def test_malformed_xml_raises_odmlib_parsing_error(self):
        path = self._write_tmp("<ODM><Study></ODM>", ".xml")
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        with self.assertRaises(OdmlibParsingError):
            loader.open_odm_document(path)

    def test_malformed_json_raises_odmlib_parsing_error(self):
        path = self._write_tmp("{not json", ".json")
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2"))
        with self.assertRaises(OdmlibParsingError):
            loader.open_odm_document(path)

    def test_json_with_bom_loads(self):
        path = self._write_tmp('﻿{"FileOID": "F1"}', ".json")
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2"))
        doc = loader.open_odm_document(path)
        self.assertEqual(doc["FileOID"], "F1")

    def test_unknown_element_raises_odmlib_parsing_error(self):
        path = self._write_tmp(UNKNOWN_ROOT_DOC, ".xml")
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        root_elem = loader.open_odm_document(path)
        with self.assertRaises(OdmlibParsingError) as ctx:
            loader.create_odmlib(root_elem)
        self.assertIn("NotAnOdmElement", str(ctx.exception))
