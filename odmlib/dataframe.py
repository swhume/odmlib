"""Optional Pandas DataFrame integration for odmlib.

Provides convenience functions to export odmlib metadata and clinical data
to Pandas DataFrames and to construct odmlib element lists from DataFrames.

Pandas is an **optional** dependency.  If it is not installed, importing
this module succeeds but calling any function raises :class:`ImportError`
with a helpful install hint.

Install with::

    pip install odmlib[dataframe]

or::

    pip install pandas

Functions
---------
:func:`metadata_to_dataframe`
    Export a list of odmlib metadata elements (e.g., all ItemDef objects in
    a MetaDataVersion) as a DataFrame with one row per element.

:func:`clinical_data_to_dataframe`
    Flatten a hierarchical ODM 1.3.2 or ODM 2.0 ClinicalData object into a
    tabular DataFrame with one row per record of one item group.

:func:`dataset_to_dataframe`
    Flatten a Dataset-XML 1.0.1 ClinicalData object (no SubjectData
    hierarchy) into a tabular DataFrame with one row per ItemGroupData record.

:func:`dataset_json_to_dataframe`
    Convert a :class:`~odmlib.dataset_json_1_1.model.DatasetJSON` object
    to a DataFrame.

:func:`define_metadata_to_dataframes`
    Flatten all Define-XML v2.1 metadata into a dict of DataFrames, one
    per metadata table (study, datasets, variables, codelists, etc.).

:func:`dataframe_to_items`
    Create odmlib element instances from a DataFrame (one row → one element).

Example::

    import odmlib.odm_1_3_2.model as ODM
    import odmlib.loader as LD
    import odmlib.odm_loader as OL
    from odmlib.dataframe import metadata_to_dataframe

    loader = LD.ODMLoader(OL.XMLODMLoader())
    loader.open_odm_document("study.xml")
    mdv = loader.MetaDataVersion()

    df = metadata_to_dataframe(mdv, "ItemDef")
    print(df[["OID", "Name", "DataType"]].to_string())
"""
from __future__ import annotations
import warnings
from typing import Any, Optional

from odmlib.exceptions import OdmlibError

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def _require_pandas() -> None:
    """Raise ImportError if pandas is not installed."""
    if not HAS_PANDAS:
        raise ImportError(
            "pandas is required for DataFrame integration.\n"
            "Install it with:  pip install odmlib[dataframe]\n"
            "or:               pip install pandas"
        )


def metadata_to_dataframe(
    mdv: Any,
    element_type: str,
    attributes: Optional[list[str]] = None,
) -> "pd.DataFrame":
    """Export odmlib metadata elements to a Pandas DataFrame.

    Extracts all elements of *element_type* from a ``MetaDataVersion`` and
    returns a DataFrame with one row per element.  Only scalar attributes
    (``str``, ``int``, ``float``, ``bool``, ``None``) are included as
    columns; child element lists and nested objects are excluded.

    Args:
        mdv: A ``MetaDataVersion`` odmlib object (ODM 1.3.2,
            Define-XML 2.0, or Define-XML 2.1).
        element_type: Name of the element list to export.  Examples:
            ``"ItemDef"``, ``"ItemGroupDef"``, ``"CodeList"``,
            ``"StudyEventDef"``, ``"FormDef"``.
        attributes: Optional list of attribute names to include as columns.
            If ``None``, all scalar attributes found on any element are
            included (union across all elements).

    Returns:
        A :class:`pandas.DataFrame` with one row per element and one
        column per scalar attribute.

    Raises:
        ImportError: If pandas is not installed.

    Example::

        df = metadata_to_dataframe(mdv, "ItemDef")
        print(df[["OID", "Name", "DataType"]].head())
    """
    _require_pandas()

    elements = getattr(mdv, element_type, [])
    if not isinstance(elements, list):
        elements = [elements] if elements is not None else []

    rows = []
    for elem in elements:
        row: dict[str, Any] = {}
        elem_dict = {k: v for k, v in elem.__dict__.items() if not k.startswith("_")}
        for attr_name, attr_val in elem_dict.items():
            if attributes is not None and attr_name not in attributes:
                continue
            # Include only scalar values; exclude child elements (lists, objects)
            if isinstance(attr_val, (str, int, float, bool, type(None))):
                row[attr_name] = attr_val
        rows.append(row)

    return pd.DataFrame(rows)


