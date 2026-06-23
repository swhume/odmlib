Reading ODM Documents
=====================

odmlib supports loading ODM documents from both XML and JSON formats.

Choosing a Loader
-----------------

Select the appropriate loader based on your file format and standard:

.. list-table::
   :header-rows: 1

   * - Format
     - Standard
     - Loader Class
   * - XML
     - ODM 1.3.2
     - :class:`~odmlib.odm_loader.XMLODMLoader`
   * - JSON
     - ODM 1.3.2
     - :class:`~odmlib.odm_loader.JSONODMLoader`
   * - XML
     - Define-XML 2.0 or 2.1
     - :class:`~odmlib.define_loader.XMLDefineLoader`
   * - JSON
     - Define-XML 2.0 or 2.1
     - :class:`~odmlib.define_loader.JSONDefineLoader`
   * - XML
     - ODM 2.0
     - :class:`~odmlib.odm_loader.XMLODMLoader` (with ``model_package="odm_2_0"``)

Choosing a Namespace URI
------------------------

The XML loaders accept an optional ``ns_uri`` argument. When omitted, the
URI is derived from ``model_package``:

.. list-table::
   :header-rows: 1

   * - ``model_package``
     - Default ``ns_uri``
   * - ``odm_1_3_2``
     - ``http://www.cdisc.org/ns/odm/v1.3``
   * - ``odm_2_0``
     - ``http://www.cdisc.org/ns/odm/v2.0``
   * - ``define_2_0``
     - ``http://www.cdisc.org/ns/def/v2.0``
   * - ``define_2_1``
     - ``http://www.cdisc.org/ns/def/v2.1``

You only need to pass ``ns_uri`` explicitly if your document uses a
non-standard URI (for example, a custom extension namespace). Passing an
explicit value overrides the derived default.

.. code-block:: python

    # Just works — ns_uri is derived from model_package
    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))

    # Override only when you need to
    loader = LD.ODMLoader(DL.XMLDefineLoader(
        model_package="define_2_1",
        ns_uri="http://example.com/extensions/v1",
    ))

Loading an ODM-XML File
-----------------------

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD

    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
    loader.open_odm_document("study.xml")

    # Get the root ODM element
    odm = loader.root()
    print(f"File OID: {odm.FileOID}")
    print(f"File Type: {odm.FileType}")

Loading a Define-XML File
--------------------------

.. code-block:: python

    import odmlib.define_loader as DL
    import odmlib.loader as LD

    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
    loader.open_odm_document("define.xml")

    odm = loader.root()
    mdv = loader.MetaDataVersion()

Loading from a String
---------------------

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD

    xml_string = """<?xml version="1.0" encoding="utf-8"?>
    <ODM xmlns="http://www.cdisc.org/ns/odm/v1.3"
         FileOID="F.001" FileType="Snapshot"
         CreationDateTime="2024-01-01T00:00:00">
      <Study OID="S.001">...</Study>
    </ODM>"""

    loader = LD.ODMLoader(OL.XMLODMLoader())
    loader.load_odm_string(xml_string)
    odm = loader.root()

Navigating the Object Tree
---------------------------

After loading, navigate the odmlib object hierarchy using standard
attribute access:

.. code-block:: python

    mdv = loader.MetaDataVersion()  # First MetaDataVersion (idx=0)

    # Iterate over item group definitions
    for igd in mdv.ItemGroupDef:
        print(f"Dataset: {igd.OID} - {igd.Name}")

    # Access a specific element
    study = loader.Study()
    print(study.OID)

Finding Elements by Attribute
------------------------------

Use :meth:`~odmlib.odm_element.ODMElement.find` to find the first
matching element:

.. code-block:: python

    # Find an ItemDef by OID
    item = mdv.find("ItemDef", "OID", "IT.AGE")
    if item:
        print(f"DataType: {item.DataType}")

    # Find an ItemGroupDef by Name
    dm = mdv.find("ItemGroupDef", "Name", "Demographics")

Use :meth:`~odmlib.odm_element.ODMElement.find_all` to get all matches:

.. code-block:: python

    # Find all items with DataType "text"
    text_items = mdv.find_all("ItemDef", "DataType", "text")

Use :meth:`~odmlib.odm_element.ODMElement.find_by` for multi-attribute search:

.. code-block:: python

    item = mdv.find_by("ItemDef", OID="IT.AGE", DataType="integer")

Loading Multiple MetaDataVersions
-----------------------------------

By default, loaders return the first MetaDataVersion. Use the ``idx``
parameter to access others:

.. code-block:: python

    mdv_0 = loader.MetaDataVersion(idx=0)  # First version
    mdv_1 = loader.MetaDataVersion(idx=1)  # Second version

Loading JSON Documents
-----------------------

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD

    loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2"))
    loader.open_odm_document("study.json")
    odm = loader.root()

Converting Loaded Documents
----------------------------

After loading, convert the odmlib object back to other formats:

.. code-block:: python

    # Convert to XML string
    xml_str = odm.to_xml_string()

    # Convert to Python dict
    doc_dict = odm.to_dict()

    # Write to XML file
    odm.write_xml("output.xml")

    # Write to JSON file
    odm.write_json("output.json")

Loading Non-Conformant Documents
---------------------------------

If a document contains invalid or incomplete content, odmlib normally
rejects it at load time.  Use permissive mode to load it anyway for
inspection and repair:

.. code-block:: python

    from odmlib import permissive

    with permissive():
        loader.open_odm_document("broken.xml")
        odm = loader.root()

    # Fix issues in strict mode, then validate
    errors = odm.validate(collect_errors=True)

See :doc:`permissive_loading` for the full guide including graduated
control, the ``ValidationMode`` flags, and the load-fix-validate
workflow.
