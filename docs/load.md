# Loading ODM

This section covers how to load existing ODM documents, including extensions like Define-XML, into odmlib so that they can be processed, extended, and validated.

## Using Models

You will be loading ODM-based content into a model such as ODM v1.3.2, Define-XML v2.1, or CT-XML v1.1. You'll need to import the appropriate loader module. For example, to load an ODM v1.3.2 file import the general loader.

```python
from odmlib import loader as LO
```

The next step is to import the load module that's specific to the extension and format of the document. For example, there are separate loaders for base ODM and for Define-XML. For ODM and Define-XML, there are loaders for XML and JSON serializations. To load an XML ODM v1.3.2 file, import the following:

```python
from odmlib import odm_loader as OL
```

The next step is to instantiate the loader and load the XML ODM file. The XML loader takes two parameters: model_package and ns_uri. The model_package is the name of the odmlib model package and the ns_uri is the namespace URI.  

```python
loader =  LO.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
```

By default, the ODM loaders will be configured for ODM v1.3.2 (if you omit model_package and ns_uri).

To load a JSON ODM file, you import and specify the JSON ODM loader as follows:

```python
loader =  LO.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2")
```

JSON does not use namespaces so no need to specify the ns_uri.

Follow a similar process to load a Define-XML v2.1 document. In this case, a Define-XML loader is passed to the ODMLoader as follows:

```python
from odmlib import define_loader as OL
loader =  LO.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
```

## Loading an ODM File

Once the model and loaders have been specified, the next step is to load the file and instantiate the odmlib model with its content. The following example shows loading the document, retrieving the MetaDataVersion object, and printing all the forms.

```python
loader =  LO.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2", ns_uri="http://www.cdisc.org/ns/odm/v1.3"))
odm = loader.open_odm_document(odm_filename)
mdv = loader.MetaDataVersion()
for form in mdv.FormDef:
	print(f"FormDef OID = {form.OID} with Name = {form.Name}")
```

Loading a Define-XML file works the same way.

```python
loader =  LO.ODMLoader(OL.XMLDefineLoader(model_package="define_2_1", ns_uri="http://www.cdisc.org/ns/def/v2.1"))
odm = loader.open_odm_document(define_filename)
mdv = loader.MetaDataVersion()
for igd in mdv.ItemGroupDef:
	print(f"ItemGroupDef OID = {igd.OID} with Name = {igd.Name}")
```

## Referencing Objects

Objects are referenced by their case-sensitive name in the model. Referencing the odmlib model package provides the names and types. The names follow the name provided in the standards specification. Object attributes, such as ItemGroupDef OID, are always single values. Elements may have 1 object or a list of objects. For example, the FormDef element definition from the ODM v1.3.2 odmlib package below show how it is defined by a set of attributes and objects.
Objects are defined as T.ODMObject or T.ODMListObject, where ODMObject can have 1 instance and ODMListObjects represent a list of object instances. This mirrors the defintions in the ODM v1.3.2 standard specification.

```python
class FormDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    ArchiveLayout = T.ODMListObject(element_class=ArchiveLayout)
    Alias = T.ODMListObject(element_class=Alias)
```

Reference the OID for the first form defined in an ODM file using FormDef[0].OID, as is shown in the following example:

```python
mdv = loader.MetaDataVersion()
print(f"the OID for the first form is {mdv.FormDef[0].OID}")
```

Reference the text in the Description of the second form using the following code:

```python
print(f"the description text for the second form is {mdv.FormDef[1].Description.TranslatedText[0]._content}")
```

Notice that Desription has a TranslatedText child object that is a list. Also, notice that TranslatedText maintains its value in the element text, so to reference that odmlib uses the underscore content attribute. The following example shows how to reference the xml:lang attribute. Notice that the xml namespace prefix is not used. Namespaces are registed in the model and are not used when working with odmlib objects.


```python
print(f"the language for the translated text for the second form is {mdv.FormDef[1].Description.TranslatedText[0].lang}")
```

## Adding New Objects

To add a new object into an existing ODM document, create the new object and append it to the list element. The following example shows creating a new FormDef object and then adding ItemGroupRef objects. For forms that already exist, appending a new ItemRef follows a similar process. The example shows creating the ItemGroupRef and appending it to the FormDef ItemGroupRef object list. 

```python
fd = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs Form", Repeating="Yes")
fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1))
fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
fd.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
```

## Finding Objects

In addition to working with objects in lists, you can also retrieve objects by an attribute, such as the OID or Name. For example, the following snippet shows how to find an ItemRef Name based on a specified OID:

```python
for igd in mdv.ItemGroupDef:
	ir = igd.find("ItemRef", "ItemOID", item.OID)
   	if ir:
    	return igd.Name
```

Find works on any list element. Provide the name of the element you want to search across, an attribute of that element, and the value of the attribute. In the above example, find runs on each ItemGroupDef to return an ItemRef that has the ItemOID that matches item.OID.

## Validating the XML

Prior to loading an XML ODM document, validating it for conformance to the standard can help ensure the document can be processed by tools like odmlib. The odmlib package provides feature for performing schema validation and other conformance checks. The odm_parser module must be imported and the relevant ODM XML schemas must be available to perform the validation. The following example demonstrates how to schema validate the ODM XML file.

```python
from odmlib import odm_parser as P
import xmlschema as XSD
validator = P.ODMSchemaValidator(schema_file)
try:
    validator.validate_file(odm_file)
    print("ODM XML schema validation completed successfully...")
except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ve:
    print(f"schema validation errors: {ve}")
```