def clinical_data_to_dataframe(
    clinical_data: Any,
    item_group_oid: str,
) -> "pd.DataFrame":
    """Export the clinical data of one ItemGroup to a DataFrame.

    Collects one row per ``ItemGroupData`` whose ``ItemGroupOID`` is
    *item_group_oid*, with a ``"SubjectKey"`` column plus one column per
    ``ItemOID`` found in those records. The walk depends on the model:

    * **ODM 1.3.2:** ``SubjectData → StudyEventData → FormData → ItemGroupData
      → ItemData``. A value is the ``ItemData/@Value`` attribute.
    * **ODM 2.0:** ItemGroupData at the ClinicalData level (its ``SubjectKey`` is
      ``None``) and under ``SubjectData → StudyEventData``, recursing into
      nested ItemGroupData. Each matching group, nested or not, is one row of
      its own ItemData. A value comes from the ``Value`` child elements: one
      Value gives a scalar, several give a list ordered by ``SeqNum``, and an
      ItemData with ``IsNull="Yes"`` (or no Value) gives ``None``.

    The walk reads the tree without changing it.

    Args:
        clinical_data: A ``ClinicalData`` odmlib object from the ``odm_1_3_2``
            or ``odm_2_0`` model.
        item_group_oid: OID of the ``ItemGroupDef`` to extract (e.g.,
            ``"IG.VS"``).

    Returns:
        A :class:`pandas.DataFrame` with one row per matching record.

    Raises:
        ImportError: If pandas is not installed.

    .. versionchanged:: 0.3.0
       Supports ODM 2.0. It returned an empty DataFrame for ODM 2.0, with no
       error, because it looked for FormData.
    """
    _require_pandas()

    if _is_odm20_clinical_data(clinical_data):
        return pd.DataFrame(_odm20_rows(clinical_data, item_group_oid))

    rows = []
    for subject in _children(clinical_data, "SubjectData"):
        for se_data in _children(subject, "StudyEventData"):
            for form_data in _children(se_data, "FormData"):
                for ig_data in _children(form_data, "ItemGroupData"):
                    if getattr(ig_data, "ItemGroupOID", None) == item_group_oid:
                        row: dict[str, Any] = {
                            "SubjectKey": getattr(subject, "SubjectKey", None)
                        }
                        for item_data in _children(ig_data, "ItemData"):
                            row[item_data.ItemOID] = getattr(item_data, "Value", None)
                        rows.append(row)

    return pd.DataFrame(rows)


def _children(elem: Any, name: str) -> list:
    """The child list *name* of *elem*, read without auto-creating an empty one."""
    return getattr(elem, "__dict__", {}).get(name) or []


def _is_odm20_clinical_data(clinical_data: Any) -> bool:
    """ODM 2.0 ClinicalData holds SubjectData and ItemGroupData; 1.3.2 has no ItemGroupData."""
    elems = getattr(type(clinical_data), "_elems", {})
    return "SubjectData" in elems and "ItemGroupData" in elems


def _odm20_value(item_data: Any) -> Any:
    """The value of an ODM 2.0 ItemData: a scalar, a list ordered by SeqNum, or None."""
    if getattr(item_data, "IsNull", None) == "Yes":
        return None
    values = sorted(_children(item_data, "Value"),
                    key=lambda v: (v.SeqNum is None, v.SeqNum or 0))
    if not values:
        return None
    if len(values) == 1:
        return values[0]._content
    return [v._content for v in values]


def _odm20_rows(clinical_data: Any, item_group_oid: str) -> list[dict[str, Any]]:
    """One row per ODM 2.0 ItemGroupData matching *item_group_oid*, at any depth."""
    rows: list[dict[str, Any]] = []

    def walk(groups: list, subject_key: Optional[str]) -> None:
        for ig_data in groups:
            if getattr(ig_data, "ItemGroupOID", None) == item_group_oid:
                row: dict[str, Any] = {"SubjectKey": subject_key}
                for item_data in _children(ig_data, "ItemData"):
                    row[item_data.ItemOID] = _odm20_value(item_data)
                rows.append(row)
            walk(_children(ig_data, "ItemGroupData"), subject_key)

    walk(_children(clinical_data, "ItemGroupData"), None)
    for subject in _children(clinical_data, "SubjectData"):
        for se_data in _children(subject, "StudyEventData"):
            walk(_children(se_data, "ItemGroupData"), getattr(subject, "SubjectKey", None))
    return rows


