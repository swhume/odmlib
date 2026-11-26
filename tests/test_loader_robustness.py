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


ODM13 = "http://www.cdisc.org/ns/odm/v1.3"
DEF21 = "http://www.cdisc.org/ns/def/v2.1"
ARM10 = "http://www.cdisc.org/ns/arm/v1.0"


def _registry(**prefixes):
    """Reset the registry to exactly *prefixes* (prefix=uri), with odm as default."""
    import odmlib.ns_registry as NS
    NS.NamespaceRegistry(prefix="odm", uri=ODM13, is_default=True, is_reset=True)
    for prefix, uri in prefixes.items():
        NS.NamespaceRegistry(prefix=prefix, uri=uri)


class TestUnknownChildPrefix(TestCase):
    """P2.5 defect 2: an unknown child prefix is an OdmlibParsingError, not a SyntaxError.

    ElementTree raises a bare ``SyntaxError`` ("prefix 'def' not found in prefix
    map") when ``find`` is given a prefix the map lacks.
    """

    def _assert_names_prefix(self, ctx, prefix):
        self.assertIn(f"'{prefix}'", str(ctx.exception))
        self.assertIn("NamespaceRegistry", ctx.exception.hint)

    def test_odm_loader(self):
        import xml.etree.ElementTree as ET
        # construct first: importing a model registers its prefixes; then drop 'def'
        loader = OL.XMLODMLoader(model_package="define_2_1")   # load_document without opening
        _registry()
        element = ET.fromstring(f'<ItemDef xmlns="{ODM13}" OID="IT.1" Name="X" DataType="text"/>')
        with self.assertRaises(OdmlibParsingError) as ctx:
            loader.load_document(element)
        self._assert_names_prefix(ctx, "def")

    def test_define_loader(self):
        import xml.etree.ElementTree as ET
        import odmlib.define_loader as DL
        loader = DL.XMLDefineLoader(model_package="define_2_1")
        _registry()
        element = ET.fromstring(f'<ItemDef xmlns="{ODM13}" OID="IT.1" Name="X" DataType="text"/>')
        with self.assertRaises(OdmlibParsingError) as ctx:
            loader.load_document(element)
        self._assert_names_prefix(ctx, "def")

    def test_arm_loader(self):
        import xml.etree.ElementTree as ET
        import odmlib.arm_loader as AL
        loader = AL.XMLArmLoader()
        _registry(arm=ARM10)                          # 'def' missing
        element = ET.fromstring(f'<ProgrammingCode xmlns="{ARM10}" Context="SAS"/>')
        with self.assertRaises(OdmlibParsingError) as ctx:
            loader.load_document(element)
        self._assert_names_prefix(ctx, "def")


class TestNamespacedAttributes(TestCase):
    """P2.5 defect 5: a namespaced attribute sets a field only in the field's own namespace."""

    def test_foreign_attribute_does_not_overwrite_the_elements_own(self):
        import xml.etree.ElementTree as ET
        import odmlib.arm_loader as AL
        from odmlib.exceptions import OdmlibWarning
        _registry(**{"def": DEF21, "arm": ARM10})
        element = ET.fromstring(
            f'<ProgrammingCode xmlns="{ARM10}" xmlns:v="urn:vendor" '
            f'Context="SAS 9.4" v:Context="vendor"/>')
        with self.assertWarns(OdmlibWarning) as ctx:
            code = AL.XMLArmLoader().load_document(element)
        self.assertEqual(code.Context, "SAS 9.4")
        self.assertIn("{urn:vendor}Context", str(ctx.warning))

    def test_xml_lang_in_the_xml_namespace_is_accepted(self):
        import odmlib.odm_1_3_2.model as ODM
        tt = ODM.TranslatedText(**{"{http://www.w3.org/XML/1998/namespace}lang": "fr",
                                   "_content": "Oui"})
        self.assertEqual(tt.lang, "fr")

    def test_lang_in_a_foreign_namespace_is_ignored(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.exceptions import OdmlibWarning
        with self.assertWarns(OdmlibWarning):
            tt = ODM.TranslatedText(**{"{urn:vendor}lang": "fr", "_content": "Oui"})
        self.assertNotIn("lang", tt.__dict__)

    def test_xsi_attribute_named_like_an_unqualified_one_is_dropped_silently(self):
        import warnings
        import odmlib.arm_1_0.model as ARM
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            code = ARM.ProgrammingCode(**{"{http://www.w3.org/2001/XMLSchema-instance}Context": "x",
                                          "Context": "SAS"})
        self.assertEqual(code.Context, "SAS")

    def test_def_attributes_survive_an_interleaved_define_2_0_open(self):
        """The model's own def binding counts, not whatever the registry holds now."""
        import odmlib.define_2_1.model as DEF
        _registry(**{"def": "http://www.cdisc.org/ns/def/v2.0"})   # another file rebound def
        igd = DEF.ItemGroupDef(**{
            "OID": "IG.DM", "Name": "DM", "Repeating": "No", "SASDatasetName": "DM",
            "Purpose": "Tabulation", f"{{{DEF21}}}Structure": "One record per subject",
            f"{{{DEF21}}}ArchiveLocationID": "LF.DM"})
        self.assertEqual(igd.Structure, "One record per subject")
        self.assertEqual(igd.ArchiveLocationID, "LF.DM")


class TestWhitespaceOnlyText(TestCase):
    """P2.5 defect 6: Define and ARM loaders keep whitespace-only text, as XMLODMLoader does."""

    def test_define_loader_keeps_a_blank_check_value(self):
        import xml.etree.ElementTree as ET
        import odmlib.define_loader as DL
        _registry(**{"def": DEF21})
        loader = DL.XMLDefineLoader(model_package="define_2_1")
        check = loader.load_document(ET.fromstring(f'<CheckValue xmlns="{ODM13}"> </CheckValue>'))
        self.assertEqual(check._content, " ")

    def test_arm_loader_keeps_a_blank_check_value(self):
        import xml.etree.ElementTree as ET
        import odmlib.arm_loader as AL
        _registry(**{"def": DEF21, "arm": ARM10})
        check = AL.XMLArmLoader().load_document(ET.fromstring(f'<CheckValue xmlns="{ODM13}"> </CheckValue>'))
        self.assertEqual(check._content, " ")

    def test_indentation_before_a_child_is_still_not_content(self):
        import xml.etree.ElementTree as ET
        import odmlib.define_loader as DL
        _registry(**{"def": DEF21})
        description = DL.XMLDefineLoader(model_package="define_2_1").load_document(ET.fromstring(
            f'<Description xmlns="{ODM13}">\n  <TranslatedText>x</TranslatedText>\n</Description>'))
        self.assertNotIn("_content", description.__dict__)


class TestToDictOmitsEmptyLists(TestCase):
    """P2.5 defect 7: reading an unset list must not make it appear in to_dict()."""

    def test_unset_list_read_is_not_serialized(self):
        import odmlib.odm_1_3_2.model as ODM
        igd = ODM.ItemGroupDef(OID="IG.1", Name="IG", Repeating="No")
        self.assertEqual(len(igd.ItemRef), 0)          # creates the empty list
        self.assertNotIn("ItemRef", igd.to_dict())
        self.assertNotIn("ItemRef", igd.to_json())

    def test_populated_list_is_still_serialized(self):
        import odmlib.odm_1_3_2.model as ODM
        igd = ODM.ItemGroupDef(OID="IG.1", Name="IG", Repeating="No")
        igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.1", Mandatory="No"))
        self.assertEqual(igd.to_dict()["ItemRef"], [{"ItemOID": "IT.1", "Mandatory": "No"}])
