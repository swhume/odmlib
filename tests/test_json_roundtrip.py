"""True round-trip tests through XML and JSON (0.3.0 plan, P3).

Every fixture in :func:`_roundtrip.all_fixtures` runs through five legs as a subTest:

=====  =============================================================  ====================
Leg    Path                                                           Comparison
=====  =============================================================  ====================
A      XML -> obj -> XML                                              canonically equal,
                                                                      no reordering
B      XML -> obj -> JSON file -> JSON loader -> obj -> XML           canonically equal
                                                                      after N4
C      JSON -> obj -> JSON                                            dicts equal, no
                                                                      normalization
D      XML-loaded tree vs JSON-loaded tree                            ``to_dict()`` equal
E      ``to_dict()`` vs the vendored ``.json`` (ODM 2.0)              equal
=====  =============================================================  ====================

The vendored ODM 2.0 ClinicalData documents joined in P4. Their JSON was produced by
odm-v2's own converter, not by odmlib, so leg E is an independent check of the data layer.

The normalizer (N1-N5, in ``tests/_roundtrip.py``) is the complete list of forgiven
differences, and ``KNOWN_REORDERINGS`` the one named exception. Anything else is a
library bug, to be fixed in the library, never normalized away. Leg A applies no
reordering, so it also protects the order of interleaved children. Every leg resets the
namespace registry first, so no leg can pass on namespaces an earlier load left behind.
"""
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.ns_registry as NS
import odmlib.odm_2_0.model as ODM2
import odmlib.typed as T

try:
    from . import _roundtrip as R
except ImportError:                     # run from inside tests/
    import _roundtrip as R

FIXTURES = R.all_fixtures()
XS_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)")


class _WithTempDir(TestCase):

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = folder.name