def dataset_to_dataframe(clinical_data: Any) -> "pd.DataFrame":
    """Export Dataset-XML 1.0.1 ClinicalData to a Pandas DataFrame.

    For the simpler Dataset-XML 1.0.1 structure, which does not have the
    ``SubjectData`` hierarchy.  Each ``ItemGroupData`` row becomes one
    row in the DataFrame.

    Args:
        clinical_data: A ``ClinicalData`` odmlib object from the
            ``dataset_1_0_1`` model.

    Returns:
        A :class:`pandas.DataFrame` with one row per ``ItemGroupData``
        record.  Columns include ``"ItemGroupOID"``, ``"ItemGroupDataSeq"``,
        and one column per ``ItemOID`` found in any record.

    Raises:
        ImportError: If pandas is not installed.
    """
    _require_pandas()

    rows = []
    for ig_data in (getattr(clinical_data, "ItemGroupData", None) or []):
        row: dict[str, Any] = {
            "ItemGroupOID": getattr(ig_data, "ItemGroupOID", None),
            "ItemGroupDataSeq": getattr(ig_data, "ItemGroupDataSeq", None),
        }
        for item_data in (getattr(ig_data, "ItemData", None) or []):
            row[item_data.ItemOID] = getattr(item_data, "Value", None)
        rows.append(row)

    return pd.DataFrame(rows)


def dataset_json_to_dataframe(dataset: Any) -> "pd.DataFrame":
    """Convert a Dataset-JSON v1.1 dataset object to a Pandas DataFrame.

    Column names come from the :attr:`DatasetJSON.column_names` property
    and row data from :attr:`DatasetJSON.rows` (list of lists).

    Args:
        dataset: An :class:`odmlib.dataset_json_1_1.model.DatasetJSON` object.

    Returns:
        A :class:`pandas.DataFrame` with one row per record and columns
        named by variable name.

    Raises:
        ImportError: If pandas is not installed.

    Example::

        from odmlib.dataset_json_1_1 import DatasetJSON
        from odmlib.dataframe import dataset_json_to_dataframe

        ds = DatasetJSON.read_json("ae.json")
        df = dataset_json_to_dataframe(ds)
        print(df.head())
    """
    _require_pandas()

    col_names = dataset.column_names
    rows = dataset.rows if dataset.rows else []
    return pd.DataFrame(rows, columns=col_names)


def define_metadata_to_dataframes(
    odm_root: Any,
    study_idx: int = 0,
) -> "dict[str, pd.DataFrame]":
    """Flatten Define-XML v2.1 metadata into a dict of Pandas DataFrames.

    Uses :class:`~odmlib.dataset_json_1_1.define_flattener.DefineFlattener`
    internally to convert a loaded Define-XML v2.1 ODM root object into
    tabular Dataset-JSON datasets, then converts each to a DataFrame.

    The returned dict maps dataset names to DataFrames.  Dataset names
    are: ``study``, ``standards``, ``datasets``, ``variables``,
    ``value_level``, ``where_clauses``, ``methods``, ``comments``,
    ``documents``, ``codelists``, ``codelist_terms``.

    Args:
        odm_root: A loaded Define-XML v2.1 ODM root object (from odmlib
            loader).
        study_idx: Index of the Study element to use (default: 0).

    Returns:
        dict[str, pandas.DataFrame]: Mapping of dataset name to DataFrame.

    Raises:
        ImportError: If pandas is not installed.

    Example::

        import odmlib.define_loader as DL
        import odmlib.loader as LD
        from odmlib.dataframe import define_metadata_to_dataframes

        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1'))
        loader.open_odm_document('define.xml')
        odm = loader.root()

        dfs = define_metadata_to_dataframes(odm)
        print(dfs['variables'][['DatasetOID', 'Name', 'DataType']].head())
    """
    _require_pandas()

    from odmlib.dataset_json_1_1.define_flattener import DefineFlattener

    flattener = DefineFlattener(odm_root, study_idx=study_idx)
    datasets = flattener.flatten_all()

    result = {}
    for name, ds in datasets.items():
        col_names = ds.column_names
        rows = ds.rows if ds.rows else []
        result[name] = pd.DataFrame(rows, columns=col_names)

    return result


