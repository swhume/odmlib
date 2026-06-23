Model Reference
===============

odmlib provides Python model packages for each supported CDISC standard.
Select the appropriate package based on the document type you are working with.

Available Model Packages
-------------------------

.. list-table::
   :header-rows: 1

   * - Package
     - Standard
     - Loader
     - Notes
   * - ``odmlib.odm_1_3_2``
     - ODM 1.3.2
     - :class:`~odmlib.odm_loader.XMLODMLoader`, :class:`~odmlib.odm_loader.JSONODMLoader`
     - Primary stable model
   * - ``odmlib.odm_2_0``
     - ODM 2.0 (draft)
     - :class:`~odmlib.odm_loader.XMLODMLoader` with ``model_package="odm_2_0"``
     - Draft implementation
   * - ``odmlib.define_2_0``
     - Define-XML 2.0
     - :class:`~odmlib.define_loader.XMLDefineLoader`, :class:`~odmlib.define_loader.JSONDefineLoader`
     - Regulatory submission metadata
   * - ``odmlib.define_2_1``
     - Define-XML 2.1
     - :class:`~odmlib.define_loader.XMLDefineLoader` with ``model_package="define_2_1"``
     - Current Define-XML version
   * - ``odmlib.dataset_1_0_1``
     - Dataset-XML 1.0.1
     - :class:`~odmlib.odm_loader.XMLODMLoader` with ``model_package="dataset_1_0_1"``
     - Tabular dataset transmission
   * - ``odmlib.ct_1_1_1``
     - CT-XML 1.1.1
     - :class:`~odmlib.odm_loader.XMLODMLoader` with ``model_package="ct_1_1_1"``
     - Controlled terminology

ODM 1.3.2 Model Structure
--------------------------

The ODM 1.3.2 model follows the CDISC ODM specification hierarchy:

.. code-block:: text

    ODM
    └── Study
        ├── GlobalVariables (StudyName, StudyDescription, ProtocolName)
        ├── BasicDefinitions (MeasurementUnit)
        └── MetaDataVersion
            ├── Protocol
            │   └── StudyEventRef (links to StudyEventDef)
            ├── StudyEventDef
            │   └── FormRef (links to FormDef)
            ├── FormDef
            │   └── ItemGroupRef (links to ItemGroupDef)
            ├── ItemGroupDef
            │   └── ItemRef (links to ItemDef)
            ├── ItemDef
            │   └── CodeListRef (links to CodeList)
            ├── CodeList (CodeListItem / EnumeratedItem)
            ├── ConditionDef
            ├── MethodDef
            └── Presentation

ODM 2.0 Key Differences
------------------------

ODM 2.0 uses a flatter structure and adds workflow support:

- :class:`~odmlib.odm_2_0.model.StudyEventDef` directly contains
  :class:`~odmlib.odm_2_0.model.ItemGroupRef` (no FormDef/FormRef layer)
- New :class:`~odmlib.odm_2_0.model.WorkflowDef` and
  :class:`~odmlib.odm_2_0.model.WorkflowRef` elements
- :class:`~odmlib.odm_2_0.model.Study` has ``StudyName`` and
  ``ProtocolName`` as string attributes (not child elements)
- Timing elements: :class:`~odmlib.odm_2_0.model.AbsoluteTimingConstraint`,
  :class:`~odmlib.odm_2_0.model.RelativeTimingConstraint`, etc.

ODM 2.0 Known Limitations
-------------------------

The ODM 2.0 model is a draft. v0.2.0 aligned it with the ODM 2.0 XSD for the
core CRF/dataset metadata subset (``TranslatedText/@Type`` is now required
with a builder default, duplicate ``Arm``/``CheckValue`` removed, 12 missing
value-set keys added, permissive mode can bypass an unregistered value set).
Five **structural** features remain deferred to v0.2.1 and produce
schema-invalid output if used under ``model_package="odm_2_0"``:

- :class:`~odmlib.odm_2_0.model.ConditionDef` lacks the XSD-required
  ``MethodSignature`` child (and required ``Description``) --
  :meth:`~odmlib.builder.ODMBuilder.add_condition_def` is unsafe for ODM 2.0.
