"""Tests for ODMMeta merge_fields subclassing support.

Previously ODMMeta rebuilt _fields/_elems/_attrs from the subclass body
only, so a subclass had to redeclare every inherited field: a pass-only
subclass of ItemDef silently dropped ALL inherited children from to_xml()
and rejected inherited kwargs in __init__.  The Define-XML models exploit
that behaviour deliberately to *restrict* inherited ODM fields, so
inheritance-merging is opt-in via the ``merge_fields=True`` class keyword.
"""
from unittest import TestCase

import odmlib.define_2_1.model as DEFINE
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
from odmlib.exceptions import OdmlibRequiredAttributeError, OdmlibTypeError


class ExtendedItemDef(ODM.ItemDef, merge_fields=True):
    """Extension subclass — inherits every ItemDef field, adds one."""
    Priority = T.Integer()


class PassThroughItemDef(ODM.ItemDef, merge_fields=True):
    pass


class TestMergeFieldsSubclassing(TestCase):
    def test_pass_subclass_inherits_all_fields(self):
        self.assertEqual(PassThroughItemDef._fields, ODM.ItemDef._fields)
        self.assertEqual(set(PassThroughItemDef._elems), set(ODM.ItemDef._elems))

    def test_extension_appends_new_field_at_end(self):
        self.assertEqual(ExtendedItemDef._fields[:-1], ODM.ItemDef._fields)
        self.assertEqual(ExtendedItemDef._fields[-1], "Priority")

    def test_inherited_kwargs_accepted(self):
        item = ExtendedItemDef(OID="IT.AGE", Name="AGE", DataType="integer", Priority=1)
        self.assertEqual(item.OID, "IT.AGE")
        self.assertEqual(item.Priority, 1)

    def test_inherited_required_attrs_enforced(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            ExtendedItemDef(Name="AGE", DataType="integer")

    def test_inherited_children_serialize(self):
        item = ExtendedItemDef(OID="IT.AGE", Name="AGE", DataType="integer")
        item.Description = ODM.Description()
        item.Description.TranslatedText.append(
            ODM.TranslatedText(_content="Age in years", lang="en"))
        elem = item.to_xml()
        self.assertIsNotNone(elem.find("Description"))

    def test_redeclared_field_repositions(self):
        class ReorderedItemDef(ODM.ItemDef, merge_fields=True):
            Alias = ODM.ItemDef.Alias
            Extra = T.String()

        self.assertEqual(ReorderedItemDef._fields[-2:], ["Alias", "Extra"])
        self.assertNotIn("Alias", ReorderedItemDef._fields[:-2])


class TestRestrictedSubclassStrictness(TestCase):
    """Define models drop inherited ODM fields; those must stay unassignable."""

    def test_dropped_child_element_rejected_on_assignment(self):
        item = DEFINE.ItemDef(OID="IT.X", Name="X", DataType="text")
        with self.assertRaises(OdmlibTypeError):
            item.Question = ODM.Question()

    def test_dropped_scalar_rejected_on_assignment(self):
        item = DEFINE.ItemDef(OID="IT.X", Name="X", DataType="text")
        with self.assertRaises(OdmlibTypeError):
            item.SDSVarName = "AGE"

    def test_dropped_field_rejected_as_kwarg(self):
        with self.assertRaises(OdmlibTypeError):
            DEFINE.ItemDef(OID="IT.X", Name="X", DataType="text", SDSVarName="AGE")

    def test_define_item_def_unchanged(self):
        item = DEFINE.ItemDef(OID="IT.X", Name="X", DataType="text",
                              DisplayFormat="8.1")
        self.assertEqual(item.DisplayFormat, "8.1")
