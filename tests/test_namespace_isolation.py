"""Regression tests for namespace registry correctness.

The NamespaceRegistry is shared process-wide (Borg pattern), which
previously caused several defects fixed together:

- xmlns was resolved from *current* global state at write time, so loading
  a second document changed the namespaces a first document serialized with.
- Every registered prefix was emitted on every document, so importing an
  unrelated model package polluted output with unused declarations.
- arm_1_0 registered itself as a *default* namespace, making the effective
  default depend on import order.
- An empty registry crashed the writer with a bare IndexError.
- to_xml_string() emitted no xmlns declarations at all.
"""
import os
import tempfile
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL
from odmlib.exceptions import OdmlibNamespaceError

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CDASH_XML = os.path.join(DATA_DIR, "cdash-odm-test.xml")
ODM_13_URI = "http://www.cdisc.org/ns/odm/v1.3"
ODM_20_URI = "http://www.cdisc.org/ns/odm/v2.0"


class TestWriteUsesLoadTimeNamespaces(TestCase):
    def test_second_default_does_not_corrupt_first_document(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document(CDASH_XML)
        odm = loader.root()
        # simulate loading a second document under a different default namespace
        NS.NamespaceRegistry(prefix="odm", uri=ODM_20_URI, is_default=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "out.xml")
            odm.write_xml(out)
            root = ET.parse(out).getroot()
        self.assertEqual(root.tag, "{%s}ODM" % ODM_13_URI)

    def test_to_xml_string_is_reparseable(self):
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document(CDASH_XML)
        odm = loader.root()
        xml_string = odm.to_xml_string()
        root = ET.fromstring(xml_string)
        self.assertEqual(root.tag, "{%s}ODM" % ODM_13_URI)


class TestUnusedPrefixFiltering(TestCase):
    def test_unused_prefix_not_emitted(self):
        NS.NamespaceRegistry(prefix="zzz", uri="http://example.com/zzz")
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document(CDASH_XML)
        odm = loader.root()
        with tempfile.TemporaryDirectory() as tmpdir:
            out = os.path.join(tmpdir, "out.xml")
            odm.write_xml(out)
            with open(out, encoding="utf-8") as f:
                content = f.read()
        self.assertNotIn("xmlns:zzz", content)
        self.assertNotIn("xmlns:xml=", content)  # reserved prefix, never declared


class TestSingleDefaultNamespace(TestCase):
    def test_arm_is_not_registered_as_default(self):
        import odmlib.arm_1_0.model  # noqa: F401  (registers namespaces on import)
        NS.NamespaceRegistry.reset()
        import importlib
        import odmlib.arm_1_0.model as ARM
        importlib.reload(ARM)
        nsr = NS.NamespaceRegistry()
        self.assertNotIn("arm", nsr.default_namespace)
        self.assertIn("arm", nsr.namespaces)

    def test_new_default_replaces_previous(self):
        NS.NamespaceRegistry(prefix="odm", uri=ODM_13_URI, is_default=True, is_reset=True)
        NS.NamespaceRegistry(prefix="odm2", uri=ODM_20_URI, is_default=True)
        nsr = NS.NamespaceRegistry()
        self.assertEqual(list(nsr.default_namespace.keys()), ["odm2"])


class TestEmptyRegistryErrors(TestCase):
    def test_clear_error_when_no_default_registered(self):
        NS.NamespaceRegistry.reset()
        nsr = NS.NamespaceRegistry()
        with self.assertRaises(OdmlibNamespaceError):
            nsr.get_odm_namespace_entries()
        with self.assertRaises(OdmlibNamespaceError):
            nsr.set_odm_namespace_attributes(ET.Element("ODM"))
