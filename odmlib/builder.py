"""
Optional builder/fluent API for constructing ODM documents.

The builder provides a chainable interface for constructing complex
documents with less boilerplate. It wraps the standard odmlib model
classes and is purely additive — all existing APIs continue to work
unchanged.

Example::

    from odmlib.builder import ODMBuilder

    odm = (ODMBuilder("odm_1_3_2")
        .set_file(FileOID="F.001", FileType="Snapshot",
                  CreationDateTime="2024-01-01T00:00:00")
        .add_study(OID="S.001",
                   study_name="My Study",
                   study_description="A study",
                   protocol_name="PROT-001")
        .add_metadata_version(OID="MDV.001", Name="Version 1")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .add_item_ref(ItemOID="IT.SUBJID", Mandatory="Yes", OrderNumber=1)
        .add_item_ref(ItemOID="IT.AGE", Mandatory="No", OrderNumber=2)
        .build())
"""
from __future__ import annotations
from typing import Any, Optional
import importlib

import odmlib.odm_element as OE
import odmlib.typed as T


class ODMBuilder:
    """Fluent builder for constructing ODM documents.

    Maintains state for the currently active Study, MetaDataVersion,
    and ItemGroupDef so that ``add_*`` calls automatically append to
    the right parent.

    Works with ``odm_1_3_2``, ``define_2_0``, ``define_2_1`` and
    ``odm_2_0``.  Model-shape differences are handled automatically —
    notably the ODM 2.0 ``Study`` (scalar ``StudyName`` / ``ProtocolName``,
    no ``GlobalVariables``) and its object-valued ``Description``.  Note
    that ODM 2.0 is structurally flatter: ``StudyEventDef`` references
    ``ItemGroupRef`` directly (there is no ``FormDef`` / ``FormRef``), so
    the form-level helpers do not apply to ``odm_2_0``.

    :param model_package: The odmlib model package to use.
        Defaults to ``"odm_1_3_2"``.
    """

    def __init__(self, model_package: str = "odm_1_3_2") -> None:
        self._model = importlib.import_module(f"odmlib.{model_package}.model")
        self._file_attrs: dict[str, Any] = {}
        self._studies: list = []
        self._current_study: Any = None
        self._current_mdv: Any = None
        self._current_igd: Any = None
        self._current_item_def: Any = None
        self._current_form_def: Any = None
        self._current_sed: Any = None

    # ------------------------------------------------------------------
    # Model-shape detection
    # ------------------------------------------------------------------

    def _uses_global_variables(self) -> bool:
        """Whether the active model uses the ODM 1.3.2 study structure.

        ODM 1.3.2 and the Define-XML models nest study identification under
        a ``GlobalVariables`` element (with ``StudyName`` /
        ``StudyDescription`` / ``ProtocolName`` child elements) and model
        ``MetaDataVersion.Description`` as a plain string.  ODM 2.0 has a
        flatter shape: scalar ``StudyName`` / ``ProtocolName`` attributes on
        ``Study``, an object-valued ``Study.Description``, and an
        object-valued ``MetaDataVersion.Description``.  Presence of the
        ``GlobalVariables`` class is a precise proxy for that distinction.
        """
        return hasattr(self._model, "GlobalVariables")

    def _translated_text(self, **kw: Any) -> Any:
        """Construct a model ``TranslatedText``.

        ODM 2.0 makes ``TranslatedText/@Type`` required (a free-text media
        type per the XSD). For the ODM 2.0 model shape this helper defaults
        ``Type="text/plain"`` so builder output is schema- and model-valid;
        an explicit ``Type`` in ``kw`` always wins. For ODM 1.3.2 / Define
        (which have a ``GlobalVariables`` element and no required ``Type``)
        the kwargs are passed through unchanged, so output is byte-identical
        to before.
        """
        M = self._model
        if not self._uses_global_variables() and "Type" not in kw:
            kw["Type"] = "text/plain"
        return M.TranslatedText(**kw)

    # ------------------------------------------------------------------
    # File-level
    # ------------------------------------------------------------------

    def set_file(self, **kwargs: Any) -> ODMBuilder:
        """Set ODM file-level attributes (FileOID, FileType, CreationDateTime, …).

        These are passed directly to the ``ODM`` constructor when
        :meth:`build` is called.

        :returns: self, for chaining.
        """
        self._file_attrs = kwargs
        return self

    # ------------------------------------------------------------------
    # Study
    # ------------------------------------------------------------------

    def add_study(self, OID: str, study_name: str,
                  study_description: str, protocol_name: str,
                  **kwargs: Any) -> ODMBuilder:
        """Add a Study element.

        The Study is constructed in whichever shape the active model uses:

        - **ODM 1.3.2 / Define-XML:** a ``GlobalVariables`` element wrapping
          ``StudyName`` / ``StudyDescription`` / ``ProtocolName`` children.
        - **ODM 2.0:** scalar ``StudyName`` / ``ProtocolName`` attributes on
          ``Study`` plus an object-valued ``Description`` (there is no
          ``GlobalVariables`` element in ODM 2.0).

        :param OID: Study OID.
        :param study_name: Study name (StudyName content/attribute).
        :param study_description: Study description.
        :param protocol_name: Protocol name (ProtocolName content/attribute).
        :param kwargs: Additional Study attributes.
        :returns: self, for chaining.
        """
        M = self._model
        if self._uses_global_variables():
            sn = M.StudyName(_content=study_name)
            sd = M.StudyDescription(_content=study_description)
            pn = M.ProtocolName(_content=protocol_name)
            gv = M.GlobalVariables(StudyName=sn, StudyDescription=sd,
                                   ProtocolName=pn)
            self._current_study = M.Study(OID=OID, GlobalVariables=gv, **kwargs)
        else:
            # ODM 2.0: StudyName/ProtocolName are scalar attributes; the
            # description is an object-valued Description element.
            desc = M.Description(TranslatedText=[
                self._translated_text(_content=study_description, lang="en")])
            self._current_study = M.Study(
                OID=OID, StudyName=study_name, ProtocolName=protocol_name,
                Description=desc, **kwargs)
        self._studies.append(self._current_study)
        # a new Study starts a new scope: stale pointers from a previous
        # study must not receive later with_*/attach_to_current() calls
        self._current_mdv = None
        self._current_igd = None
        self._current_item_def = None
        self._current_sed = None
        self._current_form_def = None
        return self

    # ------------------------------------------------------------------
    # MetaDataVersion
    # ------------------------------------------------------------------

    def add_metadata_version(self, **kwargs: Any) -> ODMBuilder:
        """Add a MetaDataVersion to the current Study.

        :param kwargs: MetaDataVersion attributes (OID, Name, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no Study has been added yet.
        """
        if self._current_study is None:
            raise RuntimeError("Call add_study() before add_metadata_version()")
        M = self._model
        self._current_mdv = M.MetaDataVersion(**kwargs)
        self._current_study.MetaDataVersion.append(self._current_mdv)
        # a new MetaDataVersion starts a new scope for definitions
        self._current_igd = None
        self._current_item_def = None
        self._current_sed = None
        self._current_form_def = None
        return self

    # ------------------------------------------------------------------
    # ItemGroupDef
    # ------------------------------------------------------------------

    def add_item_group_def(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemGroupDef to the current MetaDataVersion.

        :param kwargs: ItemGroupDef attributes (OID, Name, Repeating, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_item_group_def()")
        M = self._model
        self._current_igd = M.ItemGroupDef(**kwargs)
        self._current_mdv.ItemGroupDef.append(self._current_igd)
        # the new ItemGroupDef is now the "most recent element": clear the
        # previous ItemDef so with_description()/with_alias() target this one
        self._current_item_def = None
        return self

    # ------------------------------------------------------------------
    # ItemRef
    # ------------------------------------------------------------------

    def add_item_ref(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemRef to the current ItemGroupDef.

        :param kwargs: ItemRef attributes (ItemOID, Mandatory, OrderNumber, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemGroupDef has been added yet.
        """
        if self._current_igd is None:
            raise RuntimeError("Call add_item_group_def() before add_item_ref()")
        M = self._model
        self._current_igd.ItemRef.append(M.ItemRef(**kwargs))
        return self

    # ------------------------------------------------------------------
    # ItemDef
    # ------------------------------------------------------------------

    def add_item_def(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemDef to the current MetaDataVersion.

        :param kwargs: ItemDef attributes (OID, Name, DataType, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_item_def()")
        M = self._model
        self._current_item_def = M.ItemDef(**kwargs)
        self._current_mdv.ItemDef.append(self._current_item_def)
        return self

    # ------------------------------------------------------------------
    # CodeList
    # ------------------------------------------------------------------

    def add_code_list(self, OID: str, Name: str, DataType: str,
                      items: Optional[list] = None,
                      **kwargs: Any) -> ODMBuilder:
        """Add a CodeList to the current MetaDataVersion.

        :param OID: CodeList OID.
        :param Name: CodeList name.
        :param DataType: Coded value data type.
        :param items: Optional list of dicts.  Each dict must have a
            ``"CodedValue"`` key and may have a ``"Decode"`` key
            (a plain English label string).  If ``"Decode"`` is present
            a CodeListItem is created; otherwise an EnumeratedItem.
        :param kwargs: Additional CodeList attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_code_list()")
        M = self._model
        cl = M.CodeList(OID=OID, Name=Name, DataType=DataType, **kwargs)
        if items:
            for item in items:
                coded_value = item["CodedValue"]
                decode_text = item.get("Decode")
                if decode_text:
                    decode = M.Decode(TranslatedText=[
                        self._translated_text(_content=decode_text, lang="en")])
                    cl.CodeListItem.append(
                        M.CodeListItem(CodedValue=coded_value, Decode=decode))
                else:
                    cl.EnumeratedItem.append(
                        M.EnumeratedItem(CodedValue=coded_value))
        self._current_mdv.CodeList.append(cl)
        return self

    # ------------------------------------------------------------------
    # Description helper
    # ------------------------------------------------------------------

    def with_description(self, text: str, lang: str = "en") -> ODMBuilder:
        """Attach a Description to the most recently created element.

        Applies to the most recently created ItemGroupDef or ItemDef.
        Falls back to the current MetaDataVersion if neither is set.

        :param text: Description text.
        :param lang: Language code (default ``"en"``).
        :returns: self, for chaining.
        """
        M = self._model
        desc = M.Description(TranslatedText=[
            self._translated_text(_content=text, lang=lang)])
        if self._current_item_def is not None:
            self._current_item_def.Description = desc
        elif self._current_igd is not None:
            self._current_igd.Description = desc
        elif self._current_mdv is not None:
            if self._uses_global_variables():
                # ODM 1.3.2 / Define: MetaDataVersion.Description is a String.
                self._current_mdv.Description = text
            else:
                # ODM 2.0: MetaDataVersion.Description is a Description object.
                self._current_mdv.Description = desc
        return self

    # ------------------------------------------------------------------
    # Protocol / StudyEventDef / StudyEventRef
    # ------------------------------------------------------------------

    def _require_v1(self, feature: str) -> None:
        """Raise if the active model is ODM 2.0 (which lacks ``feature``)."""
        if not self._uses_global_variables():
            raise RuntimeError(
                f"{feature} is not part of ODM 2.0. In ODM 2.0 a "
                f"StudyEventDef references ItemGroupRef directly — use "
                f"add_study_event_def() then add_item_group_ref().")

    def add_study_event_def(self, **kwargs: Any) -> ODMBuilder:
        """Add a StudyEventDef to the current MetaDataVersion.

        The StudyEventDef is appended to ``MetaDataVersion.StudyEventDef``
        and becomes the *current* study event so that subsequent
        :meth:`add_form_ref` (ODM 1.3.2) or :meth:`add_item_group_ref`
        (ODM 2.0) calls attach to it.  This does *not* create a Protocol
        reference — use :meth:`add_study_event_ref` for that.

        :param kwargs: StudyEventDef attributes (OID, Name, Repeating, Type, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_study_event_def()")
        M = self._model
        self._current_sed = M.StudyEventDef(**kwargs)
        self._current_form_def = None
        self._current_mdv.StudyEventDef.append(self._current_sed)
        return self

    def add_study_event_ref(self, **kwargs: Any) -> ODMBuilder:
        """Add a StudyEventRef to the current MetaDataVersion's Protocol.

        The Protocol element is created automatically if it does not exist
        yet.

        .. warning::

           **Not valid for ``model_package="odm_2_0"``.** The ODM 2.0 XSD
           removed ``Protocol/StudyEventRef`` (Protocol uses
           ``StudyEventGroupRef`` instead); a document built with this helper
           under odm_2_0 is schema-invalid. See ROADMAP "v0.2.1 — ODM 2.0
           Model/XSD Alignment" and ``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md``
           §3.3. Safe for ODM 1.3.2.

        :param kwargs: StudyEventRef attributes (StudyEventOID, Mandatory,
            OrderNumber, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_study_event_ref()")
        M = self._model
        if self._current_mdv.Protocol is None:
            self._current_mdv.Protocol = M.Protocol()
        self._current_mdv.Protocol.StudyEventRef.append(M.StudyEventRef(**kwargs))
        return self

    # ------------------------------------------------------------------
    # FormDef / FormRef (ODM 1.3.2 / Define-XML only)
    # ------------------------------------------------------------------

    def add_form_def(self, **kwargs: Any) -> ODMBuilder:
        """Add a FormDef to the current MetaDataVersion (ODM 1.3.2 only).

        Becomes the current form so that :meth:`add_item_group_ref`
        attaches its ItemGroupRefs here.

        :param kwargs: FormDef attributes (OID, Name, Repeating, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion yet, or model is ODM 2.0.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_form_def()")
        self._require_v1("FormDef")
        M = self._model
        self._current_form_def = M.FormDef(**kwargs)
        self._current_mdv.FormDef.append(self._current_form_def)
        return self

    def add_form_ref(self, **kwargs: Any) -> ODMBuilder:
        """Add a FormRef to the current StudyEventDef (ODM 1.3.2 only).

        :param kwargs: FormRef attributes (FormOID, Mandatory, OrderNumber, …).
        :returns: self, for chaining.
        :raises RuntimeError: if no StudyEventDef yet, or model is ODM 2.0.
        """
        self._require_v1("FormRef")
        if self._current_sed is None:
            raise RuntimeError("Call add_study_event_def() before add_form_ref()")
        M = self._model
        self._current_sed.FormRef.append(M.FormRef(**kwargs))
        return self

    def add_item_group_ref(self, **kwargs: Any) -> ODMBuilder:
        """Add an ItemGroupRef to the appropriate parent.

        In ODM 1.3.2 / Define-XML the ItemGroupRef is added to the current
        FormDef (call :meth:`add_form_def` first).  In ODM 2.0 — which has
        no FormDef — it is added to the current StudyEventDef (call
        :meth:`add_study_event_def` first).

        :param kwargs: ItemGroupRef attributes (ItemGroupOID, Mandatory, …).
        :returns: self, for chaining.
        :raises RuntimeError: if the required parent has not been added yet.
        """
        M = self._model
        if self._uses_global_variables():
            if self._current_form_def is None:
                raise RuntimeError("Call add_form_def() before add_item_group_ref()")
            self._current_form_def.ItemGroupRef.append(M.ItemGroupRef(**kwargs))
        else:
            if self._current_sed is None:
                raise RuntimeError(
                    "Call add_study_event_def() before add_item_group_ref()")
            self._current_sed.ItemGroupRef.append(M.ItemGroupRef(**kwargs))
        return self

    # ------------------------------------------------------------------
    # MethodDef / ConditionDef
    # ------------------------------------------------------------------

    def add_method_def(self, OID: str, Name: str, Type: str, description: str,
                        formal_expression: Optional[str] = None,
                        expression_context: str = "Python",
                        lang: str = "en", **kwargs: Any) -> ODMBuilder:
        """Add a MethodDef to the current MetaDataVersion.

        MethodDef requires a Description; it is built from ``description``.
        An optional FormalExpression is added when ``formal_expression`` is
        given.

        .. warning::

           For ``model_package="odm_2_0"``, do **not** pass
           ``formal_expression``: ODM 2.0 ``FormalExpression`` is
           element-based (``Code | ExternalCodeLib``) while odmlib's model is
           text-based, so a text FormalExpression is schema-invalid. The
           Description-only form is valid. See ROADMAP "v0.2.1 — ODM 2.0
           Model/XSD Alignment" / ``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`` §3.2.

        :param OID: Method OID.
        :param Name: Method name.
        :param Type: Method type (e.g. "Computation", "Imputation").
        :param description: Human-readable description text.
        :param formal_expression: Optional expression source code.
        :param expression_context: FormalExpression Context (e.g. "Python",
            "SAS"); used only when ``formal_expression`` is given.
        :param lang: Language code for the Description (default ``"en"``).
        :param kwargs: Additional MethodDef attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_method_def()")
        M = self._model
        desc = M.Description(TranslatedText=[
            self._translated_text(_content=description, lang=lang)])
        md = M.MethodDef(OID=OID, Name=Name, Type=Type, Description=desc,
                         **kwargs)
        if formal_expression is not None:
            md.FormalExpression.append(M.FormalExpression(
                Context=expression_context, _content=formal_expression))
        self._current_mdv.MethodDef.append(md)
        return self

    def add_condition_def(self, OID: str, Name: str,
                          description: Optional[str] = None,
                          formal_expression: Optional[str] = None,
                          expression_context: str = "Python",
                          lang: str = "en", **kwargs: Any) -> ODMBuilder:
        """Add a ConditionDef to the current MetaDataVersion.

        .. warning::

           **Not valid for ``model_package="odm_2_0"``.** The ODM 2.0 XSD
           requires a ``MethodSignature`` child on ``ConditionDef`` (and a
           required ``Description``), which odmlib's odm_2_0 model cannot yet
           express, so any ConditionDef built here is schema-invalid — and
           transitively any ``CollectionExceptionConditionOID`` pointing at
           it. ``formal_expression`` is additionally invalid under odm_2_0
           (text vs. element-based, see :meth:`add_method_def`). See ROADMAP
           "v0.2.1 — ODM 2.0 Model/XSD Alignment" /
           ``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`` §3.1–§3.2. Safe for ODM
           1.3.2.

        :param OID: Condition OID.
        :param Name: Condition name.
        :param description: Optional description text.
        :param formal_expression: Optional expression source code.
        :param expression_context: FormalExpression Context; used only when
            ``formal_expression`` is given.
        :param lang: Language code for the Description (default ``"en"``).
        :param kwargs: Additional ConditionDef attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no MetaDataVersion has been added yet.
        """
        if self._current_mdv is None:
            raise RuntimeError("Call add_metadata_version() before add_condition_def()")
        M = self._model
        cd = M.ConditionDef(OID=OID, Name=Name, **kwargs)
        if description is not None:
            cd.Description = M.Description(TranslatedText=[
                self._translated_text(_content=description, lang=lang)])
        if formal_expression is not None:
            cd.FormalExpression.append(M.FormalExpression(
                Context=expression_context, _content=formal_expression))
        self._current_mdv.ConditionDef.append(cd)
        return self

    # ------------------------------------------------------------------
    # MeasurementUnit (ODM 1.3.2 / Define-XML only)
    # ------------------------------------------------------------------

    def add_measurement_unit(self, OID: str, Name: str, symbol: str,
                             lang: str = "en", **kwargs: Any) -> ODMBuilder:
        """Add a MeasurementUnit to the Study's BasicDefinitions.

        BasicDefinitions is created automatically if absent.  Not available
        in ODM 2.0 (which has no BasicDefinitions/MeasurementUnit).

        :param OID: MeasurementUnit OID.
        :param Name: MeasurementUnit name.
        :param symbol: Symbol text (wrapped in Symbol/TranslatedText).
        :param lang: Language code for the Symbol (default ``"en"``).
        :param kwargs: Additional MeasurementUnit attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no Study yet, or model is ODM 2.0.
        """
        if self._current_study is None:
            raise RuntimeError("Call add_study() before add_measurement_unit()")
        self._require_v1("BasicDefinitions/MeasurementUnit")
        M = self._model
        if self._current_study.BasicDefinitions is None:
            self._current_study.BasicDefinitions = M.BasicDefinitions()
        sym = M.Symbol(TranslatedText=[
            self._translated_text(_content=symbol, lang=lang)])
        self._current_study.BasicDefinitions.MeasurementUnit.append(
            M.MeasurementUnit(OID=OID, Name=Name, Symbol=sym, **kwargs))
        return self

    # ------------------------------------------------------------------
    # ItemDef enrichers (operate on the most recent ItemDef)
    # ------------------------------------------------------------------

    def _require_item_def(self, method: str) -> Any:
        if self._current_item_def is None:
            raise RuntimeError(f"Call add_item_def() before {method}()")
        return self._current_item_def

    def with_question(self, text: str, lang: str = "en") -> ODMBuilder:
        """Set the Question on the most recently created ItemDef.

        :param text: Question text.
        :param lang: Language code (default ``"en"``).
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemDef has been added yet.
        """
        item = self._require_item_def("with_question")
        M = self._model
        item.Question = M.Question(TranslatedText=[
            self._translated_text(_content=text, lang=lang)])
        return self

    def with_codelist_ref(self, codelist_oid: str) -> ODMBuilder:
        """Attach a CodeListRef to the most recently created ItemDef.

        :param codelist_oid: OID of the referenced CodeList.
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemDef has been added yet.
        """
        item = self._require_item_def("with_codelist_ref")
        item.CodeListRef = self._model.CodeListRef(CodeListOID=codelist_oid)
        return self

    def with_measurement_unit_ref(self, mu_oid: str) -> ODMBuilder:
        """Add a MeasurementUnitRef to the most recent ItemDef (ODM 1.3.2 only).

        :param mu_oid: OID of the referenced MeasurementUnit.
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemDef yet, or model is ODM 2.0.
        """
        item = self._require_item_def("with_measurement_unit_ref")
        self._require_v1("MeasurementUnitRef")
        item.MeasurementUnitRef.append(
            self._model.MeasurementUnitRef(MeasurementUnitOID=mu_oid))
        return self

    def with_range_check(self, comparator: Optional[str], check_values: list,
                         soft_hard: str = "Soft",
                         **kwargs: Any) -> ODMBuilder:
        """Add a RangeCheck to the most recently created ItemDef.

        :param comparator: Comparator (e.g. "GE", "LE", "IN"); may be None.
        :param check_values: List of check values (rendered as CheckValue).
        :param soft_hard: SoftHard flag (default ``"Soft"``).
        :param kwargs: Additional RangeCheck attributes.
        :returns: self, for chaining.
        :raises RuntimeError: if no ItemDef has been added yet.
        """
        item = self._require_item_def("with_range_check")
        M = self._model
        rc_kwargs: dict[str, Any] = {"SoftHard": soft_hard}
        if comparator is not None:
            rc_kwargs["Comparator"] = comparator
        rc_kwargs["CheckValue"] = [
            M.CheckValue(_content=str(v)) for v in check_values]
        rc_kwargs.update(kwargs)
        item.RangeCheck.append(M.RangeCheck(**rc_kwargs))
        return self

    def with_alias(self, context: str, name: str) -> ODMBuilder:
        """Add an Alias to the most recent ItemDef (or ItemGroupDef).

        Applies to the most recently created ItemDef; falls back to the
        current ItemGroupDef.

        :param context: Alias Context.
        :param name: Alias Name.
        :returns: self, for chaining.
        :raises RuntimeError: if neither an ItemDef nor ItemGroupDef exists.
        """
        M = self._model
        alias = M.Alias(Context=context, Name=name)
        if self._current_item_def is not None:
            self._current_item_def.Alias.append(alias)
        elif self._current_igd is not None:
            self._current_igd.Alias.append(alias)
        else:
            raise RuntimeError(
                "Call add_item_def() or add_item_group_def() before with_alias()")
        return self

    # ------------------------------------------------------------------
    # Generic escape hatch
    # ------------------------------------------------------------------

    def _find_elem_field(self, parent: Any, element: Any):
        """Return ``(field, descriptor)`` on *parent* that accepts *element*.

        Prefers an exact class match, falling back to a subclass match
        (so a Define-XML subclass element still resolves).  Returns
        ``None`` if *parent* has no child field for *element*'s type.
        """
        elems = type(parent)._elems
        fallback = None
        for field, descr in elems.items():
            ec = getattr(descr, "element_class", None)
            if ec is None:
                continue
            if type(element) is ec:
                return field, descr
            if fallback is None and isinstance(element, ec):
                fallback = (field, descr)
        return fallback

    def _attach(self, parent: Any, element: Any) -> None:
        if not isinstance(element, OE.ODMElement):
            raise TypeError(
                f"attach() expects an ODMElement, got "
                f"{type(element).__name__}")
        match = self._find_elem_field(parent, element)
        if match is None:
            accepted = sorted({
                d.element_class.__name__
                for d in type(parent)._elems.values()
                if getattr(d, "element_class", None) is not None})
            raise TypeError(
                f"{type(parent).__name__} cannot hold "
                f"{type(element).__name__}. Accepted child elements: "
                f"{', '.join(accepted)}")
        field, descr = match
        if isinstance(descr, T.ODMListObject):
            getattr(parent, field).append(element)
        else:
            setattr(parent, field, element)

    def attach(self, parent: Any, element: Any) -> ODMBuilder:
        """Attach a pre-built ODMElement onto an explicit parent element.

        Escape hatch for any model element that has no dedicated
        ``add_*`` method.  The target child field is resolved from the
        parent's model definition — appended if it is a list element,
        assigned otherwise.

        :param parent: An ODMElement already in the tree being built
            (e.g. a value returned via :attr:`current`).
        :param element: A pre-built ODMElement to attach.
        :returns: self, for chaining.
        :raises TypeError: if *element* is not an ODMElement or *parent*
            has no child field able to hold it.
        """
        self._attach(parent, element)
        return self

    def attach_to_current(self, element: Any) -> ODMBuilder:
        """Attach a pre-built ODMElement to the most specific current parent.

        Tries the active ItemDef, FormDef, StudyEventDef, ItemGroupDef,
        MetaDataVersion and Study in turn, attaching to the first that
        accepts *element*'s type.

        :param element: A pre-built ODMElement to attach.
        :returns: self, for chaining.
        :raises TypeError: if no active element can hold *element*.
        """
        for parent in (self._current_item_def, self._current_form_def,
                       self._current_sed, self._current_igd,
                       self._current_mdv, self._current_study):
            if parent is not None and \
                    self._find_elem_field(parent, element) is not None:
                self._attach(parent, element)
                return self
        raise TypeError(
            f"No active element can hold {type(element).__name__}; "
            f"use attach(parent, element) with an explicit parent.")

    @property
    def current(self) -> dict:
        """The active context elements, for use with :meth:`attach`.

        Keys: ``study``, ``mdv``, ``item_group_def``, ``item_def``,
        ``form_def``, ``study_event_def`` (value is ``None`` if not set).
        """
        return {
            "study": self._current_study,
            "mdv": self._current_mdv,
            "item_group_def": self._current_igd,
            "item_def": self._current_item_def,
            "form_def": self._current_form_def,
            "study_event_def": self._current_sed,
        }

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> Any:
        """Construct and return the top-level ODM object.

        :returns: An ``ODM`` instance containing all added elements.
        """
        M = self._model
        return M.ODM(Study=self._studies, **self._file_attrs)
