"""Regression tests for data-shape bugs found in review.

- ODMBuilder left stale current-element pointers when a new scope opened,
  so with_description()/with_alias() attached to the wrong element.
- A single-child ODMObject descriptor accepted ANY list without checking
  item types (only ODMListObject validated items).
- dataframe_to_items silently dropped rows that failed construction.
"""
import warnings
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM
from odmlib.builder import ODMBuilder
from odmlib.exceptions import OdmlibTypeError


class TestBuilderCurrentPointers(TestCase):
    def _builder(self):
        return (ODMBuilder()
                .add_study(OID="ST.001", study_name="S", study_description="D",
                           protocol_name="P")
                .add_metadata_version(OID="MDV.001", Name="MDV"))

    def test_description_after_new_item_group_targets_the_group(self):
        b = self._builder()
        b.add_item_def(OID="IT.AGE", Name="AGE", DataType="integer")
        b.add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        b.with_description("Demographics dataset")
        mdv = b._current_mdv
        igd = mdv.ItemGroupDef[0]
        item = mdv.ItemDef[0]
        self.assertIsNotNone(igd.__dict__.get("Description"))
        self.assertIsNone(item.__dict__.get("Description"))

    def test_new_study_clears_previous_scope(self):
        b = self._builder()
        b.add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        b.add_study(OID="ST.002", study_name="S2", study_description="D2",
                    protocol_name="P2")
        self.assertIsNone(b._current_mdv)
        self.assertIsNone(b._current_igd)
        with self.assertRaises(RuntimeError):
            b.add_item_group_def(OID="IG.AE", Name="AE", Repeating="No")


class TestODMObjectListValidation(TestCase):
    def test_single_child_rejects_list_of_wrong_type(self):
        mu = ODM.MeasurementUnit(OID="MU.CM", Name="cm")
        with self.assertRaises(OdmlibTypeError):
            mu.Symbol = ["not a symbol"]

    def test_single_child_accepts_valid_instance(self):
        mu = ODM.MeasurementUnit(OID="MU.CM", Name="cm")
        mu.Symbol = ODM.Symbol()
        self.assertIsInstance(mu.Symbol, ODM.Symbol)


class TestDataFrameRowDropWarning(TestCase):
    def test_failed_rows_warn(self):
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas not installed")
        from odmlib.dataframe import dataframe_to_items

        df = pd.DataFrame([
            {"OID": "IT.AGE", "Name": "AGE", "DataType": "integer"},
            {"OID": "IT.BAD", "Name": "BAD", "DataType": "not-a-type"},
        ])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 1)
        self.assertTrue(any("Skipping DataFrame row" in str(w.message)
                            for w in caught))
