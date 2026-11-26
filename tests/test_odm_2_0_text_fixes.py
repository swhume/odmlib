"""ODM 2.0 text fixes (P2.6).

* D107: the spec allows only ``text/plain`` and ``application/xhtml+xml`` as a
  ``TranslatedText/@Type``; odmlib's own examples used ``text/html``. The XSD types
  the attribute as free text, so the model still accepts any value (the opt-in rule
  checker, P5, is where D107 is enforced).
* ``Coding/@CommentOID`` is free text in the XSD but a ``CommentDef`` reference in
  the spec. odmlib loads any XSD-valid value, and the OID checker applies the spec.
"""
import inspect
from unittest import TestCase

import odmlib.odm_2_0.model as ODM2
from odmlib import create_oid_checker
from odmlib.exceptions import OdmlibOIDError


def _mdv(comment_oid):
    mdv = ODM2.MetaDataVersion(OID="MDV.1", Name="MDV")
    itd = ODM2.ItemDef(OID="IT.AE", Name="AE", DataType="text")
    itd.Coding = [ODM2.Coding(Code="10019211", System="MedDRA", CommentOID=comment_oid)]
    mdv.ItemDef = [itd]
    description = ODM2.Description(TranslatedText=[
        ODM2.TranslatedText(_content="Coded with MedDRA 26.1", lang="en", Type="text/plain")])
    mdv.CommentDef = [ODM2.CommentDef(OID="COM.1", Description=description)]
    return mdv


class TestTranslatedTextType(TestCase):

    def test_documented_example_uses_the_spec_media_type(self):
        doc = inspect.getdoc(ODM2.TranslatedText)
        self.assertIn('Type="application/xhtml+xml"', doc)
        self.assertNotIn("text/html", doc)

    def test_xhtml_text_round_trips(self):
        tt = ODM2.TranslatedText(lang="en", Type="application/xhtml+xml",
                                 div="<div><p>Bold</p></div>")
        self.assertEqual(tt.to_dict()["Type"], "application/xhtml+xml")


class TestCodingCommentOID(TestCase):
    """Both behaviours are deliberate; this pins them."""

    def test_any_xsd_valid_value_loads(self):
        self.assertEqual(ODM2.Coding(System="MedDRA", CommentOID="").CommentOID, "")
        self.assertEqual(ODM2.Coding(System="MedDRA", CommentOID="not an oid").CommentOID,
                         "not an oid")

    def test_oid_checker_treats_it_as_a_comment_def_reference(self):
        self.assertEqual(create_oid_checker("odm_2_0").ref_def["CommentOID"], "CommentDef")
        self.assertTrue(_mdv("COM.1").verify_oids(create_oid_checker("odm_2_0")))

    def test_dangling_comment_oid_is_reported(self):
        with self.assertRaises(OdmlibOIDError) as ctx:
            _mdv("COM.MISSING").verify_oids(create_oid_checker("odm_2_0"))
        self.assertEqual(ctx.exception.attribute, "CommentOID")
