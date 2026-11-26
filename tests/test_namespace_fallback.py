"""Prefixes missing from the namespace registry are declared or reported, never dropped.

Prefixed names (``xs:schemaLocation``, ``xlink:href``, ``def:leaf``) get their ``xmlns:``
declarations from ``NamespaceRegistry.set_odm_namespace_attributes()``. Before 0.3.0 a
used prefix the registry (or the document's snapshot) did not hold was skipped silently,
and the output could not be re-parsed. ``NamespaceRegistry.reset()`` -- called by the
conftest before every test, and by the README's build recipes -- removes ``xs`` and
``xlink``, and no loader registers them again.

Now a missing prefix that odmlib binds to one URI everywhere
(``ns_registry.FIXED_PREFIX_URIS``) is declared from that table, and any other missing
prefix raises an ``OdmlibInteroperabilityWarning``. Output whose prefixes are all
registered is unchanged.

The conftest leaves only ``odm`` -> ODM v1.3 registered, which is the state under test.
"""
import ast
import glob
import os
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
from unittest import mock

import odmlib.define_2_1.model as DEF
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_2_0.model as ODM2
from odmlib.exceptions import OdmlibInteroperabilityWarning
from odmlib.odm_parser import ODMSchemaValidator

ODM13 = "http://www.cdisc.org/ns/odm/v1.3"
ODM20 = "http://www.cdisc.org/ns/odm/v2.0"
DEF21 = "http://www.cdisc.org/ns/def/v2.1"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
XLINK = "http://www.w3.org/1999/xlink"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _odm_132_root():
    return ODM.ODM(FileOID="F.1", FileType="Snapshot", CreationDateTime="2026-10-16T09:00:00",
                   schemaLocation=f"{ODM13} ODM1-3-2.xsd")


def _leaf():
    return DEF.leaf(ID="LF.ACRF", href="acrf.pdf", title=DEF.title(_content="aCRF"))


def _write(element):
    """Serialize, recording any OdmlibInteroperabilityWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        text = element.to_xml_string()
    return text, [w for w in caught if issubclass(w.category, OdmlibInteroperabilityWarning)]


class TestFixedPrefixesAreDeclared(unittest.TestCase):
    """xs, xlink, nciodm, data and arm have one URI in every model package."""

    def test_odm_132_schema_location(self):
        text, caught = _write(_odm_132_root())
        root = ET.fromstring(text)
        self.assertEqual(root.get(f"{{{XSI}}}schemaLocation"), f"{ODM13} ODM1-3-2.xsd")
        self.assertIn(f'xmlns:xs="{XSI}"', text)
        self.assertEqual(caught, [])

    def test_odm_20_schema_location(self):
        NS.NamespaceRegistry(prefix="odm", uri=ODM20, is_default=True, is_reset=True)
        odm = ODM2.ODM(FileOID="F.1", FileType="Snapshot", CreationDateTime="2026-10-16T09:00:00",
                       schemaLocation=f"{ODM20} ODM.xsd", ODMVersion="2.0")
        odm.Study.append(ODM2.Study(OID="ST.1", StudyName="S", ProtocolName="P",
                                    MetaDataVersion=[ODM2.MetaDataVersion(OID="MDV.1", Name="V")]))
        text, caught = _write(odm)
        validator = ODMSchemaValidator(standard="odm", version="2.0")
        self.assertTrue(validator.validate_tree(ET.ElementTree(ET.fromstring(text))))
        self.assertEqual(caught, [])

    def test_define_leaf_href(self):
        NS.NamespaceRegistry(prefix="def", uri=DEF21)
        text, caught = _write(_leaf())
        leaf = ET.fromstring(text)
        self.assertEqual(leaf.get(f"{{{XLINK}}}href"), "acrf.pdf")
        self.assertEqual(caught, [])

    def test_dataset_xml_data_prefix(self):
        import odmlib.dataset_1_0_1.model as DS
        group = DS.ItemGroupData(ItemGroupOID="IG.DM", ItemGroupDataSeq=1)
        text, caught = _write(group)
        self.assertEqual(
            ET.fromstring(text).get("{http://www.cdisc.org/ns/Dataset-XML/v1.0}ItemGroupDataSeq"),
            "1")
        self.assertEqual(caught, [])

    def test_without_the_table_the_output_is_unparseable(self):
        """The scenario these tests cover is the real one: nothing else declares xs."""
        with mock.patch.dict(NS.FIXED_PREFIX_URIS, clear=True):
            text, caught = _write(_odm_132_root())
        self.assertEqual(len(caught), 1)
        with self.assertRaises(ET.ParseError):
            ET.fromstring(text)


class TestLoadedDocuments(unittest.TestCase):
    """A loaded document's snapshot lacks xs and xlink after a reset, too."""

    def test_define_loaded_after_reset_writes_parseable_xml(self):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(os.path.join(REPO_ROOT, "tests", "data", "defineV21-SDTM.xml"))
        define = loader.root()
        text, caught = _write(define)
        root = ET.fromstring(text)
        self.assertIsNotNone(root.find(f".//{{{DEF21}}}leaf").get(f"{{{XLINK}}}href"))
        self.assertEqual(caught, [])
        reloaded = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        reloaded.load_odm_string(text)
        self.assertEqual(reloaded.root().to_xml_string(), text)

    def test_write_xml_matches_to_xml_string(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "odm.xml")
            root = _odm_132_root()
            root.write_xml(path)
            with open(path, encoding="utf-8") as written:
                self.assertEqual(written.read(), root.to_xml_string(xml_declaration=True))


