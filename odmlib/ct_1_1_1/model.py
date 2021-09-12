import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    lang = T.String(namespace="xml")
    _content = T.String(required=True)


class Alias(OE.ODMElement):
    Context = T.String(required=True)
    Name = T.String(required=True)


class StudyDescription(OE.ODMElement):
    _content = T.String(required=True)


class ProtocolName(OE.ODMElement):
    _content = T.String(required=True)


class StudyName(OE.ODMElement):
    _content = T.String(required=True)


class GlobalVariables(OE.ODMElement):
    StudyName = T.ODMObject(element_class=StudyName)
    StudyDescription = T.ODMObject(element_class=StudyDescription)
    ProtocolName = T.ODMObject(element_class=ProtocolName)


class Description(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CDISCSynonym(OE.ODMElement):
    _content = T.String(required=True)


class CDISCDefinition(OE.ODMElement):
    _content = T.String(required=True)


class CDISCSubmissionValue(OE.ODMElement):
    _content = T.String(required=True)


class PreferredTerm(OE.ODMElement):
    _content = T.String(required=True)


class EnumeratedItem(OE.ODMElement):
    CodedValue = T.String(required=True)
    ExtCodeID = T.String(required=True, namespace="nciodm")
    CDISCSynonym = T.ODMListObject(element_class=CDISCSynonym, namespace="nciodm")
    CDISCDefinition = T.ODMObject(required=True, element_class=CDISCDefinition, namespace="nciodm")
    PreferredTerm = T.ODMObject(required=True, element_class=PreferredTerm, namespace="nciodm")


class CodeList(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    ExtCodeID = T.String(required=True, namespace="nciodm")
    CodeListExtensible = T.ValueSetString(required=True, namespace="nciodm")
    Description = T.ODMObject(element_class=Description)
    EnumeratedItem = T.ODMListObject(element_class=EnumeratedItem)
    CDISCSubmissionValue = T.ODMObject(required=True, element_class=CDISCSubmissionValue, namespace="nciodm")
    CDISCSynonym = T.ODMObject(required=True, element_class=CDISCSynonym, namespace="nciodm")
    PreferredTerm = T.ODMObject(required=True, element_class=PreferredTerm, namespace="nciodm")


class MetaDataVersion(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.String(required=False)
    CodeList = T.ODMListObject(element_class=CodeList)


class Study(OE.ODMElement):
    OID = T.String(required=True)
    GlobalVariables = T.ODMObject(required=True, element_class=GlobalVariables)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class ODM(OE.ODMElement):
    Description = T.String(required=False)
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    schemaLocation = T.String(required=False, namespace="xs")
    Study = T.ODMListObject(element_class=Study)
