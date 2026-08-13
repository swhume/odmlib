"""Regression tests for OID validation gaps found in review.

- Define-XML document references are ID-based (leaf/@ID referenced by
  DocumentRef/@leafID and ItemGroupDef/@def:ArchiveLocationID) and were
  never surfaced to the OID checkers, so dangling references passed.
- DynamicOIDRef.add_oid returned for skip_elem element types before the
  uniqueness check, so duplicate ItemGroupDef OIDs in Define-XML were
  never detected.
- The deprecated manual ODM 1.3.2 OIDRef crashed with raw KeyError on
  attributes it did not pre-register (SignatureOID) and on defined
  element types missing from def_ref.
"""
import warnings
from unittest import TestCase

import odmlib.define_2_1.model as DEFINE
import odmlib.odm_1_3_2.rules.oid_ref as ODM_OID_REF
from odmlib.exceptions import OdmlibOIDError
from odmlib.oid_generator import create_oid_checker


def make_mdv(**overrides):
    kwargs = {"OID": "MDV.001", "Name": "Test MDV", "DefineVersion": "2.1.0"}
    kwargs.update(overrides)
    return DEFINE.MetaDataVersion(**kwargs)


class TestLeafReferenceValidation(TestCase):
    def test_dangling_leafid_detected(self):
        mdv = make_mdv()
        mdv.leaf.append(DEFINE.leaf(ID="LF.CRF", href="crf.pdf"))
        comment = DEFINE.CommentDef(OID="COM.1")
        comment.DocumentRef.append(DEFINE.DocumentRef(leafID="LF.MISSING"))
        mdv.CommentDef.append(comment)
        checker = create_oid_checker("define_2_1")
        with self.assertRaises(OdmlibOIDError):
            mdv.verify_oids(checker)

    def test_valid_leafid_passes(self):
        mdv = make_mdv()
        mdv.leaf.append(DEFINE.leaf(ID="LF.CRF", href="crf.pdf"))
        comment = DEFINE.CommentDef(OID="COM.1")
        comment.DocumentRef.append(DEFINE.DocumentRef(leafID="LF.CRF"))
        mdv.CommentDef.append(comment)
        checker = create_oid_checker("define_2_1")
        self.assertTrue(mdv.verify_oids(checker))

    def test_dangling_archive_location_id_detected(self):
        mdv = make_mdv()
        igd = DEFINE.ItemGroupDef(
            OID="IG.DM", Name="DM", Repeating="No", Purpose="Tabulation",
            Structure="One record per subject", ArchiveLocationID="LF.MISSING",
        )
        mdv.ItemGroupDef.append(igd)
        checker = create_oid_checker("define_2_1")
        with self.assertRaises(OdmlibOIDError):
            mdv.verify_oids(checker)


class TestDuplicateOIDDetection(TestCase):
    def test_duplicate_item_group_def_oid_detected(self):
        mdv = make_mdv()
        for name in ("AE", "AE2"):
            mdv.ItemGroupDef.append(DEFINE.ItemGroupDef(
                OID="IG.AE", Name=name, Repeating="No", Purpose="Tabulation",
                Structure="One record per event"))
        checker = create_oid_checker("define_2_1")
        with self.assertRaises(OdmlibOIDError):
            mdv.verify_oids(checker)

    def test_unique_item_group_def_oids_pass(self):
        mdv = make_mdv()
        for name in ("AE", "DM"):
            mdv.ItemGroupDef.append(DEFINE.ItemGroupDef(
                OID=f"IG.{name}", Name=name, Repeating="No", Purpose="Tabulation",
                Structure="One record per subject"))
        checker = create_oid_checker("define_2_1")
        self.assertTrue(mdv.verify_oids(checker))


class TestManualCheckerCrashGuards(TestCase):
    def setUp(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.checker = ODM_OID_REF.OIDRef()

    def test_unregistered_oid_ref_attr_does_not_crash(self):
        # SignatureOID is not pre-registered in _init_oid_ref; this raised KeyError
        self.checker.add_oid_ref("SIG.001", "SignatureOID")

    def test_unreferenced_check_handles_unknown_def_element(self):
        # element types missing from def_ref raised KeyError
        self.checker.oid["SD.001"] = "SignatureDef"
        orphans = self.checker.check_unreferenced_oids()
        self.assertNotIn("SD.001", orphans)