class TestRegisteredPrefixesUnchanged(unittest.TestCase):
    """Valid output today must stay byte-identical."""

    def test_registered_prefixes_take_precedence(self):
        NS.NamespaceRegistry(prefix="def", uri=DEF21)
        NS.NamespaceRegistry(prefix="xs", uri=XSI)
        NS.NamespaceRegistry(prefix="xlink", uri=XLINK)
        with_table = _odm_132_root().to_xml_string() + _leaf().to_xml_string()
        with mock.patch.dict(NS.FIXED_PREFIX_URIS, clear=True):
            without_table = _odm_132_root().to_xml_string() + _leaf().to_xml_string()
        self.assertEqual(with_table, without_table)


class TestUnresolvablePrefixes(unittest.TestCase):
    def test_version_dependent_prefix_warns(self):
        """def is v2.0 or v2.1 depending on the model, so it cannot be filled in."""
        text, caught = _write(_leaf())
        self.assertEqual(len(caught), 1)
        message = str(caught[0].message)
        self.assertIn("'def'", message)
        self.assertIn("NamespaceRegistry(prefix='def'", message)
        self.assertNotIn("xmlns:def", text)

    def test_locally_declared_markup_prefixes_do_not_warn(self):
        """XHTML markup declares its own extra prefixes on the element that uses them."""
        NS.NamespaceRegistry(prefix="odm", uri=ODM20, is_default=True, is_reset=True)
        tt = ODM2.TranslatedText(
            Type="text/html", lang="en",
            div='<div xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:vendor" v:note="x">'
                '<p xml:lang="fr">Oui</p></div>')
        text, caught = _write(tt)
        self.assertEqual(caught, [])
        ET.fromstring(text)


class TestTableMatchesTheModels(unittest.TestCase):
    """Every model package binds each fixed prefix to the URI in FIXED_PREFIX_URIS.

    Read from the source with ``ast`` -- re-importing a model would re-run its
    registrations and recreate its classes. A model that binds one of these prefixes to
    another URI must take the prefix out of the table, or the fallback would declare
    the wrong namespace.
    """

    def test_registrations_agree(self):
        seen = {}
        for path in sorted(glob.glob(os.path.join(REPO_ROOT, "odmlib", "*", "model.py"))):
            with open(path, encoding="utf-8") as source:
                tree = ast.parse(source.read())
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and getattr(node.func, "attr", None)
                        == "NamespaceRegistry"):
                    continue
                kwargs = {k.arg: k.value.value for k in node.keywords
                          if isinstance(k.value, ast.Constant)}
                prefix, uri = kwargs.get("prefix"), kwargs.get("uri")
                if prefix in NS.FIXED_PREFIX_URIS:
                    seen.setdefault(prefix, set()).add((uri, os.path.relpath(path, REPO_ROOT)))
        self.assertEqual(sorted(seen), sorted(NS.FIXED_PREFIX_URIS))
        for prefix, bindings in seen.items():
            for uri, path in bindings:
                self.assertEqual(uri, NS.FIXED_PREFIX_URIS[prefix],
                                 f"{path} binds {prefix!r} to {uri}")


if __name__ == "__main__":
    unittest.main()
