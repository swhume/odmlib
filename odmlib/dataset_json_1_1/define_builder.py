"""Reconstruct Define-XML v2.1 from flattened Dataset-JSON v1.1 datasets.

This module is the inverse of :mod:`~odmlib.dataset_json_1_1.define_flattener`.
It takes the 11 tabular Dataset-JSON datasets produced by
:class:`DefineFlattener` and reconstructs a full odmlib Define-XML v2.1
object tree that can be written to XML.

Classes:
    :class:`DefineBuilder` -- reconstructs Define-XML v2.1 from Dataset-JSON tables

Target datasets consumed (11 total):
    study, standards, datasets, variables, value_level, where_clauses,
    methods, comments, documents, codelists, codelist_terms
"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Optional

import odmlib.define_2_1.model as DEF
from odmlib import mode as _mode
from odmlib.dataset_json_1_1.model import DatasetJSON
from odmlib.exceptions import OdmlibTypeError, OdmlibValidationError
from odmlib.typed import _XS_INTEGER_PAT, _xsd_collapse


# ------------------------------------------------------------------ #
# Helper utilities
# ------------------------------------------------------------------ #

def _optional(kwargs: dict, key: str, value: Any):
    """Add *key* to *kwargs* only if *value* is not None."""
    if value is not None:
        kwargs[key] = value


def _split_ids(value: Optional[str]) -> list[str]:
    """Split a comma-joined string into a list, handling None/empty."""
    if not value:
        return []
    return [v.strip() for v in value.split(",")]


def _int_or_none(value: Any, field_name: Optional[str] = None) -> Optional[int]:
    """Convert to int, handling None and float-from-JSON.

    JSON often delivers an integer as a float (``8.0``), which is converted. A
    float with a fractional part (``3.7``) raises :exc:`OdmlibValidationError`
    rather than being truncated, and a string must be an ``xs:integer`` (as
    :class:`~odmlib.typed.Integer` requires). Anything else that is not an int,
    including ``bool``, raises :exc:`OdmlibTypeError`.

    Under ``ValidationMode.SKIP_TYPE`` (permissive), returns the raw value
    unchanged when conversion fails so the descriptor can store it as-is.

    .. versionchanged:: 0.3.0
       A non-integral float was silently truncated (``3.7`` became ``3``).
    """
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and _XS_INTEGER_PAT.fullmatch(_xsd_collapse(value)):
        try:
            return int(_xsd_collapse(value))
        except ValueError:       # more digits than int() will convert
            pass
    if _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
        return value
    if isinstance(value, float):
        raise OdmlibValidationError(
            f"Expected integer for {field_name or 'attribute'}, found {value!r}",
            attribute=field_name,
            actual_value=value,
            hint="The value has a fractional part; odmlib will not truncate it",
        )
    raise OdmlibTypeError(
        f"Expected integer for {field_name or 'attribute'} with value {value!r}",
        attribute=field_name,
        expected_type="int",
        actual_value=value,
        hint="Provide an integer, an integral float such as 8.0, or an xs:integer string",
    )


def _float_or_none(value: Any, field_name: Optional[str] = None) -> Optional[float]:
    """Convert to float, handling None.

    Under ``ValidationMode.SKIP_TYPE`` (permissive), returns the raw value
    unchanged when conversion fails so the descriptor can store it as-is.
    Otherwise raises :exc:`OdmlibTypeError` for parity with descriptor errors.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        if _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
            return value
        raise OdmlibTypeError(
            f"Expected float for {field_name or 'attribute'} with value {value!r}",
            attribute=field_name,
            expected_type="float",
            actual_value=value,
            hint="Provide a number or a string convertible to a float",
        )


def _make_description(text: Optional[str]) -> Optional[DEF.Description]:
    """Create a Description element from text, or return None."""
    if text is None:
        return None
    return DEF.Description(
        TranslatedText=[DEF.TranslatedText(_content=text)]
    )


