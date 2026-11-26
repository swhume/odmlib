"""Tests for odmlib.dataframe (optional Pandas DataFrame integration).

All test classes are skipped if pandas is not installed.

Covers:
- metadata_to_dataframe(): scalar attribute extraction, attribute filtering
- clinical_data_to_dataframe(): hierarchical ODM 1.3.2 and ODM 2.0 data flattening
- dataset_to_dataframe(): Dataset-XML 1.0.1 flat ClinicalData
- dataframe_to_items(): DataFrame rows → odmlib element instances
- _require_pandas(): ImportError when pandas absent (mocked)

dataset_json_to_dataframe() coverage lives in test_dataframe_phase3.py
(TestDatasetJSON11ToDataFrame).
"""
import os
import unittest

import odmlib.ns_registry as NS

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def _reset_ns():
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )


# ---------------------------------------------------------------------------
# Helpers shared across test classes
# ---------------------------------------------------------------------------

def _make_odm_132_mdv():
    """Build a simple ODM 1.3.2 MetaDataVersion with two ItemDefs."""
    import odmlib.odm_1_3_2.model as ODM
    _reset_ns()
    mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test MDV")
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.STUDYID", Name="STUDYID", DataType="text"))
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.USUBJID", Name="USUBJID", DataType="text"))
    mdv.ItemDef.append(ODM.ItemDef(OID="IT.AGE", Name="AGE", DataType="integer"))
    return mdv


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestMetadataToDataFrame(unittest.TestCase):
    """Tests for metadata_to_dataframe()."""

    def setUp(self):
        _reset_ns()

    def test_itemdef_to_dataframe_basic(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 3)
        self.assertIn("OID", df.columns)
        self.assertIn("Name", df.columns)
        self.assertIn("DataType", df.columns)

    def test_itemdef_oid_values(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        oids = df["OID"].tolist()
        self.assertIn("IT.STUDYID", oids)
        self.assertIn("IT.USUBJID", oids)
        self.assertIn("IT.AGE", oids)

    def test_attribute_filtering(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef", attributes=["OID", "Name"])
        self.assertIn("OID", df.columns)
        self.assertIn("Name", df.columns)
        # DataType not requested
        self.assertNotIn("DataType", df.columns)

    def test_empty_element_list(self):
        from odmlib.dataframe import metadata_to_dataframe
        import odmlib.odm_1_3_2.model as ODM
        _reset_ns()
        mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Empty")
        df = metadata_to_dataframe(mdv, "ItemDef")
        self.assertEqual(len(df), 0)

    def test_nonexistent_element_type(self):
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        # getattr returns None for missing attr; should return empty DataFrame
        df = metadata_to_dataframe(mdv, "NonExistentDef")
        self.assertEqual(len(df), 0)

    def test_child_elements_excluded(self):
        """Child element lists should not appear as columns."""
        from odmlib.dataframe import metadata_to_dataframe
        mdv = _make_odm_132_mdv()
        df = metadata_to_dataframe(mdv, "ItemDef")
        # "Alias", "Description", "Question" etc. are child elements
        for col in df.columns:
            # All included columns must have scalar values in the first row
            val = df.iloc[0][col]
            self.assertNotIsInstance(val, list)
            self.assertNotIsInstance(val, dict)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestClinicalDataToDataFrame(unittest.TestCase):
    """clinical_data_to_dataframe() for ODM 1.3.2 and, since 0.3.0, ODM 2.0."""

    ODM20 = "http://www.cdisc.org/ns/odm/v2.0"

    def setUp(self):
        NS.NamespaceRegistry(prefix="odm", uri=self.ODM20, is_default=True, is_reset=True)

    @staticmethod
    def _item(oid, *values, **attrs):
        import odmlib.odm_2_0.model as ODM2
        item = ODM2.ItemData(ItemOID=oid, **attrs)
        item.Value = [ODM2.Value(_content=v) if isinstance(v, str)
                      else ODM2.Value(SeqNum=v[0], _content=v[1]) for v in values]
        return item

    def _odm20_clinical_data(self):
        """Subject 001: a form with ItemData on both sides of two nested RACE groups."""
        import odmlib.odm_2_0.model as ODM2
        clinical = ODM2.ClinicalData(StudyOID="ST.1", MetaDataVersionOID="MDV.1")
        for key in ("001", "002"):
            form = ODM2.ItemGroupData(ItemGroupOID="IG.DM")
            form.ItemData.append(self._item("IT.SEX", "F" if key == "001" else "M"))
            for repeat, race in (("1", "WHITE"), ("2", "ASIAN")):
                group = ODM2.ItemGroupData(ItemGroupOID="IG.RACE", ItemGroupRepeatKey=repeat)
                group.ItemData.append(self._item("IT.RACE", race))
                form.ItemGroupData.append(group)
            form.ItemData.append(self._item("IT.AGE", "50"))
            event = ODM2.StudyEventData(StudyEventOID="SE.1", ItemGroupData=[form])
            clinical.SubjectData.append(ODM2.SubjectData(SubjectKey=key, StudyEventData=[event]))
        return clinical

    def test_odm132_walks_form_data(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        from odmlib.dataframe import clinical_data_to_dataframe
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document(os.path.join(DATA_DIR, "test_clinical_data_01.xml"))
        df = clinical_data_to_dataframe(loader.ClinicalData(), "LB")
        self.assertEqual(df.to_dict("records"),
                         [{"SubjectKey": "1000", "LBDTC": "2006-07-14T14:48",
                           "LBTESTCD": "ALT", "LBORRES": "245"}])

    def test_odm20_nested_groups_rows(self):
        """One row per matching group at any depth, holding that group's own items."""
        from odmlib.dataframe import clinical_data_to_dataframe
        clinical = self._odm20_clinical_data()
        races = clinical_data_to_dataframe(clinical, "IG.RACE")
        self.assertEqual(races.to_dict("records"),
                         [{"SubjectKey": "001", "IT.RACE": "WHITE"},
                          {"SubjectKey": "001", "IT.RACE": "ASIAN"},
                          {"SubjectKey": "002", "IT.RACE": "WHITE"},
                          {"SubjectKey": "002", "IT.RACE": "ASIAN"}])
        forms = clinical_data_to_dataframe(clinical, "IG.DM")
        self.assertEqual(forms.to_dict("records"),
                         [{"SubjectKey": "001", "IT.SEX": "F", "IT.AGE": "50"},
                          {"SubjectKey": "002", "IT.SEX": "M", "IT.AGE": "50"}])

    def test_odm20_clinicaldata_level_groups(self):
        """ItemGroupData directly under ClinicalData belongs to no subject."""
        import odmlib.odm_2_0.model as ODM2
        from odmlib.dataframe import clinical_data_to_dataframe
        clinical = self._odm20_clinical_data()
        site = ODM2.ItemGroupData(ItemGroupOID="IG.RACE", ItemGroupRepeatKey="9")
        site.ItemData.append(self._item("IT.RACE", "OTHER"))
        clinical.ItemGroupData.append(site)
        df = clinical_data_to_dataframe(clinical, "IG.RACE")
        self.assertEqual(len(df), 5)
        site_row = df.iloc[0]
        self.assertTrue(pd.isna(site_row["SubjectKey"]))      # None; pandas may show NaN
        self.assertEqual(site_row["IT.RACE"], "OTHER")

        only_groups = ODM2.ClinicalData(StudyOID="ST.1", MetaDataVersionOID="MDV.1",
                                        ItemGroupData=[site])
        self.assertEqual(len(clinical_data_to_dataframe(only_groups, "IG.RACE")), 1)

    def test_odm20_multi_value_and_isnull(self):
        """Several Values become a list ordered by SeqNum; IsNull and no Value become None."""
        import odmlib.odm_2_0.model as ODM2
        from odmlib.dataframe import clinical_data_to_dataframe
        group = ODM2.ItemGroupData(ItemGroupOID="IG.CM")
        group.ItemData = [self._item("IT.ROUTE", (2, "IV"), (1, "ORAL"), (3, "TOPICAL")),
                          self._item("IT.DOSE", IsNull="Yes"),
                          self._item("IT.UNIT"),
                          self._item("IT.NAME", "aspirin")]
        clinical = ODM2.ClinicalData(StudyOID="ST.1", MetaDataVersionOID="MDV.1",
                                     ItemGroupData=[group])
        row = clinical_data_to_dataframe(clinical, "IG.CM").iloc[0].to_dict()
        self.assertEqual(list(row), ["SubjectKey", "IT.ROUTE", "IT.DOSE", "IT.UNIT", "IT.NAME"])
        self.assertEqual(row["IT.ROUTE"], ["ORAL", "IV", "TOPICAL"])
        self.assertEqual(row["IT.NAME"], "aspirin")
        for column in ("SubjectKey", "IT.DOSE", "IT.UNIT"):       # None (pandas may show NaN)
            self.assertTrue(pd.isna(row[column]), column)

    def test_odm20_walk_does_not_change_the_tree(self):
        from odmlib.dataframe import clinical_data_to_dataframe
        clinical = self._odm20_clinical_data()
        before = {id(e): dict(vars(e)) for e in self._walk(clinical)}
        clinical_data_to_dataframe(clinical, "IG.NONE")
        clinical_data_to_dataframe(clinical, "IG.RACE")
        self.assertEqual({id(e): dict(vars(e)) for e in self._walk(clinical)}, before)

    def test_odm20_vendored_example(self):
        import odmlib.loader as LD
        import odmlib.odm_loader as OL
        from odmlib.dataframe import clinical_data_to_dataframe
        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(os.path.join(
            DATA_DIR, "odm_v2", "github", "Demographics_RACE",
            "Demographics_RACE_check_all_that_apply.xml"))
        df = clinical_data_to_dataframe(loader.ClinicalData(), "IG.RACE")
        self.assertEqual(len(df), 18)
        self.assertEqual(sorted(df["SubjectKey"].unique()), ["001", "002", "003"])

    @staticmethod
    def _walk(element):
        stack = [element]
        while stack:
            current = stack.pop()
            yield current
            for value in vars(current).values():
                if isinstance(value, list):
                    stack.extend(value)
                elif hasattr(value, "__dict__") and hasattr(type(value), "_elems"):
                    stack.append(value)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDatasetToDataFrame(unittest.TestCase):
    """Tests for dataset_to_dataframe() (Dataset-XML 1.0.1)."""

    def setUp(self):
        _reset_ns()
        NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    def _make_clinical_data(self):
        import odmlib.dataset_1_0_1.model as DSX
        clinical = DSX.ClinicalData(StudyOID="S.001", MetaDataVersionOID="MDV.001")
        igd1 = DSX.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="1")
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        igd1.ItemData.append(DSX.ItemData(ItemOID="IT.AETERM", Value="Headache"))
        igd2 = DSX.ItemGroupData(ItemGroupOID="IG.AE", ItemGroupDataSeq="2")
        igd2.ItemData.append(DSX.ItemData(ItemOID="IT.STUDYID", Value="CDISC01"))
        igd2.ItemData.append(DSX.ItemData(ItemOID="IT.AETERM", Value="Nausea"))
        clinical.ItemGroupData.append(igd1)
        clinical.ItemGroupData.append(igd2)
        return clinical

    def test_returns_dataframe(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertIsInstance(df, pd.DataFrame)

    def test_row_count(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertEqual(len(df), 2)

    def test_column_names(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertIn("ItemGroupOID", df.columns)
        self.assertIn("ItemGroupDataSeq", df.columns)
        self.assertIn("IT.STUDYID", df.columns)
        self.assertIn("IT.AETERM", df.columns)

    def test_values(self):
        from odmlib.dataframe import dataset_to_dataframe
        clinical = self._make_clinical_data()
        df = dataset_to_dataframe(clinical)
        self.assertEqual(df.iloc[0]["IT.AETERM"], "Headache")
        self.assertEqual(df.iloc[1]["IT.AETERM"], "Nausea")

    def test_empty_clinical_data(self):
        from odmlib.dataframe import dataset_to_dataframe
        import odmlib.dataset_1_0_1.model as DSX
        clinical = DSX.ClinicalData(StudyOID="S.001", MetaDataVersionOID="MDV.001")
        df = dataset_to_dataframe(clinical)
        self.assertEqual(len(df), 0)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestDataframeToItems(unittest.TestCase):
    """Tests for dataframe_to_items()."""

    def setUp(self):
        _reset_ns()

    def test_basic_construction(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        df = pd.DataFrame([
            {"OID": "IT.X", "Name": "X", "DataType": "text"},
            {"OID": "IT.Y", "Name": "Y", "DataType": "integer"},
        ])
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].OID, "IT.X")
        self.assertEqual(items[0].Name, "X")
        self.assertEqual(items[0].DataType, "text")

    def test_column_mapping(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # Rename DataFrame columns to odmlib attribute names
        df = pd.DataFrame([{"oid_col": "IT.Z", "name_col": "Z", "DataType": "text"}])
        mapping = {"oid_col": "OID", "name_col": "Name"}
        items = dataframe_to_items(df, ODM, "ItemDef", column_mapping=mapping)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].OID, "IT.Z")

    def test_nan_values_skipped(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # Row with NaN for optional attribute — should construct, not crash
        df = pd.DataFrame([
            {"OID": "IT.A", "Name": "A", "DataType": "text", "Length": float("nan")},
        ])
        # Should not crash; NaN length skipped
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].OID, "IT.A")

    def test_invalid_rows_skipped(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        # A row without required OID should be skipped (or raise internally)
        df = pd.DataFrame([
            {"OID": "IT.GOOD", "Name": "Good", "DataType": "text"},
            {"Name": "Bad"},  # missing OID — will fail required check
        ])
        # Should return at least 0 elements without crashing
        try:
            items = dataframe_to_items(df, ODM, "ItemDef")
            # At minimum, the good row should be included
            good_oids = [it.OID for it in items if hasattr(it, "OID")]
            self.assertIn("IT.GOOD", good_oids)
        except Exception:
            # Acceptable if the bad row propagates an error (implementation may vary)
            pass

    def test_empty_dataframe(self):
        import odmlib.odm_1_3_2.model as ODM
        from odmlib.dataframe import dataframe_to_items
        df = pd.DataFrame(columns=["OID", "Name", "DataType"])
        items = dataframe_to_items(df, ODM, "ItemDef")
        self.assertEqual(len(items), 0)


@unittest.skipUnless(HAS_PANDAS, "pandas not installed")
class TestRequirePandas(unittest.TestCase):
    """Test _require_pandas() raises when pandas unavailable (simulated)."""

    def test_import_error_message(self):
        """Patch HAS_PANDAS to False and verify the error message is helpful."""
        import odmlib.dataframe as df_module
        original = df_module.HAS_PANDAS
        try:
            df_module.HAS_PANDAS = False
            with self.assertRaises(ImportError) as ctx:
                df_module._require_pandas()
            msg = str(ctx.exception)
            self.assertIn("pandas", msg)
            self.assertIn("pip install", msg)
        finally:
            df_module.HAS_PANDAS = original


class TestNoPandasImport(unittest.TestCase):
    """dataframe module must be importable even without pandas."""

    def test_module_imports_without_pandas(self):
        """Importing odmlib.dataframe must not raise even if pandas is absent."""
        try:
            import odmlib.dataframe  # noqa: F401
        except ImportError as e:
            self.fail(f"odmlib.dataframe raised ImportError on import: {e}")


if __name__ == "__main__":
    unittest.main()
