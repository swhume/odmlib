"""Security regression tests: DOCTYPE declarations must be rejected.

ODM documents never require a DTD, and internal entity definitions enable
entity-expansion denial-of-service attacks (billion laughs) that the
stdlib ElementTree parser does not defend against.
"""
import os
import tempfile
from unittest import TestCase

import odmlib.odm_parser as P
from odmlib.exceptions import OdmlibParsingError

BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
 <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
 <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
 <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
]>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" FileOID="F1"
     FileType="Snapshot" CreationDateTime="2026-07-08T00:00:00">&lol5;</ODM>
"""

VALID_ODM = """<?xml version="1.0"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v1.3" FileOID="F1"
     FileType="Snapshot" CreationDateTime="2026-07-08T00:00:00"/>
"""

MALFORMED = "<ODM><Study></ODM>"


class TestDoctypeRejection(TestCase):
    def test_string_parser_rejects_doctype(self):
        with self.assertRaises(OdmlibParsingError):
            P.ODMStringParser(BILLION_LAUGHS).parse()

    def test_file_parser_rejects_doctype(self):
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".xml", delete=False) as f:
            f.write(BILLION_LAUGHS)
            path = f.name
        try:
            with self.assertRaises(OdmlibParsingError):
                P.ODMParser(path).parse()
        finally:
            os.unlink(path)

    def test_valid_document_still_parses(self):
        root = P.ODMStringParser(VALID_ODM).parse()
        self.assertEqual(root.attrib["FileOID"], "F1")

    def test_malformed_xml_raises_odmlib_error(self):
        with self.assertRaises(OdmlibParsingError):
            P.ODMStringParser(MALFORMED).parse()
