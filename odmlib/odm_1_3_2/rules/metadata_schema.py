from abc import ABC, abstractmethod
from cerberus import schema_registry, validator


class ConformanceChecker(ABC):
    @abstractmethod
    def verify_conformance(self, doc, schema_name):
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_tree in the Validator class")


class MetadataSchema(ConformanceChecker):
    def __init__(self):
        self._set_metadata_registry()

    def verify_conformance(self, doc, schema_name):
        schema = schema_registry.get(schema_name)
        v = validator.Validator(schema)
        is_valid = v.validate(doc)
        if not is_valid:
            raise ValueError(v.errors)
        return is_valid

    @staticmethod
    def _set_metadata_registry():
        """ a cerberus json schema has been generated from the odm_1_3_2 model """
        schema_registry.add("TranslatedText", {"lang": {"type": "string"},
                                                 "_content": {"type": "string", "required": True}})

        schema_registry.add("Alias", {
            "Context": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True}
        })

        schema_registry.add("Description", {"TranslatedText": {"type": "list",
                            "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}})

        schema_registry.add("StudyEventRef", {
                    "StudyEventOID": {"type": "string", "required": True},
                    "OrderNumber":  {"type": "integer", "required": False},
                    "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
                    "CollectionExceptionOID": {"type": "string", "required": False}
                })

        schema_registry.add("Protocol", {
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "StudyEventRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("StudyEventRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("FormRef", {
            "FormOID": {"type": "string", "required": True},
            "OrderNumber":  {"type": "integer", "required": False},
            "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
            "CollectionExceptionOID": {"type": "string", "required": False}
        })

        schema_registry.add("StudyEventDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "allowed": ["Yes", "No"]},
            "Type": {"type": "string", "allowed": ["Scheduled", "Unscheduled", "Common"]},
            "Category": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "FormRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("ItemGroupRef", {
            "ItemGroupOID": {"type": "string", "required": True},
            "OrderNumber": {"type": "integer", "required": False},
            "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
            "CollectionExceptionOID": {"type": "string", "required": False}
        })

        schema_registry.add("ArchiveLayout", {
            "OID": {"type": "string", "required": True},
            "PdfFileName": {"type": "string", "required": True},
        })

        schema_registry.add("FormDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "allowed": ["Yes", "No"]},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "ItemGroupRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemGroupRef")}},
            "ArchiveLayout": {"type": "list","schema": {"type": "dict", "schema": schema_registry.get("ArchiveLayout")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("ItemRef", {
            "ItemOID": {"type": "string", "required": True},
            "OrderNumber":  { "type": "integer", "required": False},
            "Mandatory": { "type": "string", "required": False, "allowed": ["Yes", "No"]},
            "KeySequence": { "type": "integer", "required": False},
            "MethodOID": {"type": "string", "required": False},
            "Role": {"type": "string", "required": False},
            "RoleCodeListOID": {"type": "string", "required": False},
            "CollectionExceptionOID": {"type": "string", "required": False},
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
            "Comment": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("FormalExpression", {
            "Context": {"type": "string", "required": True},
            "_content": {"type": "string", "required": True}
        })

        schema_registry.add("MeasurementUnitRef", {
            "MeasurementUnitOID": {"type": "string", "required": True}
        })

        schema_registry.add("RangeCheck", {
            "Comparator": {"type": "string", "allowed": ["LT", "LE", "GT", "GE", "EQ", "NE", "IN", "NOTIN"]},
            "SoftHard": {"type": "string", "allowed": ["Soft", "Hard"]},
            "CheckValue": {"type": "list", "schema": {"type": "dict", "schema": {"_content": {"type": "string"}}}},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormalExpression")}},
            "MeasurementUnitRef": {"type": "dict", "schema": schema_registry.get("MeasurementUnitRef")},
            "ErrorMessage": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                         "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}}
        })

        schema_registry.add("ExternalQuestion", {
            "Dictionary": {"type": "string", "required": False},
            "Version": {"type": "string", "required": False},
            "Code": {"type": "string", "required": False},
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
            "SDSVarName": {"type": "string"},
            "Origin": {"type": "string"},
            "Comment": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "Question": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                         "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
            "ExternalQuestion": {"type": "dict", "schema": schema_registry.get("ExternalQuestion")},
            "CodeListRef": {"type": "dict", "schema": schema_registry.get("CodeListRef")},
            "ErrorMessage": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                             "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
            "RangeCheck": {"type": "dict", "schema": schema_registry.get("RangeCheck")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("CodeListItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "Decode": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                       "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("EnumeratedItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
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
            "SASFormatName": {"type": "string"},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "CodeListItem": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("CodeListItem")}},
            "EnumeratedItem": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("EnumeratedItem")}},
            "ExternalCodeList": {"type": "dict", "schema": schema_registry.get("ExternalCodeList")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("ConditionDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "dict", "schema": schema_registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("MethodDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Type": {"type": "string", "required": True, "allowed": ["Computation", "Imputation", "Transpose", "Other"]},
            "Description": {"type": "dict", "required": True, "schema": schema_registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("Alias")}}
        })

        schema_registry.add("MetaDataVersion", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "string"},
            "Protocol": {"type": "dict", "schema": schema_registry.get("Protocol")},
            "StudyEventDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("StudyEventDef")}},
            "FormDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("FormDef")}},
            "ItemGroupDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemGroupDef")}},
            "ItemDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ItemDef")}},
            "CodeList": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("CodeList")}},
            "ConditionDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("ConditionDef")}},
            "MethodDef": {"type": "list", "schema": {"type": "dict", "schema": schema_registry.get("MethodDef")}}
        })


        schema_registry.add("Study", {
            "OID": {"type": "string", "required": True},
            "GlobalVariables": {"type": "dict", "required": True, "schema": {
                    "StudyName": {"schema": {"_content": {"type": "string", "required": True}}},
                    "StudyDescription": {"schema": {"_content": {"type": "string", "required": True}}},
                    "ProtocolName": {"schema": {"_content": {"type": "string", "required": True}}}
                }
            },
            "MetaDataVersion": {"type": "dict", "schema": schema_registry.get("MetaDataVersion")}
        })

        # schema_registry.add("Study", {
        #     "OID": {"type": "string", "required": True},
        #     "GlobalVariables": {"type": "dict", "required": True, "schema": {
        #             "StudyName": {"schema": {"TranslatedText": {"type": "list",
        #                           "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
        #             "StudyDescription": {"schema": {"TranslatedText": {"type": "list",
        #                                  "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}},
        #             "ProtocolName": {"schema": {"TranslatedText": {"type": "list",
        #                              "schema": {"type": "dict", "schema": schema_registry.get("TranslatedText")}}}}
        #         }
        #     },
        #     "MetaDataVersion": {"type": "dict", "schema": schema_registry.get("MetaDataVersion")}
        # })