def _make_doc_refs(leaf_ids_str: Optional[str]) -> list:
    """Build a list of DocumentRef from a comma-joined leafID string."""
    ids = _split_ids(leaf_ids_str)
    return [DEF.DocumentRef(leafID=lid) for lid in ids]


# ------------------------------------------------------------------ #
# DefineBuilder
# ------------------------------------------------------------------ #

class DefineBuilder:
    """Reconstruct a Define-XML v2.1 ODM object tree from Dataset-JSON tables.

    Takes the same ``dict[str, DatasetJSON]`` that
    :meth:`DefineFlattener.flatten_all` returns and rebuilds the full odmlib
    object hierarchy.

    Args:
        datasets: Mapping of table name to DatasetJSON, with keys:
            study, standards, datasets, variables, value_level,
            where_clauses, methods, comments, documents, codelists,
            codelist_terms.

    Example::

        from odmlib.dataset_json_1_1 import DefineFlattener, DefineBuilder

        flattener = DefineFlattener(odm_root)
        flat = flattener.flatten_all()
        rebuilt = DefineBuilder(flat).build()
        rebuilt.write_xml('rebuilt_define.xml')
    """

    # Expected dataset names (same as DefineFlattener.TABLE_NAMES)
    TABLE_NAMES = [
        "study", "standards", "datasets", "variables", "value_level",
        "where_clauses", "methods", "comments", "documents",
        "codelists", "codelist_terms",
    ]

    # Optional lossless-roundtrip extension datasets
    EXTRA_TABLE_NAMES = ["aliases", "origins"]

    def __init__(self, datasets: dict[str, DatasetJSON]):
        self.datasets = datasets
        self._post_build_hooks: list = []

    def add_post_build_hook(self, hook) -> "DefineBuilder":
        """Register a callable invoked with the assembled ODM root.

        The hook runs just before :meth:`build` returns, enabling
        insertion of Define-XML elements the 11 datasets cannot express
        (e.g. ``Alias``, full ``Origin``/``DocumentRef`` trees,
        ``AnnotatedCRF``).  If the hook returns a non-``None`` value it
        replaces the ODM root.

        Args:
            hook: Callable taking the ``DEF.ODM`` root; may mutate it
                in place or return a replacement.

        Returns:
            DefineBuilder: self, for chaining.
        """
        self._post_build_hooks.append(hook)
        return self

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def build(self) -> DEF.ODM:
        """Reconstruct the full Define-XML v2.1 ODM object tree.

        Returns:
            DEF.ODM: A complete odmlib Define-XML v2.1 root object.
        """
        documents = self._build_documents()
        comments = self._build_comments()
        methods = self._build_methods()
        where_clauses = self._build_where_clauses()
        codelists = self._build_codelists()
        item_defs = self._build_item_defs()
        value_list_defs = self._build_value_list_defs()
        item_group_defs = self._build_item_group_defs()
        standards = self._build_standards()

        mdv = self._build_metadata_version(
            item_group_defs=item_group_defs,
            item_defs=item_defs,
            code_lists=codelists,
            method_defs=methods,
            value_list_defs=value_list_defs,
            where_clause_defs=where_clauses,
            comment_defs=comments,
            leaves=documents,
            standards=standards,
        )

        self._apply_origins(mdv)
        self._apply_aliases(mdv)

        odm = self._build_odm(mdv)
        for hook in self._post_build_hooks:
            replacement = hook(odm)
            if replacement is not None:
                odm = replacement
        return odm

    @classmethod
    def read_all(cls, input_dir: str) -> dict[str, DatasetJSON]:
        """Load 11 Dataset-JSON files from a directory.

        Expects files named ``{table_name}.json`` for each table in
        :attr:`TABLE_NAMES`.

        Args:
            input_dir: Directory containing the JSON files.

        Returns:
            dict[str, DatasetJSON]: Mapping suitable for the constructor.
        """
        result = {}
        for name in cls.TABLE_NAMES:
            path = os.path.join(input_dir, f"{name}.json")
            result[name] = DatasetJSON.read_json(path)
        for name in cls.EXTRA_TABLE_NAMES:
            path = os.path.join(input_dir, f"{name}.json")
            if os.path.exists(path):
                result[name] = DatasetJSON.read_json(path)
        return result

    # ------------------------------------------------------------------ #
    # Row access
    # ------------------------------------------------------------------ #

    def _rows_as_dicts(self, dataset_name: str) -> list[dict]:
        """Convert DatasetJSON rows to a list of dicts keyed by column name.

        Returns an empty list for an absent dataset so the optional
        lossless-extension tables (``aliases``, ``origins``) are not
        required for backward compatibility.
        """
        ds = self.datasets.get(dataset_name)
        if ds is None:
            return []
        col_names = [c.name for c in ds.columns]
        rows = getattr(ds, "rows", None) or []
        return [dict(zip(col_names, row)) for row in rows]

    # ------------------------------------------------------------------ #
    # Individual builders
    # ------------------------------------------------------------------ #

    def _build_documents(self) -> list:
        """Build leaf elements from the documents dataset."""
        result = []
        for row in self._rows_as_dicts("documents"):
            result.append(DEF.leaf(
                ID=row["ID"],
                href=row["href"],
                title=DEF.title(_content=row["title"]),
            ))
        return result

    def _build_comments(self) -> list:
        """Build CommentDef elements from the comments dataset."""
        result = []
        for row in self._rows_as_dicts("comments"):
            kwargs = {"OID": row["OID"]}
            desc = _make_description(row["DescriptionText"])
            if desc is not None:
                kwargs["Description"] = desc
            doc_refs = _make_doc_refs(row["DocumentRefLeafIDs"])
            if doc_refs:
                kwargs["DocumentRef"] = doc_refs
            result.append(DEF.CommentDef(**kwargs))
        return result

    def _build_methods(self) -> list:
        """Build MethodDef elements from the methods dataset.

        Multiple rows with the same OID represent multiple
        FormalExpressions (denormalized by the flattener).
        """
        rows = self._rows_as_dicts("methods")

        # Group by OID preserving order
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["OID"]].append(row)

        result = []
        for oid, group_rows in grouped.items():
            first = group_rows[0]
            kwargs = {"OID": oid, "Name": first["Name"], "Type": first["Type"]}
            desc = _make_description(first["DescriptionText"])
            if desc is not None:
                kwargs["Description"] = desc

            # FormalExpressions (skip None-rows from methods with no expressions)
            formal_exprs = []
            for r in group_rows:
                if r["FormalExpressionContext"] is not None:
                    formal_exprs.append(DEF.FormalExpression(
                        Context=r["FormalExpressionContext"],
                        _content=r["FormalExpressionText"],
                    ))
            if formal_exprs:
                kwargs["FormalExpression"] = formal_exprs

            # DocumentRef (from first row — flattener repeats parent fields)
            doc_refs = _make_doc_refs(first["DocumentRefLeafIDs"])
            if doc_refs:
                kwargs["DocumentRef"] = doc_refs

            result.append(DEF.MethodDef(**kwargs))
        return result

    def _build_where_clauses(self) -> list:
        """Build WhereClauseDef elements from the where_clauses dataset.

        Multiple rows with the same WhereClauseOID represent multiple
        RangeChecks.
        """
        rows = self._rows_as_dicts("where_clauses")

        grouped = defaultdict(list)
        for row in rows:
            grouped[row["WhereClauseOID"]].append(row)

        result = []
        for wc_oid, group_rows in grouped.items():
            kwargs = {"OID": wc_oid}
            _optional(kwargs, "CommentOID", group_rows[0]["WhereClauseCommentOID"])

            range_checks = []
            for r in group_rows:
                rc_kwargs = {
                    "Comparator": r["Comparator"],
                    "SoftHard": r["SoftHard"] or "Soft",
                    "ItemOID": r["ItemOID"],
                }
                if r["CheckValues"]:
                    rc_kwargs["CheckValue"] = [
                        DEF.CheckValue(_content=v.strip())
                        for v in r["CheckValues"].split(", ")
                    ]
                range_checks.append(DEF.RangeCheck(**rc_kwargs))

            kwargs["RangeCheck"] = range_checks
            result.append(DEF.WhereClauseDef(**kwargs))
        return result

    def _build_codelists(self) -> list:
        """Build CodeList elements from the codelists + codelist_terms datasets."""
        cl_rows = self._rows_as_dicts("codelists")
        term_rows = self._rows_as_dicts("codelist_terms")

        # Group terms by CodeListOID
        terms_by_cl = defaultdict(list)
        for t in term_rows:
            terms_by_cl[t["CodeListOID"]].append(t)

        result = []
        for cl in cl_rows:
            kwargs = {
                "OID": cl["OID"],
                "Name": cl["Name"],
                "DataType": cl["DataType"],
            }
            _optional(kwargs, "IsNonStandard", cl["IsNonStandard"])
            _optional(kwargs, "StandardOID", cl["StandardOID"])
            _optional(kwargs, "SASFormatName", cl["SASFormatName"])
            _optional(kwargs, "CommentOID", cl["CommentOID"])
            desc = _make_description(cl["DescriptionText"])
            if desc is not None:
                kwargs["Description"] = desc

            # Terms
            terms = terms_by_cl.get(cl["OID"], [])
            has_decodes = any(t["DecodedText"] is not None for t in terms)

            if has_decodes:
                items = []
                for t in terms:
                    cli_kwargs = {"CodedValue": t["CodedValue"]}
                    _optional(cli_kwargs, "Rank", _float_or_none(t["Rank"], "Rank"))
                    _optional(cli_kwargs, "OrderNumber", _int_or_none(t["OrderNumber"], "OrderNumber"))
                    _optional(cli_kwargs, "ExtendedValue", t["ExtendedValue"])
                    if t["DecodedText"] is not None:
                        cli_kwargs["Decode"] = DEF.Decode(
                            TranslatedText=[DEF.TranslatedText(_content=t["DecodedText"])]
                        )
                    items.append(DEF.CodeListItem(**cli_kwargs))
                kwargs["CodeListItem"] = items
            elif terms:
                items = []
                for t in terms:
                    ei_kwargs = {"CodedValue": t["CodedValue"]}
                    _optional(ei_kwargs, "Rank", _float_or_none(t["Rank"], "Rank"))
                    _optional(ei_kwargs, "OrderNumber", _int_or_none(t["OrderNumber"], "OrderNumber"))
                    _optional(ei_kwargs, "ExtendedValue", t["ExtendedValue"])
                    items.append(DEF.EnumeratedItem(**ei_kwargs))
                kwargs["EnumeratedItem"] = items

            # ExternalCodeList
            if cl["ExternalDictionary"] or cl["ExternalVersion"]:
                ecl_kwargs = {}
                _optional(ecl_kwargs, "Dictionary", cl["ExternalDictionary"])
                _optional(ecl_kwargs, "Version", cl["ExternalVersion"])
                _optional(ecl_kwargs, "ref", cl["ExternalRef"])
                _optional(ecl_kwargs, "href", cl["ExternalHref"])
                kwargs["ExternalCodeList"] = DEF.ExternalCodeList(**ecl_kwargs)

            result.append(DEF.CodeList(**kwargs))
        return result

    def _build_item_defs(self) -> list:
        """Build ItemDef elements from variables + value_level (deduplicated).

        The same ItemDef OID may appear in multiple rows of the variables
        table (shared across datasets) and in value_level. We collect the
        first occurrence of each unique OID.
        """
        var_rows = self._rows_as_dicts("variables")
        vl_rows = self._rows_as_dicts("value_level")

        seen = {}  # OID -> row dict (first occurrence)
        valuelist_map = {}  # ItemOID -> ValueListOID

        for row in var_rows:
            oid = row["ItemOID"]
            if oid not in seen:
                seen[oid] = row
            if row.get("ValueListOID"):
                valuelist_map[oid] = row["ValueListOID"]

        for row in vl_rows:
            oid = row["ItemOID"]
            if oid not in seen:
                seen[oid] = row

        result = []
        for oid, row in seen.items():
            kwargs = {
                "OID": oid,
                "Name": row["Name"],
                "DataType": row["DataType"],
            }
            _optional(kwargs, "Length", _int_or_none(row["Length"], "Length"))
            _optional(kwargs, "SignificantDigits", _int_or_none(row["SignificantDigits"], "SignificantDigits"))
            _optional(kwargs, "SASFieldName", row["SASFieldName"])
            _optional(kwargs, "DisplayFormat", row["DisplayFormat"])
            _optional(kwargs, "CommentOID", row["CommentOID"])

            desc = _make_description(row["DescriptionText"])
            if desc is not None:
                kwargs["Description"] = desc

            if row.get("CodeListOID"):
                kwargs["CodeListRef"] = DEF.CodeListRef(
                    CodeListOID=row["CodeListOID"]
                )
            if oid in valuelist_map:
                kwargs["ValueListRef"] = DEF.ValueListRef(
                    ValueListOID=valuelist_map[oid]
                )

            # Origin (only Type and Source captured by flattener)
            if row.get("OriginType"):
                origin_kwargs = {"Type": row["OriginType"]}
                _optional(origin_kwargs, "Source", row["OriginSource"])
                kwargs["Origin"] = [DEF.Origin(**origin_kwargs)]

            result.append(DEF.ItemDef(**kwargs))
        return result

    def _build_value_list_defs(self) -> list:
        """Build ValueListDef elements from the value_level dataset."""
        rows = self._rows_as_dicts("value_level")

        grouped = defaultdict(list)
        for row in rows:
            grouped[row["ValueListOID"]].append(row)

        result = []
        for vl_oid, group_rows in grouped.items():
            item_refs = []
            for r in group_rows:
                ir_kwargs = {
                    "ItemOID": r["ItemOID"],
                    "Mandatory": r["Mandatory"],
                }
                _optional(ir_kwargs, "OrderNumber", _int_or_none(r["OrderNumber"], "OrderNumber"))
                _optional(ir_kwargs, "MethodOID", r["MethodOID"])
                if r.get("WhereClauseOID"):
                    ir_kwargs["WhereClauseRef"] = [
                        DEF.WhereClauseRef(WhereClauseOID=r["WhereClauseOID"])
                    ]
                item_refs.append(DEF.ItemRef(**ir_kwargs))
            result.append(DEF.ValueListDef(OID=vl_oid, ItemRef=item_refs))
        return result

    def _build_item_group_defs(self) -> list:
        """Build ItemGroupDef elements from datasets + variables."""
        ds_rows = self._rows_as_dicts("datasets")
        var_rows = self._rows_as_dicts("variables")

        # Pre-group variables by DatasetOID
        vars_by_ds = defaultdict(list)
        for v in var_rows:
            vars_by_ds[v["DatasetOID"]].append(v)

        result = []
        for ds in ds_rows:
            kwargs = {
                "OID": ds["OID"],
                "Name": ds["Name"],
                "Repeating": ds["Repeating"],
                "Structure": ds["Structure"],
            }
            _optional(kwargs, "IsReferenceData", ds["IsReferenceData"])
            _optional(kwargs, "SASDatasetName", ds["SASDatasetName"])
            _optional(kwargs, "Domain", ds["Domain"])
            _optional(kwargs, "Purpose", ds["Purpose"])
            _optional(kwargs, "ArchiveLocationID", ds["ArchiveLocationID"])
            _optional(kwargs, "CommentOID", ds["CommentOID"])
            _optional(kwargs, "IsNonStandard", ds["IsNonStandard"])
            _optional(kwargs, "StandardOID", ds["StandardOID"])
            _optional(kwargs, "HasNoData", ds["HasNoData"])

            desc = _make_description(ds["DescriptionText"])
            if desc is not None:
                kwargs["Description"] = desc

            # Class element
            if ds["ClassName"]:
                class_kwargs = {"Name": ds["ClassName"]}
                if ds["SubClassName"]:
                    class_kwargs["SubClass"] = [
                        DEF.SubClass(Name=ds["SubClassName"])
                    ]
                kwargs["Class"] = DEF.Class(**class_kwargs)

            # leaf element
            if ds["leafID"]:
                kwargs["leaf"] = DEF.leaf(
                    ID=ds["leafID"],
                    href=ds["leafHref"],
                    title=DEF.title(_content=ds["leafTitle"] or ""),
                )

            # ItemRef children from variables table
            item_refs = []
            for v in vars_by_ds.get(ds["OID"], []):
                ir_kwargs = {
                    "ItemOID": v["ItemOID"],
                    "Mandatory": v["Mandatory"],
                }
                _optional(ir_kwargs, "OrderNumber", _int_or_none(v["OrderNumber"], "OrderNumber"))
                _optional(ir_kwargs, "KeySequence", _int_or_none(v["KeySequence"], "KeySequence"))
                _optional(ir_kwargs, "MethodOID", v["MethodOID"])
                _optional(ir_kwargs, "Role", v["Role"])
                _optional(ir_kwargs, "RoleCodeListOID", v["RoleCodeListOID"])
                _optional(ir_kwargs, "IsNonStandard", v["IsNonStandard"])
                _optional(ir_kwargs, "HasNoData", v["HasNoData"])
                item_refs.append(DEF.ItemRef(**ir_kwargs))
            if item_refs:
                kwargs["ItemRef"] = item_refs

            result.append(DEF.ItemGroupDef(**kwargs))
        return result

    def _build_standards(self) -> Optional[DEF.Standards]:
        """Build Standards element from the standards dataset."""
        rows = self._rows_as_dicts("standards")
        if not rows:
            return None

        standard_list = []
        for row in rows:
            kwargs = {
                "OID": row["OID"],
                "Name": row["Name"],
                "Type": row["Type"],
                "Version": row["Version"],
            }
            _optional(kwargs, "PublishingSet", row["PublishingSet"])
            _optional(kwargs, "Status", row["Status"])
            _optional(kwargs, "CommentOID", row["CommentOID"])
            standard_list.append(DEF.Standard(**kwargs))

        return DEF.Standards(Standard=standard_list)

    # ------------------------------------------------------------------ #
    # Lossless-roundtrip post-passes (no-op when the dataset is absent)
    # ------------------------------------------------------------------ #

    def _apply_origins(self, mdv: DEF.MetaDataVersion) -> None:
        """Replace inline Origins with the full origins-dataset trees.

        The variables/value_level tables only carry the first Origin's
        Type and Source.  When the optional ``origins`` dataset is
        present it is authoritative: every ItemDef it names has its
        Origin list rebuilt with Description and DocumentRef children.
        """
        rows = self._rows_as_dicts("origins")
        if not rows:
            return
        by_item: dict[str, list] = defaultdict(list)
        for r in rows:
            kwargs = {"Type": r["Type"]}
            _optional(kwargs, "Source", r["Source"])
            text = r.get("DescriptionText")
            if text is not None:
                lang = r.get("DescriptionLang")
                tt = (DEF.TranslatedText(_content=text, lang=lang)
                      if lang else DEF.TranslatedText(_content=text))
                kwargs["Description"] = DEF.Description(TranslatedText=[tt])
            doc_refs = _make_doc_refs(r.get("DocumentRefLeafIDs"))
            if doc_refs:
                kwargs["DocumentRef"] = doc_refs
            order = _int_or_none(r.get("OrderNumber"), "OrderNumber") or 0
            by_item[r["ItemOID"]].append((order, DEF.Origin(**kwargs)))
        for item_def in getattr(mdv, "ItemDef", None) or []:
            if item_def.OID in by_item:
                ordered = sorted(by_item[item_def.OID], key=lambda t: t[0])
                item_def.Origin = [origin for _, origin in ordered]

    def _apply_aliases(self, mdv: DEF.MetaDataVersion) -> None:
        """Attach Alias elements from the optional ``aliases`` dataset."""
        rows = self._rows_as_dicts("aliases")
        if not rows:
            return
        igd_by_oid = {x.OID: x for x in getattr(mdv, "ItemGroupDef", None) or []}
        idf_by_oid = {x.OID: x for x in getattr(mdv, "ItemDef", None) or []}
        cl_by_oid = {x.OID: x for x in getattr(mdv, "CodeList", None) or []}

        def _term(cl, member):
            for t in (getattr(cl, "CodeListItem", None) or []) + \
                     (getattr(cl, "EnumeratedItem", None) or []):
                if getattr(t, "CodedValue", None) == member:
                    return t
            return None

        for r in rows:
            ptype, poid, member = r["ParentType"], r["ParentOID"], r["Member"]
            alias = DEF.Alias(Context=r["Context"], Name=r["Name"])
            if ptype == "ItemGroupDef":
                target = igd_by_oid.get(poid)
            elif ptype == "ItemDef":
                target = idf_by_oid.get(poid)
            elif ptype == "CodeList":
                target = cl_by_oid.get(poid)
            elif ptype in ("CodeListItem", "EnumeratedItem"):
                cl = cl_by_oid.get(poid)
                target = _term(cl, member) if cl is not None else None
            else:
                target = None
            if target is not None:
                target.Alias.append(alias)

    def _build_metadata_version(self, *, item_group_defs, item_defs,
                                 code_lists, method_defs, value_list_defs,
                                 where_clause_defs, comment_defs, leaves,
                                 standards) -> DEF.MetaDataVersion:
        """Assemble MetaDataVersion from all child elements."""
        study_rows = self._rows_as_dicts("study")
        study_row = study_rows[0]

        kwargs = {
            "OID": study_row["MetaDataVersionOID"],
            "Name": study_row["MetaDataVersionName"],
            "DefineVersion": study_row["DefineVersion"],
        }
        _optional(kwargs, "CommentOID", study_row["CommentOID"])

        if standards is not None:
            kwargs["Standards"] = standards
        if value_list_defs:
            kwargs["ValueListDef"] = value_list_defs
        if where_clause_defs:
            kwargs["WhereClauseDef"] = where_clause_defs
        if item_group_defs:
            kwargs["ItemGroupDef"] = item_group_defs
        if item_defs:
            kwargs["ItemDef"] = item_defs
        if code_lists:
            kwargs["CodeList"] = code_lists
        if method_defs:
            kwargs["MethodDef"] = method_defs
        if comment_defs:
            kwargs["CommentDef"] = comment_defs
        if leaves:
            kwargs["leaf"] = leaves

        return DEF.MetaDataVersion(**kwargs)

    def _build_odm(self, metadata_version: DEF.MetaDataVersion) -> DEF.ODM:
        """Build the root ODM element from the study dataset."""
        study_rows = self._rows_as_dicts("study")
        study_row = study_rows[0]

        gv = DEF.GlobalVariables(
            StudyName=DEF.StudyName(_content=study_row["StudyName"] or ""),
            StudyDescription=DEF.StudyDescription(
                _content=study_row["StudyDescription"] or ""
            ),
            ProtocolName=DEF.ProtocolName(
                _content=study_row["ProtocolName"] or ""
            ),
        )

        study = DEF.Study(
            OID=study_row["StudyOID"],
            GlobalVariables=gv,
            MetaDataVersion=metadata_version,
        )

        odm_kwargs = {
            "FileType": "Snapshot",
            "FileOID": study_row["FileOID"],
            "CreationDateTime": study_row["CreationDateTime"],
            "ODMVersion": "1.3.2",
            "Context": study_row["Context"],
            "Study": study,
        }
        _optional(odm_kwargs, "AsOfDateTime", study_row["AsOfDateTime"])
        _optional(odm_kwargs, "Originator", study_row["Originator"])
        _optional(odm_kwargs, "SourceSystem", study_row["SourceSystem"])
        _optional(odm_kwargs, "SourceSystemVersion",
                  study_row["SourceSystemVersion"])

        return DEF.ODM(**odm_kwargs)
