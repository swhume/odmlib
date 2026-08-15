"""Tests for the XML string serialization path (to_xml_string).

Two things are covered here, both added in 0.2.2:

* ``to_xml_string(xml_declaration=...)`` and its exact byte relationship to
  ``write_xml()``.
* Recursive namespace-snapshot binding, so a nested element reached by walking the
  tree serializes with the namespaces its document was loaded under.

Note the autouse fixture in conftest.py resets the NamespaceRegistry to ODM-1.3.2-only
before every test, so Define-XML tests re-register def/xs/xml/xlink in setUp.
"""
import os
import tempfile
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.define_2_1.model as DEFINE
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_loader as OL
from odmlib.dataset_json_1_1.model import DatasetJSON

XML_DECL = "<?xml version='1.0' encoding='UTF-8'?>\n"
ODM_NS = "http://www.cdisc.org/ns/odm/v1.3"
DEFINE_NS = "http://www.cdisc.org/ns/def/v2.1"
DEFINE_20_NS = "http://www.cdisc.org/ns/def/v2.0"
DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


def _build_odm():
    """A small but complete ODM 1.3.2 document built from the model."""
    odm = ODM.ODM(FileOID="ODM.STR.1", Granularity="Metadata", FileType="Snapshot",
                  CreationDateTime="2026-08-15T00:00:00", ODMVersion="1.3.2",
                  Originator="odmlib tests", SourceSystem="odmlib")
    study = ODM.Study(OID="ST.1")
    study.GlobalVariables = ODM.GlobalVariables()
    study.GlobalVariables.StudyName = ODM.StudyName(_content="String Serialization")
    study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Test study")
    study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="PROTO-STR")
    mdv = ODM.MetaDataVersion(OID="MDV.1", Name="MDV")
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.AGE", Name="Age", DataType="integer"))
    study.MetaDataVersion.append(mdv)
    odm.Study.append(study)
    return odm


