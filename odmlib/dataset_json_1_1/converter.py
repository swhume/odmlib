"""Converters between Dataset-XML 1.0.1 and Dataset-JSON v1.1.

Provides utilities to convert between odmlib Dataset-XML objects and
the ODMElement-based Dataset-JSON v1.1 model. Produces **one
DatasetJSON per ItemGroupOID** (one dataset per file), matching the
Dataset-JSON v1.1 specification.

Functions:
    :func:`dataset_xml_to_dataset_json` -- Dataset-XML → dict of DatasetJSON
    :func:`dataset_json_to_dataset_xml` -- DatasetJSON → Dataset-XML ODM object
"""
from __future__ import annotations

import datetime
import warnings
from typing import Any, Optional

from odmlib.dataset_json_1_1.model import DatasetJSON, Column


# ---------------------------------------------------------------------------
# Mapping from ODM DataType to Dataset-JSON type
# ---------------------------------------------------------------------------

_ODM_TO_DSJ_TYPE: dict[str, str] = {
    "text": "string",
    "string": "string",
    "integer": "integer",
    "float": "float",
    "double": "double",
    "decimal": "decimal",
    "date": "date",
    "time": "time",
    "datetime": "datetime",
    "boolean": "boolean",
    "URI": "URI",
    "partialDate": "string",
    "partialTime": "string",
    "partialDatetime": "string",
    "durationDatetime": "string",
    "intervalDatetime": "string",
    "incompleteDatetime": "string",
    "base64Binary": "string",
    "hexBinary": "string",
}


