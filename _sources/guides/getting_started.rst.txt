Getting Started with odmlib
===========================

odmlib is a Python library for working with CDISC ODM (Operational Data Model)
documents and its extensions. It provides an object-oriented interface for
creating, parsing, and validating ODM files with XML and JSON serialization.

Installation
------------

Install from PyPI::

    pip install odmlib

For development (editable install with all dev tools)::

    git clone https://github.com/swhume/odmlib.git
    cd odmlib
    pip install -e ".[dev]"

Supported Standards
-------------------

.. list-table::
   :header-rows: 1

   * - Standard
     - Package
     - Status
   * - ODM 1.3.2
     - ``odmlib.odm_1_3_2``
     - Stable
   * - ODM 2.0
     - ``odmlib.odm_2_0``
     - Draft
   * - Define-XML 2.0
     - ``odmlib.define_2_0``
     - Stable
   * - Define-XML 2.1
     - ``odmlib.define_2_1``
     - Stable
   * - Dataset-XML 1.0.1
     - ``odmlib.dataset_1_0_1``
     - Stable
   * - CT-XML 1.1.1
     - ``odmlib.ct_1_1_1``
     - Stable

Quick Start
-----------

Loading an ODM-XML File
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD

    # Create a loader for ODM 1.3.2 XML
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
    loader.open_odm_document("my_study.xml")

    # Get the root ODM object
    odm = loader.root()
    print(f"File OID: {odm.FileOID}")

    # Get the first MetaDataVersion
    mdv = loader.MetaDataVersion()

    # List all item groups (datasets/domains)
    for igd in mdv.ItemGroupDef:
        print(f"  {igd.OID}: {igd.Name}")

Creating an ODM Document from Scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.odm_1_3_2.model as ODM
    import odmlib.ns_registry as NS

    # Set up the namespace registry
    NS.NamespaceRegistry(prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True)

    # Build the study name and global variables
    sn = ODM.StudyName(_content="My Clinical Study")
    sd = ODM.StudyDescription(_content="A phase II clinical trial")
    pn = ODM.ProtocolName(_content="STUDY-001")
    gv = ODM.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)

    # Create an item definition
    item = ODM.ItemDef(OID="IT.AGE", Name="Age", DataType="integer", Length=3)

    # Create an item group definition
    igd = ODM.ItemGroupDef(OID="IG.DM", Name="Demographics", Repeating="No")
    igd.ItemRef.append(ODM.ItemRef(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1))

    # Assemble the metadata version
    mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Version 1")
    mdv.ItemGroupDef.append(igd)
    mdv.ItemDef.append(item)

    # Create the study and ODM root
    study = ODM.Study(OID="S.001", GlobalVariables=gv, MetaDataVersion=[mdv])
    odm = ODM.ODM(
        FileOID="F.001",
        FileType="Snapshot",
        CreationDateTime="2024-01-01T00:00:00",
        Study=[study]
    )

    # Write to XML
    odm.write_xml("my_study.xml")

Key Concepts
------------

**Bottom-up construction**: ODM objects are built from leaves to root.
Create child elements first, then pass them to parent constructors.

**Descriptor validation**: All attribute assignments are validated at
assignment time. Invalid values raise
:exc:`~odmlib.exceptions.OdmlibTypeError` or
:exc:`~odmlib.exceptions.OdmlibValidationError`.

**Namespace management**: Use :class:`~odmlib.ns_registry.NamespaceRegistry`
to register XML namespaces before creating or loading documents. Call
:meth:`~odmlib.ns_registry.Borg.reset` to clear namespace state between
independent operations.

**Bidirectional serialization**: All elements support :meth:`~odmlib.odm_element.ODMElement.to_xml`,
:meth:`~odmlib.odm_element.ODMElement.to_json`, and
:meth:`~odmlib.odm_element.ODMElement.to_dict` for conversion back to
standard formats.

Next Steps
----------

* :doc:`reading_documents` -- Load and navigate existing ODM documents
* :doc:`creating_documents` -- Build ODM documents from scratch
* :doc:`validation` -- Validate ODM documents
* :doc:`model_reference` -- Understand the supported models and standards
