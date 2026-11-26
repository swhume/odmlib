"""``find``/``find_all``/``find_by`` accept a compiled pattern or a predicate (P2.4, D4).

A compiled ``re.Pattern`` must match the whole value (converted with ``str()``), a
callable is called with the stored value, and anything else -- including a plain
string full of regex metacharacters -- is still compared with ``==``.
"""
import re
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM


def _mdv():
    mdv = ODM.MetaDataVersion(OID="MDV.1", Name="MDV")
    mdv.ItemDef = [
        ODM.ItemDef(OID="IT.AE.AETERM", Name="AETERM", DataType="text", Length=200),
        ODM.ItemDef(OID="IT.AE.AESEV", Name="aesev", DataType="text", Length=8),
        ODM.ItemDef(OID="IT.DM.AGE", Name="AGE", DataType="integer", Length=3),
        ODM.ItemDef(OID="IT.DM.SEX", Name="SEX", DataType="text"),          # no Length
        ODM.ItemDef(OID="IT.X.(A|B)", Name="META", DataType="text", Length=1),
    ]
    return mdv


def _oids(items):
    return [item.OID for item in items]


class TestPatterns(TestCase):

    def test_full_match_not_partial(self):
        mdv = _mdv()
        self.assertEqual(_oids(mdv.find_all("ItemDef", "OID", re.compile(r"IT\.AE\..+"))),
                         ["IT.AE.AETERM", "IT.AE.AESEV"])
        # "AE" alone matches nothing: the pattern must cover the whole value
        self.assertEqual(mdv.find_all("ItemDef", "OID", re.compile("AE")), [])
        self.assertIsNone(mdv.find("ItemDef", "OID", re.compile("IT.AE")))

    def test_regex_flags_are_honoured(self):
        mdv = _mdv()
        self.assertEqual(mdv.find_by("ItemDef", Name=re.compile("^AE.*", re.I)).OID, "IT.AE.AETERM")
        self.assertEqual(_oids(mdv.find_all("ItemDef", "Name", re.compile("ae.*", re.I))),
                         ["IT.AE.AETERM", "IT.AE.AESEV"])

    def test_unset_attribute_never_matches_a_pattern(self):
        mdv = _mdv()
        # SEX has no Length; ".*" would match "None" if None were stringified
        self.assertNotIn("IT.DM.SEX", _oids(mdv.find_all("ItemDef", "Length", re.compile(".*"))))
        self.assertEqual(len(mdv.find_all("ItemDef", "Length", re.compile(".*"))), 4)

    def test_numeric_attributes_match_via_str(self):
        mdv = _mdv()
        # whole-value match: one digit selects Length 8, 3 and 1, not 200
        self.assertEqual(_oids(mdv.find_all("ItemDef", "Length", re.compile(r"\d"))),
                         ["IT.AE.AESEV", "IT.DM.AGE", "IT.X.(A|B)"])
        self.assertEqual(mdv.find("ItemDef", "Length", re.compile("200")).OID, "IT.AE.AETERM")


class TestCallables(TestCase):

    def test_predicate_selects_by_value(self):
        mdv = _mdv()
        self.assertEqual(_oids(mdv.find_all("ItemDef", "Length", lambda v: v and v > 8)),
                         ["IT.AE.AETERM"])

    def test_predicate_sees_none_for_unset(self):
        self.assertEqual(_oids(_mdv().find_all("ItemDef", "Length", lambda v: v is None)),
                         ["IT.DM.SEX"])

    def test_predicate_errors_propagate(self):
        with self.assertRaises(TypeError):
            _mdv().find_all("ItemDef", "Length", lambda v: v > 8)   # None > 8

    def test_class_is_compared_not_called(self):
        """A type is callable, but passing one means equality, as before."""
        self.assertEqual(_mdv().find_all("ItemDef", "Length", int), [])


class TestPlainValuesUnchanged(TestCase):

    def test_plain_string_with_metacharacters_matches_exactly(self):
        mdv = _mdv()
        self.assertEqual(mdv.find("ItemDef", "OID", "IT.X.(A|B)").Name, "META")
        self.assertIsNone(mdv.find("ItemDef", "OID", "IT.X.A"))
        self.assertIsNone(mdv.find("ItemDef", "OID", "IT.AE..*"))

    def test_plain_equality_still_works(self):
        mdv = _mdv()
        self.assertEqual(mdv.find("ItemDef", "Length", 8).OID, "IT.AE.AESEV")
        self.assertEqual(_oids(mdv.find_all("ItemDef", "DataType", "integer")), ["IT.DM.AGE"])


class TestFindBy(TestCase):

    def test_mixed_keyword_criteria(self):
        mdv = _mdv()
        found = mdv.find_by("ItemDef", OID=re.compile(r"IT\.AE\..*"), DataType="text",
                            Length=lambda v: v is not None and v < 100)
        self.assertEqual(found.OID, "IT.AE.AESEV")
        self.assertIsNone(mdv.find_by("ItemDef", OID=re.compile(r"IT\.DM\..*"), Length=200))

    def test_single_child_element(self):
        itd = ODM.ItemDef(OID="IT.X", Name="X", DataType="text")
        itd.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY")
        self.assertIs(itd.find("CodeListRef", "CodeListOID", re.compile("CL.*")), itd.CodeListRef)
        self.assertEqual(itd.find_all("CodeListRef", "CodeListOID", re.compile("XX")), [])

    def test_searches_direct_children_only(self):
        study = ODM.Study(OID="ST.1")
        study.MetaDataVersion = [_mdv()]
        # ItemDef lives under MetaDataVersion, not directly under Study
        self.assertEqual(study.find_all("MetaDataVersion", "OID", re.compile("MDV.*"))[0].OID,
                         "MDV.1")
        with self.assertRaises(AttributeError):
            study.find_all("ItemDef", "OID", re.compile(".*"))