class TestXmlDeclarationOption(TestCase):
    """to_xml_string(xml_declaration=...) and its relationship to write_xml()."""

    def setUp(self):
        self.odm = _build_odm()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.xml_file = os.path.join(self.tmp.name, "out.xml")

    def test_default_omits_declaration(self):
        self.assertFalse(self.odm.to_xml_string().startswith("<?xml"))

    def test_declaration_has_exact_expected_form(self):
        self.assertTrue(self.odm.to_xml_string(xml_declaration=True).startswith(XML_DECL))

    def test_string_with_declaration_equals_written_file(self):
        self.odm.write_xml(self.xml_file)
        with open(self.xml_file, "rb") as fh:
            written = fh.read()
        self.assertEqual(self.odm.to_xml_string(xml_declaration=True).encode("utf-8"), written)

    def test_string_without_declaration_equals_file_remainder(self):
        self.odm.write_xml(self.xml_file)
        with open(self.xml_file, "rb") as fh:
            written = fh.read()
        self.assertEqual(self.odm.to_xml_string().encode("utf-8"),
                         written[len(XML_DECL.encode("utf-8")):])

    def test_keyword_only(self):
        with self.assertRaises(TypeError):
            self.odm.to_xml_string(True)

    def test_round_trips_with_declaration(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.load_odm_string(self.odm.to_xml_string(xml_declaration=True))
        self.assertEqual(loader.root().FileOID, "ODM.STR.1")

    def test_round_trips_without_declaration(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.load_odm_string(self.odm.to_xml_string())
        self.assertEqual(loader.root().FileOID, "ODM.STR.1")

    def test_declaration_is_the_only_difference(self):
        self.assertEqual(self.odm.to_xml_string(xml_declaration=True),
                         XML_DECL + self.odm.to_xml_string())

    def test_dataset_json_accepts_the_keyword(self):
        """Parity fix: the keyword must reach the intended NotImplementedError."""
        ds = DatasetJSON.__new__(DatasetJSON)
        with self.assertRaises(NotImplementedError):
            ds.to_xml_string(xml_declaration=True)
        with self.assertRaises(NotImplementedError):
            ds.to_xml_string()


class TestXmlDeclarationOptionDefine21(TestCase):
    """The same byte relationship on a real Define-XML 2.1 document."""

    def setUp(self):
        NS.NamespaceRegistry(prefix="def", uri=DEFINE_NS)
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1", ns_uri=DEFINE_NS))
        loader.open_odm_document(os.path.join(DATA_DIR, "defineV21-SDTM.xml"))
        self.define = loader.root()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.xml_file = os.path.join(self.tmp.name, "define_out.xml")

    def test_string_with_declaration_equals_written_file(self):
        self.define.write_xml(self.xml_file)
        with open(self.xml_file, "rb") as fh:
            written = fh.read()
        self.assertEqual(self.define.to_xml_string(xml_declaration=True).encode("utf-8"), written)

    def test_string_without_declaration_equals_file_remainder(self):
        self.define.write_xml(self.xml_file)
        with open(self.xml_file, "rb") as fh:
            written = fh.read()
        self.assertEqual(self.define.to_xml_string().encode("utf-8"),
                         written[len(XML_DECL.encode("utf-8")):])

    def test_declared_string_reparses_standalone(self):
        root = ET.fromstring(self.define.to_xml_string())
        self.assertEqual(root.tag, "{" + ODM_NS + "}ODM")


class TestNestedElementNamespaceBinding(TestCase):
    """A nested element must serialize with its document's namespaces, not global state."""

    def setUp(self):
        NS.NamespaceRegistry(prefix="def", uri=DEFINE_NS)
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1", ns_uri=DEFINE_NS))
        loader.open_odm_document(os.path.join(DATA_DIR, "defineV21-SDTM.xml"))
        self.define = loader.root()
        self.mdv = self.define.Study.MetaDataVersion

    def _poison_registry(self):
        """Re-register def -> v2.0 globally, as importing the 2.0 model does."""
        NS.NamespaceRegistry(prefix="def", uri=DEFINE_20_NS)

    def test_root_is_bound(self):
        self.assertIsNotNone(NS.get_document_namespaces(self.define))

    def test_nested_element_is_bound(self):
        self.assertIsNotNone(NS.get_document_namespaces(self.mdv))

    def test_deeply_nested_element_is_bound(self):
        igd = self.mdv.ItemGroupDef[0]
        self.assertIsNotNone(NS.get_document_namespaces(igd))

    def test_nested_element_keeps_load_time_namespace(self):
        self._poison_registry()
        self.assertIn('xmlns:def="' + DEFINE_NS + '"', self.mdv.to_xml_string())
        self.assertNotIn(DEFINE_20_NS, self.mdv.to_xml_string())

    def test_deeply_nested_element_keeps_load_time_namespace(self):
        self._poison_registry()
        igd = self.mdv.ItemGroupDef[0]
        self.assertIn('xmlns:def="' + DEFINE_NS + '"', igd.to_xml_string())

    def test_write_xml_on_nested_element_keeps_load_time_namespace(self):
        self._poison_registry()
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "mdv.xml")
            self.mdv.write_xml(out)
            with open(out, "r", encoding="utf-8") as fh:
                written = fh.read()
        self.assertIn('xmlns:def="' + DEFINE_NS + '"', written)

    def test_element_created_after_load_is_unbound(self):
        """Documented residual limitation: post-load elements carry no snapshot."""
        fresh = DEFINE.ItemGroupDef(OID="IG.NEW", Name="New", Repeating="No",
                                    IsReferenceData="No", Purpose="Tabulation",
                                    Structure="One record per subject",
                                    ArchiveLocationID="LF.TS")
        self.assertIsNone(NS.get_document_namespaces(fresh))

    def test_explicit_rebind_fixes_a_post_load_element(self):
        fresh = DEFINE.ItemGroupDef(OID="IG.NEW", Name="New", Repeating="No",
                                    IsReferenceData="No", Purpose="Tabulation",
                                    Structure="One record per subject",
                                    ArchiveLocationID="LF.TS")
        NS.bind_document_namespaces(fresh, NS.get_document_namespaces(self.define))
        self.assertIsNotNone(NS.get_document_namespaces(fresh))
        self._poison_registry()
        self.assertIn('xmlns:def="' + DEFINE_NS + '"', fresh.to_xml_string())

    def test_recursive_bind_terminates_on_a_cycle(self):
        class Cyclic:
            _elems = []

        first, second = Cyclic(), Cyclic()
        first.child = second
        second.child = first
        NS.bind_document_namespaces(first, recursive=True)   # must not recurse forever
        self.assertIsNotNone(NS.get_document_namespaces(first))
        self.assertIsNotNone(NS.get_document_namespaces(second))

    def test_recursive_bind_tolerates_non_weakrefable_objects(self):
        class NoWeakref:
            __slots__ = ("_elems",)

        NS.bind_document_namespaces(NoWeakref(), recursive=True)   # must not raise

    def test_non_recursive_bind_leaves_children_unbound(self):
        """The default stays non-recursive, so existing callers are unaffected."""
        odm = _build_odm()
        NS.bind_document_namespaces(odm)
        self.assertIsNotNone(NS.get_document_namespaces(odm))
        self.assertIsNone(NS.get_document_namespaces(odm.Study[0]))

    def test_open_define_context_manager_binds_the_subtree(self):
        from odmlib.context import open_define

        path = os.path.join(DATA_DIR, "defineV21-SDTM.xml")
        with open_define(path, write_on_exit=False) as define:
            self.assertIsNotNone(NS.get_document_namespaces(define.Study.MetaDataVersion))


class TestSetOdmNamespaceAttributesStringDeprecated(TestCase):
    def test_emits_deprecation_warning(self):
        from odmlib.exceptions import OdmlibDeprecationWarning

        nsr = NS.NamespaceRegistry()
        with self.assertWarns(OdmlibDeprecationWarning):
            nsr.set_odm_namespace_attributes_string("<ODM FileOID='X'></ODM>")
