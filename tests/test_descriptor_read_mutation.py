"""Regression tests: reading unset attributes must not corrupt output.

Reading an unset optional child element auto-creates it (so the chained
population idiom `rc.ErrorMessage.TranslatedText.append(...)` works), but
serialization must skip auto-created elements that were never populated —
previously a read-only inspection injected spurious empty elements into
the serialized XML/JSON.  find()/find_all()/find_by() must also tolerate
unset single children (which read as None when the child class has
required attributes) and scalar attribute names instead of crashing.
"""
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM


def make_study():
    study = ODM.Study(OID="ST.001")
    study.GlobalVariables = ODM.GlobalVariables()
    study.GlobalVariables.StudyName = ODM.StudyName(_content="Test Study")
    study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="desc")
    study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="proto")
    return study


class TestReadDoesNotCorruptOutput(TestCase):
    def test_reading_unset_child_does_not_serialize_it(self):
        study = make_study()
        _ = study.BasicDefinitions  # read-only inspection
        elem = study.to_xml()
        self.assertIsNone(elem.find("BasicDefinitions"))
        self.assertNotIn("BasicDefinitions", study.to_dict())

    def test_populated_auto_created_child_serializes(self):
        rc = ODM.RangeCheck(Comparator="EQ", SoftHard="Soft")
        rc.ErrorMessage.TranslatedText.append(
            ODM.TranslatedText(_content="out of range", lang="en"))
        elem = rc.to_xml()
        self.assertIsNotNone(elem.find("ErrorMessage"))

    def test_explicitly_assigned_empty_child_serializes(self):
        study = make_study()
        study.BasicDefinitions = ODM.BasicDefinitions()
        elem = study.to_xml()
        self.assertIsNotNone(elem.find("BasicDefinitions"))

    def test_reading_child_with_required_attrs_returns_none(self):
        mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test")
        # Include requires StudyOID and MetaDataVersionOID, so it cannot be
        # auto-created; reading it must return None rather than raising
        self.assertIsNone(mdv.Include)

    def test_reading_unset_scalar_returns_none_without_storing(self):
        mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test")
        self.assertIsNone(mdv.Description)
        self.assertNotIn("Description", mdv.__dict__)


class TestFindGuards(TestCase):
    def setUp(self):
        self.mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test")

    def test_find_on_unset_single_child_returns_none(self):
        self.assertIsNone(self.mdv.find("Include", "StudyOID", "ST.001"))

    def test_find_all_on_unset_single_child_returns_empty(self):
        self.assertEqual(self.mdv.find_all("Include", "StudyOID", "ST.001"), [])

    def test_find_by_on_unset_single_child_returns_none(self):
        self.assertIsNone(self.mdv.find_by("Include", StudyOID="ST.001"))

    def test_find_on_scalar_attribute_returns_none(self):
        self.assertIsNone(self.mdv.find("Name", "x", "y"))
