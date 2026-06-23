Working with Dataset-JSON v1.1
================================

odmlib provides a spec-conformant Dataset-JSON v1.1 implementation using the
same ODMElement/descriptor pattern as all other odmlib models.

Creating a Dataset-JSON File
-----------------------------

Build a dataset programmatically and write it to JSON:

.. code-block:: python

    from odmlib.dataset_json_1_1.model import DatasetJSON, Column, SourceSystem

    ds = DatasetJSON(
        datasetJSONCreationDateTime="2024-01-15T12:00:00Z",
        datasetJSONVersion="1.1.0",
        fileOID="FILE.AE.001",
        originator="ACME Pharma",
        sourceSystem=SourceSystem(name="SAS", version="9.4"),
        studyOID="CDISC01",
        metaDataVersionOID="MDV.001",
        itemGroupOID="IG.AE",
        records=0,
        name="AE",
        label="Adverse Events",
    )

    # Add columns
    ds.add_column(Column(itemOID="IT.STUDYID", name="STUDYID",
                         label="Study Identifier", dataType="string",
                         keySequence=1))
    ds.add_column(Column(itemOID="IT.AETERM", name="AETERM",
                         label="Reported Term", dataType="string"))

    # Add rows (auto-increments records)
    ds.add_row(["CDISC01", "Headache"])
    ds.add_row(["CDISC01", "Nausea"])

    # Write to JSON file
    ds.write_json("ae.json")

    # Or write NDJSON (streaming format)
    ds.write_ndjson("ae.ndjson")

Reading a Dataset-JSON File
-----------------------------

.. code-block:: python

    from odmlib.dataset_json_1_1 import DatasetJSON

    # From JSON
    ds = DatasetJSON.read_json("ae.json")
    print(f"Dataset: {ds.name}, Records: {ds.records}")
    print(f"Columns: {ds.column_names}")
    for row in ds.rows:
        print(row)

    # From NDJSON
    ds = DatasetJSON.read_ndjson("ae.ndjson")

    # From a JSON string
    ds = DatasetJSON.from_json('{"datasetJSONVersion": "1.1.0", ...}')

Converting from Dataset-XML
-----------------------------

Convert Dataset-XML 1.0.1 files to Dataset-JSON v1.1 (one file per dataset):

.. code-block:: python

    import odmlib.odm_loader as OL
    import odmlib.loader as LD
    import odmlib.ns_registry as NS
    from odmlib.dataset_json_1_1.converter import dataset_xml_to_dataset_json

    NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
                         is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="data",
                         uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")

    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="dataset_1_0_1",
                          ns_uri="http://www.cdisc.org/ns/Dataset-XML/v1.0"))
    loader.open_odm_document("ae.xml")
    odm = loader.root()

    # Returns dict[str, DatasetJSON] — one per ItemGroupOID
    datasets = dataset_xml_to_dataset_json(odm)
    for name, ds in datasets.items():
        ds.write_json(f"{name.lower()}.json")

Flattening Define-XML v2.1 Metadata
--------------------------------------

Convert Define-XML v2.1 metadata into tabular Dataset-JSON datasets
for analysis or round-tripping:

.. code-block:: python

    import odmlib.define_loader as DL
    import odmlib.loader as LD
    from odmlib.dataset_json_1_1.define_flattener import DefineFlattener

    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1'))
    loader.open_odm_document('define.xml')
    odm = loader.root()

    flattener = DefineFlattener(odm)
    datasets = flattener.flatten_all()  # dict of 11 metadata tables

    # Write all to individual JSON files
    flattener.write_all('/output/dir')

    # Or work with individual datasets
    variables = datasets['variables']
    print(f"Total variables: {variables.records}")

The flattener produces 11 metadata tables:

- **study** — Study-level metadata (1 row)
- **standards** — Standard references
- **datasets** — ItemGroupDef definitions
- **variables** — Variable definitions (ItemRef + ItemDef)
- **value_level** — Value-level metadata (ValueListDef)
- **where_clauses** — Where clause conditions
- **methods** — Computation methods
- **comments** — Comment definitions
- **documents** — External document references
- **codelists** — CodeList definitions
- **codelist_terms** — Individual coded values

Pandas Integration
-------------------

Convert between DataFrames and Dataset-JSON (requires pandas):

.. code-block:: python

    from odmlib.dataframe import (
        dataset_json_to_dataframe,
        dataframe_to_dataset_json,
        define_metadata_to_dataframes,
    )

    # DatasetJSON → DataFrame
    from odmlib.dataset_json_1_1 import DatasetJSON
    ds = DatasetJSON.read_json("dm.json")
    df = dataset_json_to_dataframe(ds)

    # DataFrame → DatasetJSON
    import pandas as pd
    df = pd.DataFrame({"STUDYID": ["CDISC01"], "AGE": [65]})
    ds = dataframe_to_dataset_json(df, "DM", "Demographics", "IG.DM")
    ds.write_json("dm.json")

    # Define-XML → DataFrames (11 metadata tables)
    import odmlib.define_loader as DL
    import odmlib.loader as LD
    loader = LD.ODMLoader(DL.XMLDefineLoader(model_package='define_2_1'))
    loader.open_odm_document('define.xml')
    dfs = define_metadata_to_dataframes(loader.root())
    print(dfs['variables'][['DatasetOID', 'Name', 'DataType']].head())
