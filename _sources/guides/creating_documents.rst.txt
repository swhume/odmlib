Creating ODM Documents
======================

odmlib uses a **bottom-up** construction pattern: create leaf elements
first, then pass them to parent elements.

Basic ODM 1.3.2 Document
--------------------------

.. code-block:: python

    import odmlib.odm_1_3_2.model as ODM
    import odmlib.ns_registry as NS

    # Step 1: Set up namespaces
    NS.NamespaceRegistry(prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True)

    # Step 2: Build global variables
    gv = ODM.GlobalVariables(
        StudyName=ODM.StudyName(_content="Vital Signs Study"),
        StudyDescription=ODM.StudyDescription(_content="VS collection study"),
        ProtocolName=ODM.ProtocolName(_content="VS-001"),
    )

    # Step 3: Create metadata
    mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Version 1")

    # Step 4: Create item definitions
    age_item = ODM.ItemDef(
        OID="IT.AGE", Name="Age", DataType="integer", Length=3
    )
    mdv.ItemDef.append(age_item)

    # Step 5: Create item group definition
    dm_igd = ODM.ItemGroupDef(OID="IG.DM", Name="Demographics", Repeating="No")
    dm_igd.ItemRef.append(ODM.ItemRef(
        ItemOID="IT.AGE", Mandatory="Yes", OrderNumber=1
    ))
    mdv.ItemGroupDef.append(dm_igd)

    # Step 6: Assemble study and ODM root
    study = ODM.Study(OID="S.001", GlobalVariables=gv, MetaDataVersion=[mdv])
    odm = ODM.ODM(
        FileOID="F.001",
        FileType="Snapshot",
        CreationDateTime="2024-01-15T12:00:00",
        Study=[study]
    )

    # Step 7: Write to file
    odm.write_xml("study.xml")
    odm.write_json("study.json")

Adding Code Lists
-----------------

.. code-block:: python

    # Create a code list for Sex
    decode_m = ODM.Decode(
        TranslatedText=[ODM.TranslatedText(_content="Male", lang="en")]
    )
    decode_f = ODM.Decode(
        TranslatedText=[ODM.TranslatedText(_content="Female", lang="en")]
    )
    cl_sex = ODM.CodeList(OID="CL.SEX", Name="Sex", DataType="text")
    cl_sex.CodeListItem.append(ODM.CodeListItem(CodedValue="M", Decode=decode_m))
    cl_sex.CodeListItem.append(ODM.CodeListItem(CodedValue="F", Decode=decode_f))
    mdv.CodeList.append(cl_sex)

    # Reference the code list from an item
    sex_item = ODM.ItemDef(OID="IT.SEX", Name="Sex", DataType="text", Length=1)
    sex_item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.SEX")
    mdv.ItemDef.append(sex_item)

Adding Descriptions
-------------------

Most elements accept an optional ``Description`` child with translated text:

.. code-block:: python

    tt = ODM.TranslatedText(_content="Subject age in years", lang="en")
    desc = ODM.Description(TranslatedText=[tt])
    age_item.Description = desc

Using the Builder API
---------------------

odmlib also provides a fluent builder API for common construction patterns:

.. code-block:: python

    from odmlib.builder import ODMBuilder

    builder = ODMBuilder()
    odm = (builder
        .odm(FileOID="F.001", FileType="Snapshot",
             CreationDateTime="2024-01-01T00:00:00")
        .study(OID="S.001")
        .global_variables("My Study", "A study", "PROT-001")
        .metadata_version(OID="MDV.001", Name="Version 1")
        .build()
    )

Creating a Define-XML 2.1 Document
------------------------------------

.. code-block:: python

    import odmlib.define_2_1.model as DEF
    import odmlib.ns_registry as NS

    NS.NamespaceRegistry(prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="def",
        uri="http://www.cdisc.org/ns/def/v2.1")

    # Define-XML uses a single Study (ODMObject, not list)
    # See the Define-XML 2.1 model for additional attributes

Serialization Options
---------------------

All odmlib elements support multiple output formats:

.. code-block:: python

    # Write XML to file
    odm.write_xml("output.xml")

    # Write JSON to file
    odm.write_json("output.json")

    # Get XML as string
    xml_str = odm.to_xml_string()

    # Get Python dict
    doc_dict = odm.to_dict()

    # Get JSON string
    json_str = odm.to_json()
