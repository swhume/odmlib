# Validate ODM

This section covers how to create validate and run basic conformance checks on ODM documents, including extensions like Define-XML, using odmlib.

## Validating the XML

Prior to loading an XML ODM document, validating it for conformance to the standard can help ensure the document can be processed by tools like odmlib. The odmlib package provides feature for performing schema validation and other conformance checks. The odm_parser module must be imported and the relevant ODM XML schemas must be available to perform the validation. The xmlschema module should be imported when you want to work with the exceptions. The following example demonstrates how to schema validate the ODM XML file.

```python
from odmlib import odm_parser as P
import xmlschema as XSD
validator = P.ODMSchemaValidator(schema_file)
try:
    validator.validate_file(odm_file)
except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
    print(f"schema validation errors: {ve}")
else:
    print("ODM XML schema validation completed successfully...")
```

In addition to validating a file, you can also validate the tree after a file has been parsed. 

```python
import odmlib.odm_parser as P
validator = P.ODMSchemaValidator(schema_file)
odm_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cdash-odm-test.xml')
parser = P.ODMParser(odm_file)
tree = parser.parse_tree()
is_valid = validator.validate_tree(tree)
```

A useful variant of this is to validate an ODM string.

```python
import odmlib.odm_parser as P
validator = P.ODMSchemaValidator(schema_file)
with open(odm_file, "r", encoding="utf-8") as f:
    odm_string = f.read()
parser = P.ODMStringParser(odm_string)
tree = parser.parse_tree()
is_valid = validator.validate_tree(tree)
```

## Verifying OIDs

Beyond schema validation, odmlib adds OID checking. The verify_oids method can be executed on any ODM element and recursivley checks the OIDs for uniqueness and checks that ever OIDRef has an associated Def.

```python
import odmlib.odm_1_3_2.rules.oid_ref as OID
mdv = ODM.MetaDataVersion(**attrs)
# add additiona elements into MetaDataVersion...
oid_checker = OID.OIDRef()
try:
    # checks for non-unique OIDs and runs the ref/def check
    mdv.verify_oids(oid_checker)
except ValueError as ve:
    print(f"Error verifying OIDS. {ve}")
else:
    print(f"OIDs successfully verified.")
```

The check_unreferenced_oids method checks for Def elements that have not been referenced elsewhere in the ODM. The verify_oids check must be run before the check_unreferenced_oids as the verify_oids method recursively builds the data structures needed to identify the missing OIDs. This method returns a list of unreferenced OIDs.

```python
import odmlib.odm_1_3_2.rules.oid_ref as OID
oid_checker = OID.OIDRef()
mdv.verify_oids(oid_checker)
orphans = oid_checker.check_unreferenced_oids()
```

## Verifying Order

Odmlib does prevent you from adding a child to an invalid parent. That is, it will prevent you from creating or adding an object type to the wrong parent. Odmlib does not enforce object ordering. The ODM schema enforces element order. For example, FormDef elements must come before ItemGroupDefs elements. Odmlib can test for element order, and can re-order elements. The following example shows testing elements:

```python
study = ODM.Study(OID="ST.001.Test")
# add elements to the Study element...
try:
    study.verify_order()
except ValueError as ve:
    print(f"Error verifying element order. {ve}")
else:
    print(f"Study element order is verified.")
```

The verify_order method recursivley checks the elements and it's children to ensure the element order matches the model. Odmlib does include the ability to re-order the elements to match the model, but this method is not recursive at this time. A recursive re-ordering of elements may be added in a future release. The following example demonstrates re-ordering an ItemDef element where the elements were added in the wrong order:

```python
itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
itd.Description = ODM.Description()
itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
itd.Question = ODM.Question()
itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
itd.reorder_object()
```

## Conformance Checking Objects

As an odmlib is being created it may be useful to check the conformance of individual objects or sub-trees of the overall ODM document. If ODM is being used in the context of an API where individual elements are being created or updated, testing those elements for conformance may be useful. Often these individual elements or sub-trees would not pass full ODM schema validation without being part of a complete ODM document. This method of conformance checking uses Cerberus to check objects that have been serialized as a Python dictionary, as is demonstrated in the following example:

```python
method = ODM.MethodDef(**attrs)
method.Description = ODM.Description()
method.Description.TranslatedText.append(ODM.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en"))
method.FormalExpression.append(ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')"))
is_valid = validator.verify_conformance(method.to_dict(), "MethodDef")
```

## Using the odmlib Type System to Validate Input

The model created for the ODM 1.3.2 standard consists of classes comprised of typed content. When creating these objects, odmlib will test for required and valid attribute types as specified in the standard specification. It also tests types that include enumerated value domains, or code lists, for valid content. Objects can be created without all required elements, as they may be added after the object is created. The following example will generate an exception since the required Mandatory attribute is missing from the ItemGroupRef object.

```python
try:
    # missing required attribute Mandatory generates a ValueError exception
    igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", OrderNumber=1)
except ValueError as te:
    print(f"Error creating ItemGroupDef: {te}")
```

The following example will generate an exception because the data type for OrderNumber is not an interger or a string that can be converted to an integer.

```python
try:
    # invalid OrderNumber data type generates a TypeError exception
    igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber="Yes")
except TypeError as te:
    print(f"Error creating ItemGroupDef: {te}")
```
