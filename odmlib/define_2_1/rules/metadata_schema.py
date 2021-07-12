from abc import ABC, abstractmethod
from cerberus import schema_registry, validator


class ConformanceChecker(ABC):
    @abstractmethod
    def check_conformance(self, doc, schema_name):
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_tree in the Validator class")


class MetadataSchema(ConformanceChecker):
    """ The metadata schema for Define-XML v2.1 to aid in conformance checking """
    def __init__(self):
        self._set_metadata_registry()

    def check_conformance(self, doc, schema_name):
        schema = schema_registry.get(schema_name)
        v = validator.Validator(schema)
        is_valid = v.validate(doc)
        if not is_valid:
            raise ValueError(v.errors)
        return is_valid

    @staticmethod
    def _set_metadata_registry():
        schema_registry.add("TranslatedText", {"lang": {"type": "string"},
                                                 "_content": {"type": "string", "required": True}})

        schema_registry.add("Alias", {
            "Context": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True}
        })

        schema_registry.add("Description", {"TranslatedText": {"type": "list",
                            "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}})

        schema_registry.add("title", {"_content": {"type": "string", "required": True}})

        schema_registry.add("leaf", {
            "ID": {"type": "string", "required": True},
            "href": {"type": "string", "required": True},
            "title": {"type": "dict", "schema": schema_registry.get("title")}})

        schema_registry.add("WhereClauseRef", {
            "WhereClauseOID": {"type": "string", "required": True}
        })

        schema_registry.add("ValueListRef", {
            "ValueListOID": {"type": "string", "required": True}
        })

        schema_registry.add("PDFPageRef", {
            "Type": {"type": "string", "required": True, "allowed": ["PhysicalRef", "NamedDestination"]},
            "PageRefs": {"type": "string"},
            "FirstPage": {"type": "integer"},
            "LastPage": {"type": "integer"},
            "Title": {"type": "string"}
        })

        schema_registry.add("DocumentRef", {
            "leafID": {"type": "string", "required": True},
            "PDFPageRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("PDFPageRef")}}
        })

        schema_registry.add("ItemRef", {
            "ItemOID": {"type": "string", "required": True},
            "OrderNumber":  { "type": "integer", "required": False},
            "Mandatory": { "type": "string", "required": False, "allowed": ["Yes", "No"]},
            "KeySequence": { "type": "integer", "required": False},
            "MethodOID": {"type": "string", "required": False},
            "Role": {"type": "string", "required": False},
            "RoleCodeListOID": {"type": "string", "required": False},
            "IsNonStandard": {"type": "string", "allowed": ["Yes"]},
            "HasNoData": {"type": "string", "allowed": ["Yes"]},
            "WhereClauseRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("WhereClauseRef")}}
        })

        schema_registry.add("SubClass", {
            "Name": {"type": "string"},
            "ParentClass": {"type": "string"}
        })

        schema_registry.add("Class", {
            "Name": {"type": "string"},
            "SubClass": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("SubClass")}}
        })

        schema_registry.add("ItemGroupDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "allowed": ["Yes", "No"]},
            "IsReferenceData": {"type": "string", "allowed": ["Yes", "No"]},
            "SASDatasetName": {"type": "string"},
            "Domain": {"type": "string"},
            "Origin": {"type": "string"},
            "Purpose": {"type": "string"},
            "Structure": {"type": "string", "required": True},
            "ArchiveLocationID": {"type": "string"},
            "CommentOID": {"type": "string"},
            "IsNonStandard": {"type": "string", "allowed": ["Yes"]},
            "StandardOID": {"type": "string"},
            "HasNoData": {"type": "string", "allowed": ["Yes"]},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}},
            "Class": {"type": "dict", "schema": schema_registry.get("Class")},
            "leaf": {"type": "dict", "schema": schema_registry.get("leaf")}
        })

        schema_registry.add("FormalExpression", {
            "Context": {"type": "string", "required": True},
            "_content": {"type": "string", "required": True}
        })

        schema_registry.add("RangeCheck", {
            "Comparator": {"type": "string", "allowed": ["LT", "LE", "GT", "GE", "EQ", "NE", "IN", "NOTIN"]},
            "SoftHard": {"type": "string", "allowed": ["Soft", "Hard"]},
            "ItemOID": {"type": "string", "required": True},
            "CheckValue": {"type": "list", "schema": {"type": "dict", "schema": {"_content": {"type": "string"}}}}
        })

        schema_registry.add("Origin", {
            "Type": {"type": "string", "required": True,
                     "allowed": ["Collected", "Derived", "Assigned", "Protocol", "Predecessor", "Not Available"]},
            "Source": {"type": "string", "allowed": ["Subject", "Investigator", "Vendor", "Sponsor"]},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("DocumentRef")}},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")}
        })

        schema_registry.add("CodeListRef", {
            "CodeListOID": {"type": "string"}
        })

        schema_registry.add("ItemDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "DataType": {"type": "string", "allowed": ["text", "integer", "float", "date", "time", "datetime", "string",
                                                        "boolean", "double", "hexBinary", "base64Binary", "hexFloat",
                                                        "base64Float", "partialDate", "partialTime", "partialDatetime",
                                                        "durationDatetime", "intervalDatetime", "incompleteDatetime",
                                                        "incompleteDate", "incompleteTime", "URI"]},
            "Length": {"type": "integer"},
            "SignificantDigits": {"type": "integer"},
            "SASFieldName": {"type": "string"},
            "DisplayFormat": {"type": "string"},
            "CommentOID": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "CodeListRef": {"type": "dict", "schema": schema_registry.get("CodeListRef")},
            "Origin": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Origin")}},
            "ValueListRef": {"type": "dict", "schema": schema_registry.get("ValueListRef")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("CodeListItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "ExtendedValue": {"type": "string", "allowed": ["Yes"]},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "Decode": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                       "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("EnumeratedItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "ExtendedValue": {"type": "string", "allowed": ["Yes"]},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("ExternalCodeList", {
            "Dictionary": {"type": "string"},
            "Version": {"type": "string"},
            "ref": {"type": "string"},
            "href": {"type": "string"}
        })

        schema_registry.add("CodeList", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "DataType": {"type": "string", "allowed": ["text", "integer", "float", "string"]},
            "IsNonStandard": {"type": "string", "allowed": ["Yes"]},
            "StandardOID": {"type": "string"},
            "CommentOID": {"type": "string"},
            "SASFormatName": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "CodeListItem": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("CodeListItem")}},
            "EnumeratedItem": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("EnumeratedItem")}},
            "ExternalCodeList": {"type": "dict", "schema": schema_registry.get("ExternalCodeList")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("AnnotatedCRF", {
            "DocumentRef": {"type": "dict", "schema": schema_registry.get("DocumentRef")}
        })

        schema_registry.add("SupplementalDoc", {
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("DocumentRef")}}
        })

        schema_registry.add("WhereClauseDef", {
            "OID": {"type": "string", "required": True},
            "CommentOID": {"type": "string"},
            "RangeCheck": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("RangeCheck")}}
        })

        schema_registry.add("ValueListDef", {
            "OID": {"type": "string", "required": True},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemRef")}}
        })

        schema_registry.add("CommentDef", {
            "OID": {"type": "string", "required": True},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("DocumentRef")}}
        })

        schema_registry.add("MethodDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Type": {"type": "string", "required": True, "allowed": ["Computation", "Imputation", "Transpose", "Other"]},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("DocumentRef")}}
        })

        schema_registry.add("Standard", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Type": {"type": "string", "required": True},
            "PublishingSet": {"type": "string"},
            "Version": {"type": "string", "required": True},
            "Status": {"type": "string"},
            "CommentOID": {"type": "string"}
        })

        schema_registry.add("Standards", {
            "Standard": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Standard")}}
        })

        schema_registry.add("MetaDataVersion", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "string"},
            "DefineVersion": {"type": "string", "required": True},
            "CommentOID": {"type": "string"},
            "Standards": {"type": "dict", "schema": schema_registry.get("Standards")},
            "AnnotatedCRF": {"type": "dict", "schema": schema_registry.get("AnnotatedCRF")},
            "SupplementalDoc": {"type": "dict", "schema": schema_registry.get("SupplementalDoc")},
            "ValueListDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ValueListDef")}},
            "WhereClauseDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("WhereClauseDef")}},
            "ItemGroupDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemGroupDef")}},
            "ItemDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemDef")}},
            "CodeList": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("CodeList")}},
            "MethodDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("MethodDef")}},
            "CommentDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("CommentDef")}},
            "leaf": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("leaf")}}
        })


        schema_registry.add("StudyName", {"_content": {"type": "string", "required": True}})

        schema_registry.add("StudyDescription", {"_content": {"type": "string", "required": True}})

        schema_registry.add("ProtocolName", {"_content": {"type": "string", "required": True}})

        schema_registry.add("GlobalVariables", {
            "StudyName": {"type": "dict", "schema": schema_registry.get("StudyName")},
            "StudyDescription": {"type": "dict", "schema": schema_registry.get("StudyDescription")},
            "ProtocolName": {"type": "dict", "schema": schema_registry.get("ProtocolName")}
        })

        schema_registry.add("Study", {
            "OID": {"type": "string", "required": True},
            "GlobalVariables": {"type": "dict", "schema": schema_registry.get("GlobalVariables")},
            "MetaDataVersion": {"type": "dict", "schema": schema_registry.get("MetaDataVersion")}
        })