def dataframe_to_dataset_json(
    df: "pd.DataFrame",
    name: str,
    label: str,
    item_group_oid: str,
    dataset_json_version: str = "1.1.0",
    creation_datetime: Optional[str] = None,
) -> Any:
    """Convert a Pandas DataFrame to a Dataset-JSON v1.1 DatasetJSON object.

    Each DataFrame column becomes a Dataset-JSON Column with ``dataType``
    inferred from the pandas dtype (int → ``"integer"``, float →
    ``"decimal"``, otherwise ``"string"``).

    Args:
        df: Source DataFrame.
        name: Dataset name (e.g., ``"DM"``, ``"AE"``).
        label: Dataset label/description.
        item_group_oid: ItemGroupDef OID for this dataset.
        dataset_json_version: Dataset-JSON version string (default:
            ``"1.1.0"``).
        creation_datetime: ISO 8601 creation timestamp.  If ``None``,
            the current UTC time is used.

    Returns:
        A :class:`~odmlib.dataset_json_1_1.model.DatasetJSON` instance.

    Raises:
        ImportError: If pandas is not installed.

    Example::

        import pandas as pd
        from odmlib.dataframe import dataframe_to_dataset_json

        df = pd.DataFrame({
            "STUDYID": ["CDISC01", "CDISC01"],
            "USUBJID": ["001", "002"],
            "AGE": [65, 72],
        })
        ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
        ds.write_json("dm.json")
    """
    _require_pandas()

    import datetime as dt
    from odmlib.dataset_json_1_1.model import DatasetJSON, Column

    if creation_datetime is None:
        creation_datetime = dt.datetime.now(dt.timezone.utc).isoformat()

    # Build columns from DataFrame dtypes
    columns = []
    for col_name in df.columns:
        dtype = df[col_name].dtype
        if pd.api.types.is_integer_dtype(dtype):
            data_type = "integer"
        elif pd.api.types.is_float_dtype(dtype):
            data_type = "decimal"
        elif pd.api.types.is_bool_dtype(dtype):
            data_type = "boolean"
        else:
            data_type = "string"

        columns.append(Column(
            itemOID=f"IT.{name}.{col_name}",
            name=col_name,
            label=col_name,
            dataType=data_type,
        ))

    # Build rows, converting NaN to None (itertuples is much faster than iterrows)
    rows = []
    for row in df.itertuples(index=False, name=None):
        row_values = []
        for val in row:
            try:
                if pd.isna(val):
                    row_values.append(None)
                else:
                    # Convert numpy types to native Python types
                    if hasattr(val, "item"):
                        row_values.append(val.item())
                    else:
                        row_values.append(val)
            except (TypeError, ValueError):
                if hasattr(val, "item"):
                    row_values.append(val.item())
                else:
                    row_values.append(val)
        rows.append(row_values)

    ds = DatasetJSON(
        datasetJSONCreationDateTime=creation_datetime,
        datasetJSONVersion=dataset_json_version,
        itemGroupOID=item_group_oid,
        records=len(rows),
        name=name,
        label=label,
        columns=columns,
    )
    if rows:
        ds.rows = rows

    return ds


def dataframe_to_items(
    df: "pd.DataFrame",
    model_module: Any,
    element_type: str = "ItemDef",
    column_mapping: Optional[dict[str, str]] = None,
) -> list[Any]:
    """Create odmlib elements from a Pandas DataFrame.

    Each row of the DataFrame becomes one odmlib element instance of type
    *element_type*.  Columns that map to valid attribute names are passed
    as keyword arguments to the constructor.  Rows that fail to construct
    a valid element are silently skipped.

    Args:
        df: Source DataFrame where each row represents one element.
        model_module: The odmlib model module containing *element_type*
            (e.g., ``odmlib.odm_1_3_2.model``).
        element_type: Class name to instantiate (default ``"ItemDef"``).
        column_mapping: Optional dict mapping DataFrame column names to
            odmlib attribute names.  If ``None``, column names must match
            attribute names exactly.

    Returns:
        List of odmlib element instances (one per successfully constructed row).

    Raises:
        ImportError: If pandas is not installed.
        AttributeError: If *element_type* is not found in *model_module*.

    Example::

        import odmlib.odm_1_3_2.model as ODM
        import pandas as pd
        from odmlib.dataframe import dataframe_to_items

        df = pd.DataFrame([
            {"OID": "IT.AGE", "Name": "AGE", "DataType": "integer"},
            {"OID": "IT.SEX", "Name": "SEX", "DataType": "text"},
        ])
        items = dataframe_to_items(df, ODM, "ItemDef")
        for item in items:
            mdv.ItemDef.append(item)
    """
    _require_pandas()

    cls = getattr(model_module, element_type)
    mapping = column_mapping or {}

    elements: list[Any] = []
    # to_dict("records") avoids iterrows' per-row Series construction and
    # its dtype promotion (values keep their native per-cell types)
    for row_idx, record in enumerate(df.to_dict(orient="records")):
        kwargs: dict[str, Any] = {}
        for col in df.columns:
            attr_name = mapping.get(col, col)
            val = record[col]
            # Skip NaN / None / pd.NA values
            try:
                if pd.notna(val):
                    kwargs[attr_name] = val
            except (TypeError, ValueError):
                # notna() may raise for certain object types; skip gracefully
                if val is not None:
                    kwargs[attr_name] = val
        try:
            elements.append(cls(**kwargs))
        except (OdmlibError, AttributeError) as ex:
            # skipped rows must be visible: silent drops made the returned
            # list shorter than the DataFrame with no signal to the caller
            warnings.warn(
                f"Skipping DataFrame row {row_idx} — could not construct "
                f"{element_type}: {ex}",
                stacklevel=2,
            )

    return elements
