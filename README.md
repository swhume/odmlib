# odmlib

## Introduction
The odmlib package simplifies working with the CDISC ODM data exchange standard and its extensions, such as 
Define-XML, in Python. The odmlib package provides an object-oriented interface to working with ODM documents
that simplifies creating and processing them. It supports serializations in XML and JSON. ODM models have been 
created for ODM 1.3.2 and Define-XML versions 2.0 and 2.1. An ODM v2.0 draft will be delivered once the
draft specification has been completed. Odmlib simplifies the act of creating propriety extensions and
automatically serializing them as XML or JSON. Odmlib also supports conformance checks and schema validation
to ensure quality and standards compliance.

## Why odmlib?
The odmlib package satisfies my personal interest in working with ODM using an object-oriented 
interface in Python.

## Getting Started
Since odmlib is still in development it has not yet been posted to PyPi, though ultimately the plan is to do
so. For those interested in getting involved with odmlib early, the best way to proceed is to clone the odmlib 
repository, switch to the odmlib directory, and run 

`python setup.py install` 

Alternatively, for those that may want to contribute to the development of odmlib, run

`python setup.py develop`

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

Once the production version has been completed, it will be released as a PyPi package.

The odmlib package requires that some packages be installed:
* validators
* pathvalidate
* cerberus

## Example Code
Example code is available in the [odmlib_examples repository](https://github.com/swhume/odmlib_examples) 
that demonstrate ways to use odmlib. 
Selected examples include:
* get_started: a basic example that shows how to create and process a basic ODM metadata file
* xls2define: generates a Define-XML v2.0 file from a metadata spreadsheet
* define2xls: generates a metadata spreadsheet from a Define-XML v2.0 file
* merge_odm: simple merge application that generates a target ODM file with a CRF moved from a source 
  ODM file

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