class TestLegA(_WithTempDir):
    """XML -> obj -> XML is canonically equal, with no reordering."""

    def test_xml_round_trip(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                expected, actual = R.leg_a(fixture)
                self.assertTrue(expected == actual, R.first_xml_difference(expected, actual))


class TestLegB(_WithTempDir):
    """XML -> JSON -> XML is canonically equal once interleaved groups are sorted (N4)."""

    def test_xml_through_json_round_trip(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                expected, actual = R.leg_b(fixture, self.folder)
                self.assertTrue(expected == actual, R.first_xml_difference(expected, actual))


class TestLegC(_WithTempDir):
    """JSON -> obj -> JSON gives back the same dict, with no normalization."""

    def test_json_round_trip(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                given, written = R.leg_c(fixture, self.folder)
                self.assertTrue(given == written, R.dict_differences(given, written))


class TestLegD(_WithTempDir):
    """A tree loaded from XML and one loaded from its JSON have the same to_dict()."""

    def test_xml_and_json_trees_agree(self):
        for fixture in FIXTURES:
            with self.subTest(fixture=fixture.name):
                from_xml, from_json = R.leg_d(fixture, self.folder)
                self.assertTrue(from_xml == from_json, R.dict_differences(from_xml, from_json))


class TestLegE(TestCase):
    """odmlib's to_dict() matches the JSON vendored alongside each ODM v2.0 document."""

    def test_matches_vendored_json(self):
        vendored = [f for f in FIXTURES if f.vendored_json]
        self.assertEqual(len(vendored), 25)
        for fixture in vendored:
            with self.subTest(fixture=fixture.name):
                expected, actual = R.leg_e(fixture)
                self.assertTrue(expected == actual, R.dict_differences(expected, actual))


class TestHarness(_WithTempDir):
    """Properties of the fixture set and the harness itself."""

    def test_json_leg_independent_of_registry_state(self):
        """The JSON loaders register what they need (P2.5): earlier state cannot matter."""
        fixture = next(f for f in FIXTURES if f.name == "odm_2_0/odmv2_example")
        path = R._write_json(R.load_xml(fixture), self.folder, fixture)
        results = []
        for setup in (lambda: NS.NamespaceRegistry.reset(),
                      R.reset_registry,
                      lambda: (NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
                                                    is_default=True, is_reset=True),
                               NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0"))):
            setup()
            loader = fixture.json_loader()
            loader.open_odm_document(path)
            results.append(R.canonical_xml(loader.root().to_xml_string(), fixture.model))
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(results[0], R.canonical_xml(fixture.path, fixture.model))

    def test_float_attrs_are_xs_decimal_lexical(self):
        """P2.2: floats are written as xs:decimal, never with an exponent."""
        codelist = ODM2.CodeList(OID="CL.1", Name="CL", DataType="text")
        codelist.CodeListItem = [ODM2.CodeListItem(CodedValue=str(n), Rank=rank)
                                 for n, rank in enumerate((1e-07, 2.5e16, 1.0, 0.1 + 0.2))]
        root = ET.fromstring(codelist.to_xml_string())
        ranks = [item.get("Rank") for item in root]
        self.assertEqual(ranks[:3], ["0.0000001", "25000000000000000", "1.0"])
        for rank in ranks:
            self.assertRegex(rank, XS_DECIMAL)
        self.assertEqual([float(r) for r in ranks], [1e-07, 2.5e16, 1.0, 0.1 + 0.2])

    def test_float_attrs_in_every_fixture_output_are_xs_decimal(self):
        checked = 0
        for fixture in FIXTURES:
            root = ET.fromstring(R.load_xml(fixture).to_xml_string())
            for element in root.iter():
                cls = R._model_class(fixture.model, element)
                for key, value in element.attrib.items():
                    if cls is not None and isinstance(cls._attrs.get(R._local(key)), T.Float):
                        checked += 1
                        self.assertRegex(value, XS_DECIMAL, f"{fixture.name}: {key}={value}")
        self.assertGreater(checked, 0)

    def test_some_fixtures_interleave_out_of_model_order(self):
        """Leg A only protects interleaving if some fixture actually interleaves."""
        interleaved = [f.name for f in FIXTURES
                       if R.canonical_xml(f.path, f.model)
                       != R.canonical_xml(f.path, f.model, sort_groups=True)]
        self.assertGreaterEqual(len(interleaved), 6, interleaved)
        # ItemData before a nested ItemGroupData (ItemGroupDataGroup, P4)
        self.assertIn("odm_v2/github/Demographics_RACE/Demographics_RACE_check_all_that_apply.xml",
                      interleaved)

    def test_every_vendored_clinical_data_document_is_a_fixture(self):
        clinical = R.vendored_fixtures(clinical_data=True)
        self.assertEqual(len(clinical), 12)
        self.assertLessEqual({f.name for f in clinical}, {f.name for f in FIXTURES})

    def test_known_reorderings_still_occur(self):
        """An entry in KNOWN_REORDERINGS must still describe its source document."""
        names = {f.name: f for f in FIXTURES}
        for name, reorderings in R.KNOWN_REORDERINGS.items():
            with self.subTest(fixture=name):
                self.assertIn(name, names)
                self.assertGreater(R.apply_reorderings(R.parse(names[name].path), reorderings), 0)

    def test_fixture_set_covers_every_package(self):
        self.assertEqual({f.model_package for f in FIXTURES},
                         {"odm_1_3_2", "odm_2_0", "define_2_0", "define_2_1", "arm_1_0", "ct_1_1_1"})

    def test_only_documented_fixtures_load_permissively(self):
        permissive = [f for f in FIXTURES if f.permissive]
        self.assertEqual([f.name for f in permissive], ["define_2_1/define-360i"])
        self.assertTrue(all(f.permissive_reason for f in permissive))


class TestNormalizer(TestCase):
    """The normalizer forgives exactly N1-N5, and nothing else."""

    ODM20 = "http://www.cdisc.org/ns/odm/v2.0"

    def _canonical(self, xml, **kwargs):
        return R.canonical_xml(xml, ODM2, **kwargs)

    def test_normalizer_only_reorders_group_members(self):
        """N4 sorts runs of interleaved members into model order and moves nothing else."""
        interleaved = (f'<ItemGroupDef xmlns="{self.ODM20}" OID="IG.1" Name="G" Repeating="No">'
                       f'<Description/><ItemRef ItemOID="IT.1" Mandatory="No"/>'
                       f'<ItemGroupRef ItemGroupOID="IG.2" Mandatory="No"/>'
                       f'<ItemRef ItemOID="IT.2" Mandatory="No"/><Alias Context="c" Name="n"/>'
                       f'</ItemGroupDef>')
        model_order = (f'<ItemGroupDef xmlns="{self.ODM20}" OID="IG.1" Name="G" Repeating="No">'
                       f'<Description/><ItemGroupRef ItemGroupOID="IG.2" Mandatory="No"/>'
                       f'<ItemRef ItemOID="IT.1" Mandatory="No"/>'
                       f'<ItemRef ItemOID="IT.2" Mandatory="No"/><Alias Context="c" Name="n"/>'
                       f'</ItemGroupDef>')
        self.assertNotEqual(self._canonical(interleaved), self._canonical(model_order))
        self.assertEqual(self._canonical(interleaved, sort_groups=True),
                         self._canonical(model_order, sort_groups=True))
        # members of one type keep their relative order (stable sort)
        swapped = model_order.replace('"IT.1"', '"IT.X"').replace('"IT.2"', '"IT.1"') \
                             .replace('"IT.X"', '"IT.2"')
        self.assertNotEqual(self._canonical(interleaved, sort_groups=True),
                            self._canonical(swapped, sort_groups=True))
        # a non-member moved out of place is still a difference
        alias_first = model_order.replace('<Alias Context="c" Name="n"/>', '') \
                                 .replace('<Description/>', '<Description/><Alias Context="c" Name="n"/>')
        self.assertNotEqual(self._canonical(model_order, sort_groups=True),
                            self._canonical(alias_first, sort_groups=True))

    def test_normalizer_keeps_leaf_whitespace(self):
        """N2 drops indentation, but a text element's whitespace is data."""
        spaced = f'<CheckValue xmlns="{self.ODM20}"> </CheckValue>'
        empty = f'<CheckValue xmlns="{self.ODM20}"></CheckValue>'
        self.assertNotEqual(self._canonical(spaced), self._canonical(empty))
        indented = f'<Alias xmlns="{self.ODM20}" Context="c" Name="n">\n  </Alias>'
        flat = f'<Alias xmlns="{self.ODM20}" Context="c" Name="n"/>'
        self.assertEqual(self._canonical(indented), self._canonical(flat))
        nested = (f'<Description xmlns="{self.ODM20}">\n  <TranslatedText Type="text/plain">'
                  f' x </TranslatedText>\n</Description>')
        tight = (f'<Description xmlns="{self.ODM20}"><TranslatedText Type="text/plain">'
                 f' x </TranslatedText></Description>')
        self.assertEqual(self._canonical(nested), self._canonical(tight))
        trimmed = tight.replace(" x ", "x")
        self.assertNotEqual(self._canonical(tight), self._canonical(trimmed))

    def test_normalizer_skips_xhtml(self):
        """Whitespace inside an xhtml:div is content; N2 never touches it."""
        def text(inner):
            return (f'<TranslatedText xmlns="{self.ODM20}" Type="application/xhtml+xml">'
                    f'<div xmlns="http://www.w3.org/1999/xhtml">{inner}</div></TranslatedText>')
        self.assertNotEqual(self._canonical(text("<p>a</p> <p>b</p>")),
                            self._canonical(text("<p>a</p><p>b</p>")))
        self.assertNotEqual(self._canonical(text("\n<p>a</p>")), self._canonical(text("<p>a</p>")))

    def test_numeric_normalization_scoped_to_numeric_descriptors(self):
        """N5 compares T.Integer/T.Float values by number, and leaves strings alone."""
        def item(rank, order, coded):
            return (f'<CodeListItem xmlns="{self.ODM20}" CodedValue="{coded}" Rank="{rank}" '
                    f'OrderNumber="{order}"/>')
        self.assertEqual(self._canonical(item("1", "01", "A")), self._canonical(item("1.0", "1", "A")))
        self.assertNotEqual(self._canonical(item("1", "1", "A")), self._canonical(item("2", "1", "A")))
        # CodedValue is a string: "1" and "1.0" are different values
        self.assertNotEqual(self._canonical(item("1", "1", "1")), self._canonical(item("1", "1", "1.0")))

    def test_canonical_form_compares_prefixes_by_uri(self):
        """N3: the same namespace under different prefixes is the same document."""
        default = f'<Alias xmlns="{self.ODM20}" Context="c" Name="n"/>'
        prefixed = f'<o:Alias xmlns:o="{self.ODM20}" Context="c" Name="n"/>'
        self.assertEqual(self._canonical(default), self._canonical(prefixed))
        other = '<Alias xmlns="http://www.cdisc.org/ns/odm/v1.3" Context="c" Name="n"/>'
        self.assertNotEqual(self._canonical(default), self._canonical(other))

    def test_comments_and_processing_instructions_are_dropped(self):
        """N1: ElementTree's parser drops both; odmlib models neither."""
        bare = f'<Alias xmlns="{self.ODM20}" Context="c" Name="n"/>'
        noisy = (f'<?xml-stylesheet type="text/xsl" href="x.xsl"?><!-- note -->'
                 f'<Alias xmlns="{self.ODM20}" Context="c" Name="n"><!-- inside --></Alias>')
        self.assertEqual(self._canonical(bare), self._canonical(noisy))
