"""Regression tests for schema-ordered child element serialization.

The ODM/Define-XML XSDs prescribe a strict declaration order for the children
of complex elements (e.g. ``ItemGroupDef``: ``Description`` → ``ItemRef`` →
``Alias``; the Define 2.1 extension adds ``def:Class`` and ``def:leaf``).

Prior to the fix in odmlib v0.2.0, ``ODMElement.to_xml()`` iterated
``self.__dict__`` and emitted children in attribute insertion order — which
depended on whatever order the user happened to assign attributes (and on
whether ``__init__`` had already pre-populated list defaults). The result was
schema-invalid XML when users assigned children "out of order".

These tests pin the new behaviour: ``to_xml()`` always emits children in
``_elems`` (model declaration) order, regardless of how attributes were
assigned to the instance.
"""
import unittest
import xml.etree.ElementTree as ET

import odmlib.odm_1_3_2.model as ODM
import odmlib.define_2_1.model as DEFINE
import odmlib.ns_registry as NS


def _local(tag):
    """Strip ElementTree's `{uri}` prefix and any odmlib `def:` prefix from a tag name."""
    if "}" in tag:
        tag = tag.split("}", 1)[1]
    if ":" in tag:
        tag = tag.split(":", 1)[1]
    return tag


class TestSchemaOrderedSerialization(unittest.TestCase):
    """to_xml() must emit children in model declaration order."""

    def test_itemdef_children_emitted_in_schema_order(self):
        """ItemDef children: Description, Question, ..., Alias — even when assigned out of order."""
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        # assign in REVERSE schema order
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Question = ODM.Question()
        itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of birth", lang="en"))

        elem = itd.to_xml()
        children = [_local(c.tag) for c in elem]
        # Description must come first, then Question, then Alias
        self.assertEqual(children, ["Description", "Question", "Alias"])

    def test_itemgroupdef_children_emitted_in_schema_order(self):
        """ItemGroupDef: Description before ItemRef, even when ItemRef populated first."""
        igd = ODM.ItemGroupDef(OID="ODM.IG.VS", Name="Vital Signs", Repeating="Yes")
        # populate ItemRef list first (the "obvious" usage path)
        igd.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.VS.VSDAT", Mandatory="Yes"))
        igd.ItemRef.append(ODM.ItemRef(ItemOID="ODM.IT.VS.VSORRES", Mandatory="Yes"))
        # then assign Description
        igd.Description = ODM.Description()
        igd.Description.TranslatedText.append(ODM.TranslatedText(_content="Vital Signs", lang="en"))

        elem = igd.to_xml()
        children = [_local(c.tag) for c in elem]
        self.assertEqual(children[0], "Description")
        self.assertEqual(children[1:], ["ItemRef", "ItemRef"])

    def test_define21_itemgroupdef_class_after_itemrefs(self):
        """Define-XML 2.1 ItemGroupDef: Description, ItemRef*, def:Class — schema order preserved.

        This is the exact pattern from notebooks/first_define.ipynb that motivated the fix:
        Description.TranslatedText is mutated, ItemRefs are appended, and Class is assigned
        last. The serializer must still emit Description → ItemRef* → def:Class.
        """
        NS.NamespaceRegistry.reset()

        igd = DEFINE.ItemGroupDef(
            OID="IG.VS",
            Name="Vital Signs",
            Repeating="Yes",
            IsReferenceData="No",
            SASDatasetName="VS",
            Domain="VS",
            Purpose="Tabulation",
            Structure="One Record Per Subject Per Vital Signs Test",
        )
        # mirror the notebook pattern: TranslatedText first, then ItemRef append, then Class last
        igd.Description = DEFINE.Description()
        igd.Description.TranslatedText.append(DEFINE.TranslatedText(_content="Vital Signs", lang="en"))
        for i, oid in enumerate(["IT.VS.STUDYID", "IT.VS.DOMAIN", "IT.VS.USUBJID"], start=1):
            igd.ItemRef.append(DEFINE.ItemRef(ItemOID=oid, Mandatory="Yes", OrderNumber=i))
        igd.leaf = DEFINE.leaf(ID="LF.VS", href="vs.xpt")
        igd.leaf.title = DEFINE.title(_content="vs.xpt")
        igd.Class = DEFINE.Class(Name="FINDINGS")

        elem = igd.to_xml()
        children = [_local(c.tag) for c in elem]
        self.assertEqual(
            children,
            ["Description", "ItemRef", "ItemRef", "ItemRef", "Class", "leaf"],
            f"Children must follow schema order; got {children}",
        )

    def test_to_xml_element_order_survives_reparse(self):
        """Serialize → parse → re-serialize gives the same element order.

        Note this exercises to_xml()/ET.tostring(), NOT to_xml_string() - it was
        misleadingly named test_to_xml_string_round_trip_unchanged until 0.2.2, which
        is part of why the string path went untested. The real to_xml_string()
        round-trip lives in the next test and in tests/test_xml_string_serialization.py.
        """
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="DOB", lang="en"))

        first = itd.to_xml()
        first_children = [_local(c.tag) for c in first]

        # parse the serialized XML back into a string and check children are still ordered
        s = ET.tostring(first, encoding="unicode")
        reparsed = ET.fromstring(s)
        reparsed_children = [_local(c.tag) for c in reparsed]
        self.assertEqual(first_children, reparsed_children)
        self.assertEqual(first_children, ["Description", "Alias"])

    def test_to_xml_string_round_trip_preserves_order(self):
        """The real to_xml_string() round-trip: it re-parses standalone, in order."""
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="DOB", lang="en"))

        # to_xml_string() declares its own namespaces, so this parses with no fixup
        xml_str = itd.to_xml_string()
        self.assertIn('xmlns="http://www.cdisc.org/ns/odm/v1.3"', xml_str)
        reparsed = ET.fromstring(xml_str)
        self.assertEqual([_local(c.tag) for c in reparsed], ["Description", "Alias"])

    def test_unset_optional_children_skipped(self):
        """When an optional child is not assigned, it must be silently skipped."""
        # ItemDef has many optional children (Description, Question, MeasurementUnitRef, ...).
        # Build a minimal one and ensure to_xml() doesn't error and produces no spurious children.
        itd = ODM.ItemDef(OID="ODM.IT.MIN", Name="Minimal", DataType="text")
        elem = itd.to_xml()
        # No children should be emitted because none were assigned.
        self.assertEqual(list(elem), [])

    def test_attribute_serialization_unchanged(self):
        """Attribute serialization is a separate code path and must be unaffected by the fix."""
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer", Length=4)
        elem = itd.to_xml()
        self.assertEqual(elem.attrib["OID"], "ODM.IT.DM.BRTHYR")
        self.assertEqual(elem.attrib["Name"], "Birth Year")
        self.assertEqual(elem.attrib["DataType"], "integer")
        self.assertEqual(elem.attrib["Length"], "4")

    def test_content_text_preserved(self):
        """_content text emission is unrelated to the child loop and must still work."""
        tt = ODM.TranslatedText(_content="Hello", lang="en")
        elem = tt.to_xml()
        self.assertEqual(elem.text, "Hello")


if __name__ == "__main__":
    unittest.main()
