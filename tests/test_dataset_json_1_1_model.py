"""Tests for the Dataset-JSON v1.1 ODMElement-based model.

Tests cover Column, SourceSystem, and DatasetJSON classes including:
- Construction with required and optional fields
- Type and value validation via descriptors
- to_dict() serialization (spec conformance, optional field omission)
- JSON and NDJSON round-trip serialization
- File I/O (write_json/read_json, write_ndjson/read_ndjson)
- Convenience methods (add_row, add_column, column_names)
- Inherited ODMElement methods (find, find_all, find_by)
- XML serialization disabled (NotImplementedError)
- Edge cases (metadata-only mode, null values in rows, empty datasets)
"""
import json
import os
import tempfile
import unittest

from odmlib.dataset_json_1_1.model import DatasetJSON, Column, SourceSystem
from odmlib.exceptions import OdmlibTypeError, OdmlibRequiredAttributeError


class TestColumn(unittest.TestCase):
    """Tests for the Column class."""

    def test_required_fields_only(self):
        col = Column(itemOID="IT.STUDYID", name="STUDYID",
                     label="Study Identifier", dataType="string")
        self.assertEqual(col.itemOID, "IT.STUDYID")
        self.assertEqual(col.name, "STUDYID")
        self.assertEqual(col.label, "Study Identifier")
        self.assertEqual(col.dataType, "string")

    def test_all_fields(self):
        col = Column(
            itemOID="IT.AGE", name="AGE", label="Age",
            dataType="integer", targetDataType="integer",
            length=3, displayFormat="8.", keySequence=1,
        )
        self.assertEqual(col.targetDataType, "integer")
        self.assertEqual(col.length, 3)
        self.assertEqual(col.displayFormat, "8.")
        self.assertEqual(col.keySequence, 1)

    def test_to_dict_required_only(self):
        col = Column(itemOID="IT.X", name="X", label="X Label",
                     dataType="string")
        d = col.to_dict()
        self.assertEqual(d, {
            "itemOID": "IT.X",
            "name": "X",
            "label": "X Label",
            "dataType": "string",
        })
        # Optional fields should not be present
        self.assertNotIn("targetDataType", d)
        self.assertNotIn("length", d)
        self.assertNotIn("displayFormat", d)
        self.assertNotIn("keySequence", d)

    def test_to_dict_all_fields(self):
        col = Column(
            itemOID="IT.AGE", name="AGE", label="Age",
            dataType="integer", targetDataType="integer",
            length=3, displayFormat="8.", keySequence=1,
        )
        d = col.to_dict()
        self.assertEqual(d["targetDataType"], "integer")
        self.assertEqual(d["length"], 3)
        self.assertEqual(d["displayFormat"], "8.")
        self.assertEqual(d["keySequence"], 1)

    def test_dataType_valid_values(self):
        for dtype in ["string", "integer", "decimal", "float", "double",
                       "boolean", "datetime", "date", "time", "URI"]:
            col = Column(itemOID="IT.X", name="X", label="X", dataType=dtype)
            self.assertEqual(col.dataType, dtype)

    def test_dataType_invalid_value(self):
        with self.assertRaises(OdmlibTypeError):
            Column(itemOID="IT.X", name="X", label="X", dataType="invalid")

    def test_targetDataType_valid_values(self):
        for tdt in ["integer", "decimal"]:
            col = Column(itemOID="IT.X", name="X", label="X",
                         dataType="date", targetDataType=tdt)
            self.assertEqual(col.targetDataType, tdt)

    def test_targetDataType_invalid_value(self):
        with self.assertRaises(OdmlibTypeError):
            Column(itemOID="IT.X", name="X", label="X",
                   dataType="string", targetDataType="float")

    def test_missing_required_field(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            Column(itemOID="IT.X", name="X")  # missing label, dataType

    def test_to_xml_raises(self):
        col = Column(itemOID="IT.X", name="X", label="X", dataType="string")
        with self.assertRaises(NotImplementedError):
            col.to_xml()

    def test_to_xml_string_raises(self):
        col = Column(itemOID="IT.X", name="X", label="X", dataType="string")
        with self.assertRaises(NotImplementedError):
            col.to_xml_string()

    def test_to_element_raises(self):
        col = Column(itemOID="IT.X", name="X", label="X", dataType="string")
        with self.assertRaises(NotImplementedError):
            col.to_element()

    def test_length_positive_integer(self):
        col = Column(itemOID="IT.X", name="X", label="X",
                     dataType="string", length=20)
        self.assertEqual(col.length, 20)

    def test_length_string_coercion(self):
        """PositiveInteger accepts string and coerces to int."""
        col = Column(itemOID="IT.X", name="X", label="X",
                     dataType="string", length="20")
        self.assertEqual(col.length, 20)

    def test_repr(self):
        col = Column(itemOID="IT.X", name="X", label="X", dataType="string")
        r = repr(col)
        self.assertIn("Column", r)


class TestSourceSystem(unittest.TestCase):
    """Tests for the SourceSystem class."""

    def test_creation(self):
        ss = SourceSystem(name="SAS", version="9.4")
        self.assertEqual(ss.name, "SAS")
        self.assertEqual(ss.version, "9.4")

    def test_to_dict(self):
        ss = SourceSystem(name="SAS", version="9.4")
        self.assertEqual(ss.to_dict(), {"name": "SAS", "version": "9.4"})

    def test_missing_required(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            SourceSystem(name="SAS")  # missing version


class TestDatasetJSON(unittest.TestCase):
    """Tests for the DatasetJSON class."""

    def _make_columns(self):
        """Create a standard set of columns for testing."""
        return [
            Column(itemOID="IT.STUDYID", name="STUDYID",
                   label="Study Identifier", dataType="string",
                   keySequence=1),
            Column(itemOID="IT.USUBJID", name="USUBJID",
                   label="Unique Subject ID", dataType="string",
                   keySequence=2),
            Column(itemOID="IT.AGE", name="AGE",
                   label="Age", dataType="integer", length=3),
        ]

    def _make_minimal(self):
        """Create a minimal DatasetJSON with required fields only."""
        return DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.DM",
            records=0,
            name="DM",
            label="Demographics",
        )

    def _make_full(self):
        """Create a fully-populated DatasetJSON."""
        return DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            fileOID="FILE001",
            dbLastModifiedDateTime="2023-12-31T23:59:59",
            originator="ACME Corp",
            sourceSystem=SourceSystem(name="SAS", version="9.4"),
            studyOID="STUDY001",
            metaDataVersionOID="MDV001",
            metaDataRef="define.xml",
            itemGroupOID="IG.DM",
            records=2,
            name="DM",
            label="Demographics",
            columns=self._make_columns(),
            rows=[
                ["STUDY01", "SUBJ001", 84],
                ["STUDY01", "SUBJ002", 76],
            ],
        )

    # --- Construction ---

    def test_required_fields_only(self):
        dsj = self._make_minimal()
        self.assertEqual(dsj.datasetJSONCreationDateTime, "2024-01-01T00:00:00")
        self.assertEqual(dsj.datasetJSONVersion, "1.1.0")
        self.assertEqual(dsj.itemGroupOID, "IG.DM")
        self.assertEqual(dsj.records, 0)
        self.assertEqual(dsj.name, "DM")
        self.assertEqual(dsj.label, "Demographics")

    def test_all_fields(self):
        dsj = self._make_full()
        self.assertEqual(dsj.fileOID, "FILE001")
        self.assertEqual(dsj.dbLastModifiedDateTime, "2023-12-31T23:59:59")
        self.assertEqual(dsj.originator, "ACME Corp")
        self.assertEqual(dsj.sourceSystem.name, "SAS")
        self.assertEqual(dsj.studyOID, "STUDY001")
        self.assertEqual(dsj.metaDataVersionOID, "MDV001")
        self.assertEqual(dsj.metaDataRef, "define.xml")

    def test_missing_required_field(self):
        with self.assertRaises(OdmlibRequiredAttributeError):
            DatasetJSON(
                datasetJSONCreationDateTime="2024-01-01T00:00:00",
                datasetJSONVersion="1.1.0",
                # missing itemGroupOID, records, name, label
            )

    # --- columns initialization ---

    def test_columns_default_empty_list(self):
        dsj = self._make_minimal()
        self.assertIsInstance(dsj.columns, list)
        self.assertEqual(dsj.columns, [])

    def test_columns_in_dict(self):
        # columns should be in __dict__ even when empty (set by __init__)
        dsj = self._make_minimal()
        self.assertIn("columns", dsj.__dict__)

    # --- Convenience methods ---

    def test_add_column(self):
        dsj = self._make_minimal()
        col = Column(itemOID="IT.X", name="X", label="X", dataType="string")
        dsj.add_column(col)
        self.assertEqual(len(dsj.columns), 1)
        self.assertEqual(dsj.columns[0].name, "X")

    def test_add_row_valid(self):
        dsj = self._make_minimal()
        dsj.add_column(Column(itemOID="IT.X", name="X", label="X",
                               dataType="string"))
        dsj.add_row(["val1"])
        self.assertEqual(dsj.rows, [["val1"]])
        self.assertEqual(dsj.records, 1)

    def test_add_row_wrong_length(self):
        dsj = self._make_minimal()
        dsj.add_column(Column(itemOID="IT.X", name="X", label="X",
                               dataType="string"))
        with self.assertRaises(ValueError) as ctx:
            dsj.add_row(["val1", "extra"])
        self.assertIn("2 values", str(ctx.exception))
        self.assertIn("1 columns", str(ctx.exception))

    def test_add_row_auto_increments_records(self):
        dsj = self._make_minimal()
        dsj.add_column(Column(itemOID="IT.X", name="X", label="X",
                               dataType="string"))
        dsj.add_row(["a"])
        self.assertEqual(dsj.records, 1)
        dsj.add_row(["b"])
        self.assertEqual(dsj.records, 2)
        dsj.add_row(["c"])
        self.assertEqual(dsj.records, 3)

    def test_column_names_property(self):
        dsj = self._make_full()
        self.assertEqual(dsj.column_names, ["STUDYID", "USUBJID", "AGE"])

    def test_column_names_empty(self):
        dsj = self._make_minimal()
        self.assertEqual(dsj.column_names, [])

    # --- to_dict() ---

    def test_to_dict_structure(self):
        dsj = self._make_full()
        d = dsj.to_dict()
        # Required top-level fields
        self.assertEqual(d["datasetJSONCreationDateTime"], "2024-01-01T00:00:00")
        self.assertEqual(d["datasetJSONVersion"], "1.1.0")
        self.assertEqual(d["itemGroupOID"], "IG.DM")
        self.assertEqual(d["records"], 2)
        self.assertEqual(d["name"], "DM")
        self.assertEqual(d["label"], "Demographics")
        # columns is a list of dicts
        self.assertIsInstance(d["columns"], list)
        self.assertEqual(len(d["columns"]), 3)
        self.assertEqual(d["columns"][0]["itemOID"], "IT.STUDYID")
        # rows is a list of lists
        self.assertIsInstance(d["rows"], list)
        self.assertEqual(d["rows"][0], ["STUDY01", "SUBJ001", 84])

    def test_to_dict_omits_none_optionals(self):
        dsj = self._make_minimal()
        d = dsj.to_dict()
        for key in ["fileOID", "dbLastModifiedDateTime", "originator",
                     "sourceSystem", "studyOID", "metaDataVersionOID",
                     "metaDataRef"]:
            self.assertNotIn(key, d,
                             f"Optional field '{key}' should be omitted when None")

    def test_to_dict_includes_optional_when_set(self):
        dsj = self._make_full()
        d = dsj.to_dict()
        self.assertEqual(d["fileOID"], "FILE001")
        self.assertEqual(d["originator"], "ACME Corp")
        self.assertEqual(d["sourceSystem"], {"name": "SAS", "version": "9.4"})
        self.assertEqual(d["studyOID"], "STUDY001")
        self.assertEqual(d["metaDataRef"], "define.xml")

    def test_to_dict_omits_empty_rows(self):
        dsj = self._make_minimal()
        d = dsj.to_dict()
        self.assertNotIn("rows", d)

    def test_to_dict_includes_empty_columns(self):
        dsj = self._make_minimal()
        d = dsj.to_dict()
        self.assertIn("columns", d)
        self.assertEqual(d["columns"], [])

    def test_to_dict_no_internal_fields(self):
        dsj = self._make_minimal()
        d = dsj.to_dict()
        for key in d:
            self.assertFalse(key.startswith("_"),
                             f"Internal field '{key}' should not be in to_dict()")

    # --- Metadata-only mode ---

    def test_metadata_only_mode(self):
        """records > 0 but no rows transferred (metadata-only file)."""
        dsj = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.DM",
            records=100,  # data exists but not transferred
            name="DM",
            label="Demographics",
            columns=self._make_columns(),
        )
        d = dsj.to_dict()
        self.assertEqual(d["records"], 100)
        self.assertNotIn("rows", d)
        self.assertEqual(len(d["columns"]), 3)

    # --- JSON serialization ---

    def test_to_json(self):
        dsj = self._make_full()
        json_str = dsj.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], "DM")
        self.assertEqual(len(parsed["rows"]), 2)

    def test_from_json(self):
        dsj = self._make_full()
        json_str = dsj.to_json()
        dsj2 = DatasetJSON.from_json(json_str)
        self.assertEqual(dsj2.name, "DM")
        self.assertEqual(dsj2.records, 2)
        self.assertEqual(dsj2.column_names, ["STUDYID", "USUBJID", "AGE"])
        self.assertEqual(dsj2.rows, [["STUDY01", "SUBJ001", 84],
                                      ["STUDY01", "SUBJ002", 76]])

    def test_json_roundtrip(self):
        dsj = self._make_full()
        json_str = dsj.to_json()
        dsj2 = DatasetJSON.from_json(json_str)
        self.assertEqual(dsj.to_dict(), dsj2.to_dict())

    def test_json_roundtrip_minimal(self):
        dsj = self._make_minimal()
        json_str = dsj.to_json()
        dsj2 = DatasetJSON.from_json(json_str)
        self.assertEqual(dsj.to_dict(), dsj2.to_dict())

    # --- File I/O ---

    def test_write_json_read_json_roundtrip(self):
        dsj = self._make_full()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmpfile = f.name
        try:
            dsj.write_json(tmpfile)
            dsj2 = DatasetJSON.read_json(tmpfile)
            self.assertEqual(dsj.to_dict(), dsj2.to_dict())
        finally:
            os.unlink(tmpfile)

    def test_write_json_read_json_minimal(self):
        dsj = self._make_minimal()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmpfile = f.name
        try:
            dsj.write_json(tmpfile)
            dsj2 = DatasetJSON.read_json(tmpfile)
            self.assertEqual(dsj.to_dict(), dsj2.to_dict())
        finally:
            os.unlink(tmpfile)

    # --- NDJSON ---

    def test_write_ndjson_structure(self):
        dsj = self._make_full()
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
            tmpfile = f.name
        try:
            dsj.write_ndjson(tmpfile)
            with open(tmpfile) as f:
                lines = f.readlines()
            # Line 1: metadata (no rows key)
            meta = json.loads(lines[0])
            self.assertNotIn("rows", meta)
            self.assertEqual(meta["name"], "DM")
            self.assertEqual(meta["records"], 2)
            # Lines 2+: one row per line
            self.assertEqual(len(lines), 3)  # 1 metadata + 2 data rows
            row1 = json.loads(lines[1])
            self.assertEqual(row1, ["STUDY01", "SUBJ001", 84])
            row2 = json.loads(lines[2])
            self.assertEqual(row2, ["STUDY01", "SUBJ002", 76])
        finally:
            os.unlink(tmpfile)

    def test_ndjson_roundtrip(self):
        dsj = self._make_full()
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
            tmpfile = f.name
        try:
            dsj.write_ndjson(tmpfile)
            dsj2 = DatasetJSON.read_ndjson(tmpfile)
            self.assertEqual(dsj.to_dict(), dsj2.to_dict())
        finally:
            os.unlink(tmpfile)

    def test_ndjson_metadata_only(self):
        """NDJSON with no rows is just one line."""
        dsj = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.DM",
            records=0,
            name="DM",
            label="Demographics",
            columns=self._make_columns(),
        )
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
            tmpfile = f.name
        try:
            dsj.write_ndjson(tmpfile)
            with open(tmpfile) as f:
                lines = f.readlines()
            self.assertEqual(len(lines), 1)  # metadata only
            dsj2 = DatasetJSON.read_ndjson(tmpfile)
            self.assertEqual(dsj2.name, "DM")
            self.assertEqual(dsj2.records, 0)
        finally:
            os.unlink(tmpfile)

    def test_read_ndjson_empty_file(self):
        with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False,
                                          mode="w") as f:
            tmpfile = f.name
        try:
            with self.assertRaises(ValueError):
                DatasetJSON.read_ndjson(tmpfile)
        finally:
            os.unlink(tmpfile)

    # --- XML disabled ---

    def test_to_xml_raises(self):
        dsj = self._make_minimal()
        with self.assertRaises(NotImplementedError):
            dsj.to_xml()

    def test_to_xml_string_raises(self):
        dsj = self._make_minimal()
        with self.assertRaises(NotImplementedError):
            dsj.to_xml_string()

    def test_to_element_raises(self):
        dsj = self._make_minimal()
        with self.assertRaises(NotImplementedError):
            dsj.to_element()

    def test_write_xml_raises(self):
        dsj = self._make_minimal()
        with self.assertRaises(NotImplementedError):
            dsj.write_xml("dummy.xml")

    # --- from_dict ---

    def test_from_dict_with_source_system(self):
        data = {
            "datasetJSONCreationDateTime": "2024-01-01T00:00:00",
            "datasetJSONVersion": "1.1.0",
            "sourceSystem": {"name": "R", "version": "4.3"},
            "itemGroupOID": "IG.AE",
            "records": 0,
            "name": "AE",
            "label": "Adverse Events",
            "columns": [],
        }
        dsj = DatasetJSON.from_dict(data)
        self.assertIsInstance(dsj.sourceSystem, SourceSystem)
        self.assertEqual(dsj.sourceSystem.name, "R")
        self.assertEqual(dsj.sourceSystem.version, "4.3")

    def test_from_dict_with_columns_and_rows(self):
        data = {
            "datasetJSONCreationDateTime": "2024-01-01T00:00:00",
            "datasetJSONVersion": "1.1.0",
            "itemGroupOID": "IG.DM",
            "records": 1,
            "name": "DM",
            "label": "Demographics",
            "columns": [
                {"itemOID": "IT.X", "name": "X", "label": "Var X",
                 "dataType": "string"},
            ],
            "rows": [["val1"]],
        }
        dsj = DatasetJSON.from_dict(data)
        self.assertEqual(len(dsj.columns), 1)
        self.assertIsInstance(dsj.columns[0], Column)
        self.assertEqual(dsj.columns[0].name, "X")
        self.assertEqual(dsj.rows, [["val1"]])

    def test_from_dict_metadata_only(self):
        data = {
            "datasetJSONCreationDateTime": "2024-01-01T00:00:00",
            "datasetJSONVersion": "1.1.0",
            "itemGroupOID": "IG.DM",
            "records": 50,
            "name": "DM",
            "label": "Demographics",
            "columns": [
                {"itemOID": "IT.X", "name": "X", "label": "Var X",
                 "dataType": "string"},
            ],
        }
        dsj = DatasetJSON.from_dict(data)
        self.assertEqual(dsj.records, 50)
        self.assertEqual(len(dsj.columns), 1)

    # --- Row data edge cases ---

    def test_null_values_in_rows(self):
        dsj = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.AE",
            records=2,
            name="AE",
            label="Adverse Events",
            columns=[
                Column(itemOID="IT.X", name="X", label="X",
                       dataType="string"),
                Column(itemOID="IT.Y", name="Y", label="Y",
                       dataType="integer"),
            ],
            rows=[
                ["val1", None],
                [None, 42],
            ],
        )
        d = dsj.to_dict()
        self.assertEqual(d["rows"][0], ["val1", None])
        self.assertEqual(d["rows"][1], [None, 42])
        # Round-trip preserves nulls
        dsj2 = DatasetJSON.from_json(dsj.to_json())
        self.assertEqual(dsj2.rows[0], ["val1", None])
        self.assertEqual(dsj2.rows[1], [None, 42])

    def test_mixed_types_in_rows(self):
        dsj = DatasetJSON(
            datasetJSONCreationDateTime="2024-01-01T00:00:00",
            datasetJSONVersion="1.1.0",
            itemGroupOID="IG.DM",
            records=1,
            name="DM",
            label="Demographics",
            columns=[
                Column(itemOID="IT.A", name="A", label="A",
                       dataType="string"),
                Column(itemOID="IT.B", name="B", label="B",
                       dataType="integer"),
                Column(itemOID="IT.C", name="C", label="C",
                       dataType="boolean"),
                Column(itemOID="IT.D", name="D", label="D",
                       dataType="float"),
            ],
            rows=[["text", 42, True, 3.14]],
        )
        d = dsj.to_dict()
        self.assertEqual(d["rows"][0], ["text", 42, True, 3.14])

    # --- Inherited ODMElement methods ---

    def test_find_column(self):
        dsj = self._make_full()
        found = dsj.find("columns", "name", "AGE")
        self.assertIsNotNone(found)
        self.assertEqual(found.itemOID, "IT.AGE")

    def test_find_column_not_found(self):
        dsj = self._make_full()
        found = dsj.find("columns", "name", "NONEXISTENT")
        self.assertIsNone(found)

    def test_find_all_columns(self):
        dsj = self._make_full()
        found = dsj.find_all("columns", "dataType", "string")
        self.assertEqual(len(found), 2)  # STUDYID and USUBJID

    def test_find_by_column(self):
        dsj = self._make_full()
        found = dsj.find_by("columns", dataType="integer", name="AGE")
        self.assertIsNotNone(found)
        self.assertEqual(found.itemOID, "IT.AGE")

    def test_repr(self):
        dsj = self._make_minimal()
        r = repr(dsj)
        self.assertIn("DatasetJSON", r)

    # --- Schema conformance spot checks ---

    def test_records_non_negative_integer(self):
        """records must be >= 0."""
        dsj = self._make_minimal()
        dsj.records = 0
        self.assertEqual(dsj.records, 0)
        dsj.records = 100
        self.assertEqual(dsj.records, 100)

    def test_records_string_coercion(self):
        """NonNegativeInteger accepts string and coerces to int."""
        dsj = self._make_minimal()
        dsj.records = "42"
        self.assertEqual(dsj.records, 42)

    def test_column_keysequence_positive(self):
        """keySequence must be >= 1."""
        col = Column(itemOID="IT.X", name="X", label="X",
                     dataType="string", keySequence=1)
        self.assertEqual(col.keySequence, 1)

    def test_from_dict_column_already_objects(self):
        """from_dict handles columns already being Column objects."""
        cols = [Column(itemOID="IT.X", name="X", label="X",
                       dataType="string")]
        data = {
            "datasetJSONCreationDateTime": "2024-01-01T00:00:00",
            "datasetJSONVersion": "1.1.0",
            "itemGroupOID": "IG.DM",
            "records": 0,
            "name": "DM",
            "label": "Demographics",
            "columns": cols,
        }
        dsj = DatasetJSON.from_dict(data)
        self.assertIsInstance(dsj.columns[0], Column)


class TestImport(unittest.TestCase):
    """Test package-level imports."""

    def test_import_from_package(self):
        from odmlib.dataset_json_1_1 import DatasetJSON, Column, SourceSystem
        self.assertTrue(hasattr(DatasetJSON, "from_json"))
        self.assertTrue(hasattr(Column, "to_dict"))
        self.assertTrue(hasattr(SourceSystem, "to_dict"))


if __name__ == "__main__":
    unittest.main()
