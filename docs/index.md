# Welcome to odmlib

## Introduction

The odmlib package simplifies working with the CDISC ODM data exchange standard and its extensions, such as Define-XML, in Python. The odmlib package provides an object-oriented interface for working with ODM documents that simplifies creating and processing them. It supports serializations in XML and JSON. ODM models have been created for ODM 1.3.2, Define-XML versions 2.0 and 2.1, and CT 1.1.1. Odmlib simplifies the act of creating propriety extensions and automatically serializing them as XML or JSON. Odmlib also supports conformance checks and schema validation to ensure quality and standards compliance. [See my blog for posts](https://swhume.github.io/blog-home.html) on odmlib and [odmlib example programs](https://github.com/swhume/odmlib_examples).

## Table of Contents

- [Getting Started](#getting-started)
- [Validating Content](./validate.html)

## Getting Started

Although odmlib is still under development, a version of odmlib is available on PyPI. Although not the most up-to-date, it’s the easiest to install:
```
pip install odmlib
```

Alternatively, for those that may want to contribute to the development of odmlib, run:
```
python setup.py develop
```

For those running PyCharm on Windows, here are the steps to install odmlib for development:

1. switch to venv\scripts
2. run activate.bat
3. switch to odmlib directory
4. run: python setup.py develop

When running PyCharm on Linux:

1. switch to venv/bin
2. run activate (set permissions if needed)
3. switch to odmlib directory
4. run: python setup.py develop

The odmlib package requires that some packages be installed:

- validators
- pathvalidate
- cerberus

## Example Code

Example code is available in the [odmlib_examples repository](https://github.com/swhume/odmlib_examples) that demonstrate ways to use odmlib. 

Selected examples include:
* get_started: a basic example that shows how to create and process a basic ODM metadata file
* xlsx2define2-1: generates a Define-XML v2.1 file from a metadata spreadsheet
* define2-1-to-xlsx: generates a metadata spreadsheet from a Define-XML v2.1 file
* ct2odm: generates a CT-XML ODM file from the delimited text files format of the CDISC Controlled Terminology
* ct2json: a small example that shows how to convert CDISC Controlled Terminology files in ODM to JSON
* xls2define: generates a Define-XML v2.0 file from a metadata spreadsheet
* define2xls: generates a metadata spreadsheet from a Define-XML v2.0 file
* merge_odm: simple merge application that generates a target ODM file with a CRF moved from a source ODM file

## Creating Your First Application

Let’s start by creating the ODM root element. To create the root object, the object name is the same as the element name 
and the attributes are set as part of object creation:

```python
root = ODM.ODM(
	FileOID="ODM.DEMO.001", 
	Granularity="Metadata", 
	AsOfDateTime=current_datetime, CreationDateTime=current_datetime, 
	ODMVersion="1.3.2", 
	FileType="Snapshot", 
	Originator="Hume Data Labs", 
	SourceSystem="odmlib", 
	SourceSystemVersion="0.1"
)
```

Now the variable root is set to the ODM object. All that remains is to create the child elements by instantiating and appending them in the right order. For example, the Study element is created next and appended to ODM as follows:

```python
root.Study.append(ODM.Study(OID="ODM.GET.STARTED"))
```

A Study object is created with the OID set to “ODM.GET.STARTED” and appended to root.Study. When there can be multiple instances of an element, as is the case with Study, use a list to represent that element. The ODM standard specifies that there can be 0 or more Study elements under the parent ODM element, as shown below:

```
ODM(Study*, AdminData*, ReferenceData*, ClinicalData*, ...)
```

Follow this same approach to create the rest of this simple ODM file. Keep in mind the order in which you add elements should match the order in the ODM specification. For example:

```python
root.Study[0].GlobalVariables = ODM.GlobalVariables()
root.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="Get Started with ODM XML")
root.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Getting started with odmlib")
root.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="ODM XML Get Started")
```

This basic process is repeated to complete building the ODM file. Once all the content has been created, the ODM file can be generated as XML and written to a file as follows:

```python
root.write_xml("./data/simple_create.xml")
```
If you want to generate JSON instead of XML, root can be serialized as JSON as follows:

```python
root.write_json("./data/simple_create.json")
```

Now you’ve got an ODM XML file. You can find a more complete version of this [simple example in my gists](https://gist.github.com/swhume/ef8ca0385a706c344eec83dac34a1359).

Although this was a very basic example, it highlights how odmlib simplifies creating ODM documents, including extensions like Define-XML, in Python.

## Why odmlib?

The odmlib package satisfies my interest in working with ODM using an object-oriented interface in Python.

## Limitations
The odmlib package is still in development. Although odmlib supports all of ODM more work remains 
to complete all features for processing ClinicalData. The initial focus has been on getting 
the metadata sections complete. Other limitations include:

* No support for ItemData[Type]. This could easily be added, but the default ODM v1.3.2 model packaged with
  odmlib does not include ItemData[Type]. ItemData[Type] will be deprecated in ODM v2.0.
* No support for ds:Signature. This can also be added if needed.
* The plan is to generate the oid def/ref checks dynamically. The first cut have been developed manually. Until
  the code to generate the checks dynamically is written, the checks must be manually created for each new model.
* The odm_loader returns the first MetaDataVersion by default, but can be set to return others. It does not return 
  a list.

## Future

* Additional testing will be done for ClinicalData and a Dataset-XML model will be created.
* An ODM v2.0 model will be delivered once the draft specification has been completed.