def dataset_xml_to_dataset_json(
    odm_obj: Any,
    define_mdv: Optional[Any] = None,
) -> dict[str, DatasetJSON]:
    """Convert a Dataset-XML 1.0.1 ODM object to Dataset-JSON v1.1.

    Produces **one DatasetJSON per ItemGroupOID**, matching the
    Dataset-JSON v1.1 specification (one dataset per file).

    Multiple ``ItemGroupData`` rows with the same ``ItemGroupOID`` are
    merged into one DatasetJSON. The column set is the union of all
    ``ItemOID`` values observed across all rows for that group.

    Args:
        odm_obj: An ODM root object from the ``dataset_1_0_1`` model.
        define_mdv: Optional ``MetaDataVersion`` from a loaded
            Define-XML document. When provided, column labels, types,
            and lengths are read from ItemDef elements.

    Returns:
        dict[str, DatasetJSON]: Mapping of dataset name to DatasetJSON.
            Dataset name is derived from the ItemGroupOID suffix
            (e.g., ``"IG.AE"`` → ``"AE"``).
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    clinical = getattr(odm_obj, "ClinicalData", None)
    if clinical is None:
        return {}

    study_oid = getattr(clinical, "StudyOID", None)
    mdv_oid = getattr(clinical, "MetaDataVersionOID", None)

    # Group ItemGroupData records by ItemGroupOID
    datasets_by_oid: dict[str, list[Any]] = {}
    for igd in (getattr(clinical, "ItemGroupData", None) or []):
        oid = igd.ItemGroupOID
        if oid not in datasets_by_oid:
            datasets_by_oid[oid] = []
        datasets_by_oid[oid].append(igd)

    result: dict[str, DatasetJSON] = {}
    for oid, igd_list in datasets_by_oid.items():
        # Collect the union of all ItemOIDs, preserving insertion order
        item_oids: list[str] = []
        seen: set[str] = set()
        for igd in igd_list:
            for item_data in (getattr(igd, "ItemData", None) or []):
                if item_data.ItemOID not in seen:
                    item_oids.append(item_data.ItemOID)
                    seen.add(item_data.ItemOID)

        # Build Column metadata
        columns = [_make_column(ioid, define_mdv) for ioid in item_oids]

        # Extract rows
        rows = []
        for igd in igd_list:
            rows.append(_extract_row_values(igd, item_oids))

        # Derive dataset name from OID
        ds_name = oid.split(".")[-1] if "." in oid else oid
        ds_label = _get_itemgroup_label(oid, define_mdv)

        ds = DatasetJSON(
            datasetJSONCreationDateTime=now,
            datasetJSONVersion="1.1.0",
            fileOID=getattr(odm_obj, "FileOID", None),
            originator=getattr(odm_obj, "Originator", None),
            studyOID=study_oid,
            metaDataVersionOID=mdv_oid,
            itemGroupOID=oid,
            records=len(rows),
            name=ds_name,
            label=ds_label or ds_name,
            columns=columns,
        )
        if rows:
            ds.rows = rows
        if ds_name in result:
            # two ItemGroupOIDs share a name suffix (e.g. "IG.AE" and
            # "SUPP.AE"); silently overwriting would lose a dataset, so the
            # colliding entry is stored under its full OID instead
            warnings.warn(
                f"Dataset name '{ds_name}' derived from ItemGroupOID '{oid}' "
                f"collides with an existing dataset; storing it under its "
                f"full OID key '{oid}' instead",
                stacklevel=2,
            )
            result[oid] = ds
        else:
            result[ds_name] = ds

    return result


def dataset_json_to_dataset_xml(
    dataset_json: DatasetJSON,
    dataset_xml_model: Any,
    study_oid: Optional[str] = None,
    mdv_oid: Optional[str] = None,
) -> Any:
    """Convert a Dataset-JSON v1.1 DatasetJSON to a Dataset-XML ODM object.

    Args:
        dataset_json: A :class:`~odmlib.dataset_json_1_1.model.DatasetJSON`.
        dataset_xml_model: The ``odmlib.dataset_1_0_1.model`` module
            containing ``ODM``, ``ClinicalData``, ``ItemGroupData``,
            and ``ItemData`` classes.
        study_oid: Study OID override. If None, uses
            ``dataset_json.studyOID``.
        mdv_oid: MetaDataVersion OID override. If None, uses
            ``dataset_json.metaDataVersionOID``.

    Returns:
        An odmlib ODM root object with ClinicalData.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    odm = dataset_xml_model.ODM(
        FileOID=dataset_json.fileOID or "FILE.001",
        FileType="Snapshot",
        CreationDateTime=dataset_json.datasetJSONCreationDateTime or now,
        DatasetXMLVersion="1.0.1",
    )

    s_oid = study_oid or dataset_json.studyOID or "STUDY.001"
    m_oid = mdv_oid or dataset_json.metaDataVersionOID or "MDV.001"

    clinical = dataset_xml_model.ClinicalData(
        StudyOID=s_oid,
        MetaDataVersionOID=m_oid,
    )
    odm.ClinicalData = clinical

    col_names = dataset_json.column_names
    col_oids = [col.itemOID for col in dataset_json.columns]
    rows = dataset_json.rows if dataset_json.rows else []

    for seq, row in enumerate(rows, start=1):
        igd = dataset_xml_model.ItemGroupData(
            ItemGroupOID=dataset_json.itemGroupOID,
            ItemGroupDataSeq=str(seq),
        )
        for col_oid, value in zip(col_oids, row):
            if value is not None:
                igd.ItemData.append(
                    dataset_xml_model.ItemData(
                        ItemOID=col_oid,
                        Value=str(value),
                    )
                )
        clinical.ItemGroupData.append(igd)

    return odm


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_column(item_oid: str, define_mdv: Optional[Any]) -> Column:
    """Create a Column for an ItemOID, enriched from Define-XML if available."""
    if define_mdv is not None:
        item_defs = getattr(define_mdv, "ItemDef", None) or []
        for item_def in item_defs:
            if getattr(item_def, "OID", None) == item_oid:
                kwargs: dict[str, Any] = {
                    "itemOID": item_oid,
                    "name": getattr(item_def, "Name", item_oid),
                    "label": _get_description_text(item_def),
                    "dataType": _map_data_type(
                        getattr(item_def, "DataType", "string")
                    ),
                }
                length = getattr(item_def, "Length", None)
                if length is not None:
                    kwargs["length"] = length
                display_fmt = getattr(item_def, "DisplayFormat", None)
                if display_fmt is not None:
                    kwargs["displayFormat"] = display_fmt
                return Column(**kwargs)

    # Fallback: minimal metadata derived from the OID
    name = item_oid.split(".")[-1] if "." in item_oid else item_oid
    return Column(itemOID=item_oid, name=name, label=name, dataType="string")


def _get_itemgroup_label(item_group_oid: str, define_mdv: Optional[Any]) -> str:
    """Return the label for an ItemGroupDef from Define-XML, or empty string."""
    if define_mdv is None:
        return ""
    ig_defs = getattr(define_mdv, "ItemGroupDef", None) or []
    for ig_def in ig_defs:
        if getattr(ig_def, "OID", None) == item_group_oid:
            return _get_description_text(ig_def)
    return ""


def _get_description_text(element: Any) -> str:
    """Extract description text from an odmlib element's Description child."""
    desc = getattr(element, "Description", None)
    if desc is not None and hasattr(desc, "TranslatedText"):
        tt_list = desc.TranslatedText
        if tt_list:
            return getattr(tt_list[0], "_content", "") or ""
    return ""


def _map_data_type(odm_type: str) -> str:
    """Map an ODM DataType string to a Dataset-JSON type string."""
    return _ODM_TO_DSJ_TYPE.get(odm_type, "string")


def _extract_row_values(igd: Any, item_oids: list[str]) -> list[Any]:
    """Extract an ordered list of values from an ItemGroupData row."""
    oid_to_value: dict[str, Any] = {}
    for item_data in (getattr(igd, "ItemData", None) or []):
        oid_to_value[item_data.ItemOID] = getattr(item_data, "Value", None)
    return [oid_to_value.get(oid) for oid in item_oids]
