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
   * - ``odmlib.arm_1_0``
     - ARM 1.0
     - :class:`~odmlib.arm_loader.XMLArmLoader`, :class:`~odmlib.arm_loader.JSONArmLoader`
     - Analysis Results Metadata; extends Define-XML 2.1

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

The ODM 2.0 model is a draft, but every **metadata** element the ODM 2.0 XSD
defines is now modelled. ``tests/test_odm_2_0_xsd_alignment.py`` compares the
model against the bundled schema and asserts the divergence set equals a
declared allowlist, so drift cannot be introduced silently. Two areas remain.

**ClinicalData and ReferenceData are not modelled.**
:class:`~odmlib.odm_2_0.model.ODM` has no ``ClinicalData``, ``ReferenceData``
or ``Association`` child, and :class:`~odmlib.odm_2_0.model.Location` has no
``Query``. The 24 elements of that data layer are scoped to v0.3.0; see
``ROADMAP.md``.

**One deliberate approximation** remains, where the XSD says something
odmlib's descriptor model cannot express. It is documented in the class
docstring, and caught by :class:`~odmlib.odm_parser.ODMSchemaValidator` rather
than at build time:

- :class:`~odmlib.odm_2_0.model.FormalExpression` -- the XSD requires exactly
  one of ``Code`` or ``ExternalCodeLib``. odmlib has no way to express an
  ``xs:choice``, so both children are declared optional; setting neither, or
  both, builds an object odmlib accepts and the schema rejects.

Two former approximations were closed in v0.3.0:

- **Interleaved children keep their order.** Where the XSD lets two child
  types alternate -- :class:`~odmlib.odm_2_0.model.ItemGroupDef`
  (``ItemGroupRef``/``ItemRef``),
  :class:`~odmlib.odm_2_0.model.StudyEventGroupDef`
  (``StudyEventGroupRef``/``StudyEventRef``) and
  :class:`~odmlib.odm_2_0.model.WorkflowDef` (``Transition``/``Branching``) --
  the two per-type lists are views onto one ordered sequence. A loaded element
  keeps its document order, a child appended to either list goes last, and
  :meth:`~odmlib.odm_element.ODMElement.children` returns the combined order::

      for child in igd.children("ItemRef", "ItemGroupRef"):
          ...

  ODM 2.0 JSON keeps one array per type, so a JSON round trip writes the group
  in model order. See :mod:`odmlib.interleave`.
- **XHTML in TranslatedText is kept.** The XSD types
  :class:`~odmlib.odm_2_0.model.TranslatedText` ``mixed="true"`` with an
  optional ``xhtml:div`` child. The div, and any text after it, is held as one
  markup string in ``TranslatedText.div`` and written back as a real subtree
  with its own XHTML namespace declaration; text before it stays in
  ``_content``. odmlib does not model the XHTML elements inside the div.
  See :mod:`odmlib.xhtml`.

See ``ODM_XSD_ALIGNMENT.md`` for the full model/XSD comparison and the
remaining work.

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
