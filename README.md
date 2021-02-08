# odmlib

## Introduction
The odmlib package simplifies working with the CDISC ODM data exchange standard and its extensions, such as 
Define-XML, in Python. The odmlib package provides an object-oriented interface to working with ODM documents
that simplifies creating and processing them. It supports serializations in XML and JSON. DOM models have been 
created for ODM 1.3.2 and Define-XML versions 2.0 and 2.1. An ODM v2.0 draft will be delivered once the
draft specification has been completed. Odmlib simplifies the act of creating propriety extensions and
automatically serializing them as XML or JSON. Odmlib also supports conformance checks and schema validation
to ensure quality and standards compliance.

## Getting Started
Since odmlib is still in development it has not yet been posted to PyPi, though ultimately the plan is to do
so. For those interested in getting involved with odmlib early, the best way to proceed is to clone the odmlib 
repository, switch to the odmlib directory, and run 

`python setup.py install` 

Alternatively, for those that may want to contribute to the development of odmlib, run

`python setup.py develop`

For those running PyCharm, here are the steps to install odmlib for development:
1. switch to venv\scripts
2. run activate.bat
3. switch to odmlib directory
4. run: python setup.py develop

Once the production version has been completed, it will be released as a PyPi package.

## Example Code
Example code is available in the [odmlib_examples repository] (https://github.com/swhume/odmlib_examples) 
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
the metadata sections complete. 