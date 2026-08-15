"""Dataset-JSON v1.1 model using the ODMElement/descriptor pattern.

This module defines ODMElement-based classes conforming to the CDISC
Dataset-JSON v1.1 specification. The model represents one dataset per file
with column-oriented metadata and row data as arrays of arrays.

Classes:
    :class:`DatasetJSONElement` -- base class disabling XML serialization
    :class:`SourceSystem` -- optional source system metadata object
    :class:`Column` -- column (variable) metadata
    :class:`DatasetJSON` -- root element for a Dataset-JSON v1.1 file

Reference:
    CDISC Dataset-JSON v1.1 specification and JSON schema.
"""
from __future__ import annotations

import json
from typing import Any, Optional, List

import odmlib.odm_element as OE
import odmlib.typed as T


class DatasetJSONElement(OE.ODMElement):
    """Base class for Dataset-JSON v1.1 elements.

    Overrides XML serialization (not applicable for Dataset-JSON) and
    provides a ``to_dict()`` that handles mixed list types (ODMElement
    lists and plain data arrays) and omits None-valued optional fields.
    """

    namespace = "dsjson"

    def to_xml(self, parent_elem=None, top_elem=None):
        """Dataset-JSON does not support XML serialization.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Dataset-JSON does not support XML serialization")

    def to_xml_string(self, *, xml_declaration=False):
        """Dataset-JSON does not support XML serialization.

        Accepts the same keyword as :meth:`ODMElement.to_xml_string` so that
        ``to_xml_string(xml_declaration=True)`` raises the intended
        NotImplementedError rather than a TypeError.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Dataset-JSON does not support XML serialization")

    def write_xml(self, odm_file, odm_writer=None):
        """Dataset-JSON does not support XML serialization.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("Dataset-JSON does not support XML serialization")

    def to_dict(self) -> dict:
        """Serialize this element to a Python dictionary.

        Handles mixed list types: lists of ODMElement children are
        recursively serialized via ``to_dict()``, while plain data
        lists (e.g., rows) pass through unchanged. None-valued
        optional fields are omitted.

        Returns:
            dict: Spec-conformant dictionary representation.
        """
        d = {}
        for attr, obj in self.__dict__.items():
            if attr.startswith("_"):
                continue
            if obj is None:
                continue
            if isinstance(obj, OE.ODMElement):
                d[attr] = obj.to_dict()
            elif isinstance(obj, list):
                if not obj:
                    d[attr] = obj
                elif isinstance(obj[0], OE.ODMElement):
                    d[attr] = [o.to_dict() for o in obj]
                else:
                    d[attr] = obj
            else:
                d[attr] = obj
        return d

    def _init_oid_index(self, idx):
        """Override to safely handle non-ODMElement lists (e.g., rows)."""
        for attr, obj in self.__dict__.items():
            if attr.startswith("_"):
                continue
            if isinstance(obj, OE.ODMElement):
                obj._init_oid_index(idx)
            elif isinstance(obj, list):
                for o in obj:
                    if isinstance(o, OE.ODMElement):
                        o._init_oid_index(idx)
            elif attr == "OID" or (isinstance(obj, str) and "OID" in attr):
                idx.add_oid(obj, self)

    def _init_oid_check(self, oid_checker):
        """Override to safely handle non-ODMElement lists (e.g., rows)."""
        for attr, obj in self.__dict__.items():
            if attr.startswith("_"):
                continue
            if isinstance(obj, OE.ODMElement):
                obj._init_oid_check(oid_checker)
            elif isinstance(obj, list):
                for o in obj:
                    if isinstance(o, OE.ODMElement):
                        o._init_oid_check(oid_checker)
            else:
                if attr == "OID":
                    oid_checker.add_oid(obj, self.__class__.__name__)
                elif isinstance(obj, str) and "OID" in attr:
                    oid_checker.add_oid_ref(obj, attr)


class SourceSystem(DatasetJSONElement):
    """Source system information (optional nested object in Dataset-JSON v1.1).

    Attributes:
        name (str, required): The name of the source system.
        version (str, required): The version of the source system.
    """

    name = T.String(required=True)
    version = T.String(required=True)


class Column(DatasetJSONElement):
    """Column (variable) metadata for a Dataset-JSON v1.1 dataset.

    Each column describes one variable in the dataset, including its
    OID, name, label, data type, and optional formatting information.

    Attributes:
        itemOID (str, required): Variable OID (corresponds to ItemDef.OID
            in Define-XML).
        name (str, required): Variable name (e.g., "STUDYID", "AETERM").
        label (str, required): Human-readable variable description.
        dataType (str, required): Logical data type. One of: "string",
            "integer", "decimal", "float", "double", "boolean",
            "datetime", "date", "time", "URI".
        targetDataType (str): Target data type for type conversion.
            Only "integer" or "decimal" are valid.
        length (int): Maximum variable length (must be >= 1).
        displayFormat (str): SAS-style display format (e.g., "DATE9.").
        keySequence (int): Key variable ordering (must be >= 1).
    """

    itemOID = T.String(required=True)
    name = T.Name(required=True)
    label = T.String(required=True)
    dataType = T.ExtendedValidValues(required=True, valid_values=[
        "string", "integer", "decimal", "float", "double",
        "boolean", "datetime", "date", "time", "URI"
    ])
    targetDataType = T.ExtendedValidValues(valid_values=["integer", "decimal"])
    length = T.PositiveInteger()
    displayFormat = T.String()
    keySequence = T.PositiveInteger()


class DatasetJSON(DatasetJSONElement):
    """Root element for a Dataset-JSON v1.1 file.

    Represents a single dataset (one per file) conforming to the CDISC
    Dataset-JSON v1.1 specification. Contains file-level metadata,
    column definitions, and row data.

    Attributes:
        datasetJSONCreationDateTime (str, required): ISO 8601 creation
            timestamp.
        datasetJSONVersion (str, required): Specification version
            (pattern: ``1.1(.N)?``).
        fileOID (str): Unique file identifier.
        dbLastModifiedDateTime (str): ISO 8601 timestamp of last database
            modification.
        originator (str): Organization that generated the file.
        sourceSystem (SourceSystem): Source system information object.
        studyOID (str): Study OID (foreign key to ODM Study).
        metaDataVersionOID (str): MetaDataVersion OID (foreign key to ODM).
        metaDataRef (str): URI to metadata file (e.g., Define-XML).
        itemGroupOID (str, required): ItemGroupDef OID (foreign key to
            Define-XML).
        records (int, required): Total number of records (>= 0).
        name (str, required): Dataset name (e.g., "DM", "AE").
        label (str, required): Dataset description.
        columns (list[Column]): Column metadata definitions.
        rows (list): Array of row arrays. Each row is a list of values
            matching the column order. None indicates missing values.
    """

    # Required fields (in spec-recommended order)
    datasetJSONCreationDateTime = T.String(required=True)
    datasetJSONVersion = T.String(required=True)
    # Optional file-level fields
    fileOID = T.String()
    dbLastModifiedDateTime = T.String()
    originator = T.String()
    sourceSystem = T.ODMObject(element_class=SourceSystem)
    # Optional study-level fields
    studyOID = T.String()
    metaDataVersionOID = T.String()
    metaDataRef = T.String()
    # Required dataset fields
    itemGroupOID = T.String(required=True)
    records = T.NonNegativeInteger(required=True)
    name = T.Name(required=True)
    label = T.String(required=True)
    columns = T.ODMListObject(element_class=Column)
    # Data (optional — allows metadata-only files with records=0)
    rows = T.List()

    def __init__(self, **kwargs):
        """Initialize a DatasetJSON instance.

        Ensures ``columns`` is always initialized (defaults to ``[]``)
        since it is required by the Dataset-JSON v1.1 schema.
        """
        if "columns" not in kwargs:
            kwargs["columns"] = []
        super().__init__(**kwargs)

    @property
    def column_names(self) -> list:
        """Return the list of column variable names.

        Returns:
            list[str]: Variable names from each Column's ``name`` attribute.
        """
        return [col.name for col in self.columns]

    def add_column(self, column: Column) -> None:
        """Append a Column to this dataset's column list.

        Args:
            column (Column): Column metadata to add.

        Raises:
            OdmlibTypeError: If ``column`` is not a Column instance.
        """
        self.columns.append(column)

    def add_row(self, values: list) -> None:
        """Append a row of values to this dataset.

        Validates that the number of values matches the number of columns.
        Automatically increments the ``records`` count.

        Args:
            values (list): List of values in column order. Use None for
                missing values.

        Raises:
            ValueError: If ``len(values)`` does not match ``len(columns)``.
        """
        if self.__dict__.get("rows") is None:
            self.rows = []
        n_cols = len(self.columns)
        if len(values) != n_cols:
            raise ValueError(
                f"Row has {len(values)} values but dataset has {n_cols} columns"
            )
        self.rows.append(values)
        self.records = len(self.rows)

    def to_dict(self) -> dict:
        """Serialize to a spec-conformant Dataset-JSON v1.1 dictionary.

        Omits empty ``rows`` for metadata-only mode (records > 0 but no
        row data transferred). All other behavior inherited from
        :meth:`DatasetJSONElement.to_dict`.

        Returns:
            dict: Dataset-JSON v1.1 conformant dictionary.
        """
        d = super().to_dict()
        # Omit empty rows (metadata-only mode)
        if "rows" in d and not d["rows"]:
            del d["rows"]
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string.

        Args:
            indent (int): JSON indentation level (default: 2).

        Returns:
            str: JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)

    def write_json(self, filename: str, indent: int = 2) -> None:
        """Write this dataset to a JSON file.

        Args:
            filename (str): Output file path.
            indent (int): JSON indentation level (default: 2).
        """
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=indent)

    def write_ndjson(self, filename: str) -> None:
        """Write this dataset to an NDJSON file.

        NDJSON format: line 1 is the metadata (everything except rows),
        lines 2+ are one row array per line.

        Args:
            filename (str): Output file path.
        """
        d = self.to_dict()
        rows = d.pop("rows", [])
        with open(filename, "w") as f:
            f.write(json.dumps(d) + "\n")
            for row in rows:
                f.write(json.dumps(row) + "\n")

    @classmethod
    def from_dict(cls, data: dict) -> DatasetJSON:
        """Construct a DatasetJSON from a dictionary.

        Handles nested construction of Column and SourceSystem objects
        from their dict representations.

        Args:
            data (dict): Dictionary with Dataset-JSON v1.1 fields.

        Returns:
            DatasetJSON: Constructed instance.
        """
        kwargs = {}
        for key, value in data.items():
            if key == "columns" and isinstance(value, list):
                kwargs["columns"] = [
                    Column(**col) if isinstance(col, dict) else col
                    for col in value
                ]
            elif key == "sourceSystem" and isinstance(value, dict):
                kwargs["sourceSystem"] = SourceSystem(**value)
            else:
                kwargs[key] = value
        return cls(**kwargs)

    @classmethod
    def from_json(cls, json_string: str) -> DatasetJSON:
        """Construct a DatasetJSON from a JSON string.

        Args:
            json_string (str): JSON string with Dataset-JSON v1.1 fields.

        Returns:
            DatasetJSON: Constructed instance.
        """
        return cls.from_dict(json.loads(json_string))

    @classmethod
    def read_json(cls, filename: str) -> DatasetJSON:
        """Read a DatasetJSON from a JSON file.

        Args:
            filename (str): Input file path.

        Returns:
            DatasetJSON: Constructed instance.
        """
        with open(filename, "r") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def read_ndjson(cls, filename: str) -> DatasetJSON:
        """Read a DatasetJSON from an NDJSON file.

        NDJSON format: line 1 is the metadata (everything except rows),
        lines 2+ are one row array per line.

        Args:
            filename (str): Input file path.

        Returns:
            DatasetJSON: Constructed instance.
        """
        with open(filename, "r") as f:
            lines = f.readlines()
        if not lines:
            raise ValueError("Empty NDJSON file")
        metadata = json.loads(lines[0])
        rows = [json.loads(line) for line in lines[1:] if line.strip()]
        if rows:
            metadata["rows"] = rows
            if "records" not in metadata:
                metadata["records"] = len(rows)
        return cls.from_dict(metadata)
