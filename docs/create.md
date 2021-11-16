# Creating ODM

This section covers how to create new ODM documents, including extensions like Define-XML, using odmlib.

## Creating the ODM Element

Let’s start by creating the ODM root element as an odmlib object. To create the root object, the object name is the same as the element name 
and the attributes are set as part of object creation:

```python
import odmlib.odm_1_3_2.model as ODM
root = ODM.ODM(
	FileOID="ODM.DEMO.001", 
	Granularity="Metadata", 
	AsOfDateTime=current_datetime, 
	CreationDateTime=current_datetime, 
	ODMVersion="1.3.2", 
	FileType="Snapshot", 
	Originator="Hume Data Labs", 
	SourceSystem="odmlib", 
	SourceSystemVersion="0.1"
)
```

The ODM element in odmlib matches the the attribute name and data types defined in the ODM 1.3.2 specification. At a minimum the required attributes must be instantiated to create the ODM object. Once created the ODM child elements can be created and added. The ODM object is defined in the odm_1_3_2/model.py file. Other models, such as define_2_1, are also availble in the odmlib package. Within the odm_1_3_2 model you will find the formal definition for all the classes, including ODM, as shown below.

```python
class ODM(OE.ODMElement):
    Description = T.String(required=False)
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    Archival = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    PriorFileOID = T.OIDRef(required=False)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    schemaLocation = T.String(required=False, namespace="xs")
    ID = T.ID()
    Study = T.ODMListObject(element_class=Study)
    AdminData = T.ODMListObject(element_class=AdminData)
    ReferenceData = T.ODMListObject(element_class=ReferenceData)
    ClinicalData = T.ODMListObject(element_class=ClinicalData)
    Association = T.ODMListObject(element_class=Association)
```

The ValueSetString type is defined in odmlib and describes the valid values for the attribute. These are the same as described in the ODM 1.3.2 specification.

## Creating ODM Child Elements

Elements are defined as ODMObject, or if element is a list as ODMListObject. Elements are instantianted as objects and added to the parent object. The following example shows the creation and addition of the Study object to the root object, created as the ODM object above. The Study child element is created and appended to the Study list, as study is defined as an ODMListObject. Since order matters in the ODM XML schema, objects should be added in the order that's reflected in the model. For example, the Study element is created next and appended to ODM as follows:

```python
root.Study.append(ODM.Study(OID="ODM.GET.STARTED"))
```

A Study object is created with the OID set to “ODM.GET.STARTED” and appended to root.Study. When there can be multiple instances of an element, as is the case with Study, use a list to represent that element. The ODM standard specifies that there can be 0 or more Study elements under the parent ODM element, as shown below:

```
ODM(Study*, AdminData*, ReferenceData*, ClinicalData*, ...)
```

Follow this same approach to create the rest of the objects needed to complete your ODM document. Keep in mind the order in which you add elements should match the order in the ODM specification. For example:

```python
root.Study[0].GlobalVariables = ODM.GlobalVariables()
root.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="Get Started with ODM XML")
root.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="Getting started with odmlib")
root.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="ODM XML Get Started")
```

Notice that because the Study object is a list you need to reference the specific Study object in the list, typically the first Study. Objects like StudyName are not lists, so just set the StudyName object to the instantiated ODM.StudyName object. Notice that StudyName does not have any attributes and in XML represents the content in the Body, or text, of the XML element. In these cases, the \_content attribute is used to represent content that the ODM specification shows as in the Body of the element. 

## Another Object Creation Example

All the objects in the ODM model are fundamentally created the same way and follow the definition specified in the odm_1_3_2 model. This next example demonstrates creating a MethodDef objects.

```python
attrs = {"OID": "ODM.MT.AGE", "Name": "Algorithm to derive AGE", "Type": "Computation"}
methoddef = ODM.MethodDef(**attrs)
methoddef.Description = ODM.Description()
methoddef.Description.TranslatedText.append(ODM.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en"))
methoddef.FormalExpression.append(ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')"))
```

Before this MethodDef object can be added to the root ODM object created above, we need to create the MetaDataVersion object. Once created we can add the MethodDef object to it.

```python
root.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(OID="MDV.TRACE-XML-ODM-01", Name="TRACE-XML MDV", Description="Trace-XML Example"))
root.Study[0].MetaDataVersion[0].MethodDef.append(methoddef)
```

This basic process is repeated to complete building the ODM file keeping in mind that proper ordering of the elements matters.

## Creating the ODM File

Once all the content has been created, the ODM file can be generated as XML and written to a file as follows:

```python
root.write_xml("./data/simple_create.xml")
```
If you want to generate JSON instead of XML, root can be serialized as JSON as follows:

```python
root.write_json("./data/simple_create.json")
```