- :class:`~odmlib.odm_2_0.model.FormalExpression` is text-based; the XSD is
  element-based (``Code | ExternalCodeLib``) -- do not pass
  ``formal_expression`` to :meth:`~odmlib.builder.ODMBuilder.add_method_def`
  for ODM 2.0.
- :class:`~odmlib.odm_2_0.model.Protocol` carries ``StudyEventRef``, removed
  in the ODM 2.0 schema -- :meth:`~odmlib.builder.ODMBuilder.add_study_event_ref`
  is unsafe for ODM 2.0.
- ``MetaDataVersion.StudyTiming`` placement (the XSD puts timing under
  ``Protocol/StudyTimings``).
- :class:`~odmlib.odm_2_0.model.StudyEventGroupDef` cannot satisfy its
  required ``(StudyEventGroupRef?, StudyEventRef?)`` child group.

The :class:`~odmlib.odm_2_0.model.ItemDef` attribute-set alignment (drop
``FractionDigits`` / ``DatasetVarName`` / ``SDSVarName``, add
``DisplayFormat`` / ``VariableSet``) landed in v0.2.1; its XSD
``ItemDef/ValueListRef`` child element remains deferred.

See the ROADMAP "v0.2.1 -- ODM v2.0 Model/XSD Alignment" section and
``ODM20-MODEL-XSD-DIFFERENCES_PLAN.md`` for full detail and the schema-valid
safe-subset workaround.

Define-XML Extensions
---------------------

Define-XML extends ODM 1.3.2 with regulatory submission metadata:

**New elements in Define-XML 2.1:**

- :class:`~odmlib.define_2_1.model.ValueListDef` -- permissible value lists
- :class:`~odmlib.define_2_1.model.WhereClauseDef` -- filtering conditions
- :class:`~odmlib.define_2_1.model.CommentDef` -- annotation definitions
- :class:`~odmlib.define_2_1.model.Standards` / :class:`~odmlib.define_2_1.model.Standard`
  -- CDISC standard references (e.g., SDTM, ADaM)
- :class:`~odmlib.define_2_1.model.leaf` -- external document references

**Extended elements** (additional attributes):

- :class:`~odmlib.define_2_1.model.ItemGroupDef` -- adds ``Structure``,
  ``ArchiveLocationID``, ``CommentOID``, ``StandardOID``, ``HasNoData``
- :class:`~odmlib.define_2_1.model.ItemDef` -- adds ``DisplayFormat``,
  ``CommentOID``, ``Origin``, ``ValueListRef``
- :class:`~odmlib.define_2_1.model.MetaDataVersion` -- adds ``DefineVersion``,
  ``Standards``, ``ValueListDef``, ``WhereClauseDef``, ``CommentDef``

Selecting the Right Loader
---------------------------

.. code-block:: python

    import odmlib.loader as LD
    import odmlib.odm_loader as OL
    import odmlib.define_loader as DL

    # ODM 1.3.2 XML
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))

    # ODM 2.0 XML
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))

    # Define-XML 2.1 XML
    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))

    # Define-XML 2.0 JSON
    loader = LD.ODMLoader(DL.JSONDefineLoader(model_package="define_2_0"))

    # Dataset-XML 1.0.1
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="dataset_1_0_1"))

Creating Custom Extensions
---------------------------

To create a proprietary ODM extension:

1. Create a new model module importing the base model
2. Subclass existing elements to add new attributes/elements
3. Register any new namespaces
4. Use ``local_model=True`` with the full module path

.. code-block:: python

    # myext/model.py
    import odmlib.odm_1_3_2.model as ODM
    import odmlib.typed as T
    import odmlib.ns_registry as NS

    NS.NamespaceRegistry(prefix="myext", uri="http://example.com/myext")

    class ItemDef(ODM.ItemDef):
        CustomAttr = T.String(namespace="myext")

    # Load using local_model
    loader = LD.ODMLoader(OL.XMLODMLoader(
        model_package="myext",
        local_model=True
    ))
