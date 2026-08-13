from abc import ABC, abstractmethod
from cerberus import validator
from cerberus.schema import SchemaRegistry
from odmlib.exceptions import OdmlibConformanceError


class ConformanceChecker(ABC):
    @abstractmethod
    def check_conformance(self, doc, schema_name):
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_tree in the Validator class")


class MetadataSchema(ConformanceChecker):
    def __init__(self):
        # each instance gets a private SchemaRegistry: the module-level
        # cerberus registry is process-global, so two MetadataSchema classes
        # from different model packages would overwrite each other's schemas
        self._registry = SchemaRegistry()
        self._validators = {}
        self._set_metadata_registry(self._registry)

    def check_conformance(self, doc, schema_name):
        schema = self._registry.get(schema_name)
        if schema is None:
            raise OdmlibConformanceError(
                f"No conformance schema registered for '{schema_name}'",
                element_type=schema_name,
                hint=f"Register a schema for '{schema_name}' in MetadataSchema._set_metadata_registry(), "
                     "or call validate() without conformance_checker for this model.",
            )
        v = self._validators.get(schema_name)
        if v is None:
            v = validator.Validator(schema, schema_registry=self._registry)
            self._validators[schema_name] = v
        is_valid = v.validate(doc)
        if not is_valid:
            raise OdmlibConformanceError(
                f"Conformance validation failed for {schema_name}: {v.errors}",
                cerberus_errors=v.errors,
                element_type=schema_name,
                hint="Review the cerberus_errors attribute for a field-by-field breakdown",
            )
        return is_valid

    @staticmethod
    def _set_metadata_registry(registry):
        """ a cerberus json schema has been generated from the odm_1_3_2 model """
        registry.add("TranslatedText", {"lang": {"type": "string"},
                                                 "_content": {"type": "string", "required": True}})

        registry.add("Alias", {
            "Context": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True}
        })

        registry.add("Description", {"TranslatedText": {"type": "list",
                            "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}})

        registry.add("StudyEventRef", {
                    "StudyEventOID": {"type": "string", "required": True},
                    "OrderNumber":  {"type": "integer", "required": False},
                    "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
                    "CollectionExceptionOID": {"type": "string", "required": False}
                })

        registry.add("Protocol", {
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "StudyEventRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("StudyEventRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("FormRef", {
            "FormOID": {"type": "string", "required": True},
            "OrderNumber":  {"type": "integer", "required": False},
            "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
            "CollectionExceptionOID": {"type": "string", "required": False}
        })

        registry.add("StudyEventDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "required": True, "allowed": ["Yes", "No"]},
            "Type": {"type": "string", "allowed": ["Scheduled", "Unscheduled", "Common"]},
            "Category": {"type": "string"},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "FormRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("ItemGroupRef", {
            "ItemGroupOID": {"type": "string", "required": True},
            "OrderNumber": {"type": "integer", "required": False},
            "Mandatory": {"type": "string", "allowed": ["Yes", "No"]},
            "CollectionExceptionOID": {"type": "string", "required": False}
        })

        registry.add("ArchiveLayout", {
            "OID": {"type": "string", "required": True},
            "PdfFileName": {"type": "string", "required": True},
        })

        registry.add("FormDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "required": True, "allowed": ["Yes", "No"]},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "ItemGroupRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemGroupRef")}},
            "ArchiveLayout": {"type": "list","schema": {"type": "dict", "schema": registry.get("ArchiveLayout")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("ItemRef", {
            "ItemOID": {"type": "string", "required": True},
            "OrderNumber":  { "type": "integer", "required": False},
            "Mandatory": { "type": "string", "required": False, "allowed": ["Yes", "No"]},
            "KeySequence": { "type": "integer", "required": False},
            "MethodOID": {"type": "string", "required": False},
            "Role": {"type": "string", "required": False},
            "RoleCodeListOID": {"type": "string", "required": False},
            "CollectionExceptionOID": {"type": "string", "required": False},
        })

        registry.add("ItemGroupDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Repeating": {"type": "string", "required": True, "allowed": ["Yes", "No"]},
            "IsReferenceData": {"type": "string", "allowed": ["Yes", "No"]},
            "SASDatasetName": {"type": "string"},
            "Domain": {"type": "string"},
            "Origin": {"type": "string"},
            "Purpose": {"type": "string"},
            "Comment": {"type": "string"},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("FormalExpression", {
            "Context": {"type": "string", "required": True},
            "_content": {"type": "string", "required": True}
        })

        registry.add("MeasurementUnitRef", {
            "MeasurementUnitOID": {"type": "string", "required": True}
        })

        registry.add("RangeCheck", {
            "Comparator": {"type": "string", "allowed": ["LT", "LE", "GT", "GE", "EQ", "NE", "IN", "NOTIN"]},
            "SoftHard": {"type": "string", "allowed": ["Soft", "Hard"]},
            "CheckValue": {"type": "list", "schema": {"type": "dict", "schema": {"_content": {"type": "string"}}}},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormalExpression")}},
            "MeasurementUnitRef": {"type": "dict", "schema": registry.get("MeasurementUnitRef")},
            "ErrorMessage": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                         "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}}
        })

        registry.add("ExternalQuestion", {
            "Dictionary": {"type": "string", "required": False},
            "Version": {"type": "string", "required": False},
            "Code": {"type": "string", "required": False},
        })

        registry.add("CodeListRef", {
            "CodeListOID": {"type": "string", "required": True}
        })

        registry.add("ItemDef", {
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
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "Question": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                         "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}},
            "ExternalQuestion": {"type": "dict", "schema": registry.get("ExternalQuestion")},
            "MeasurementUnitRef": {"type": "list", "schema": {  "type": "dict", "schema": registry.get("MeasurementUnitRef")}},
            "CodeListRef": {"type": "dict", "schema": registry.get("CodeListRef")},
            "ErrorMessage": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                             "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}},
            "RangeCheck": {"type": "dict", "schema": registry.get("RangeCheck")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("CodeListItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "Decode": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                       "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("EnumeratedItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("ExternalCodeList", {
            "Dictionary": {"type": "string"},
            "Version": {"type": "string"},
            "ref": {"type": "string"},
            "href": {"type": "string"}
        })

        registry.add("CodeList", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "DataType": {"type": "string", "allowed": ["text", "integer", "float", "string"]},
            "SASFormatName": {"type": "string"},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "CodeListItem": {"type": "list", "schema": {"type": "dict", "schema": registry.get("CodeListItem")}},
            "EnumeratedItem": {"type": "list", "schema": {"type": "dict", "schema": registry.get("EnumeratedItem")}},
            "ExternalCodeList": {"type": "dict", "schema": registry.get("ExternalCodeList")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("ConditionDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("MethodDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Type": {"type": "string", "required": True, "allowed": ["Computation", "Imputation", "Transpose", "Other"]},
            "Description": {"type": "dict", "required": True, "schema": registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("Include", {
            "StudyOID": {"type": "string", "required": True},
            "MetaDataVersionOID": {"type": "string", "required": True}
        })

        registry.add("Presentation", {
            "OID": {"type": "string", "required": True},
            "lang": {"type": "string"},
            "_content": {"type": "string"}
        })

        registry.add("MetaDataVersion", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "string"},
            "Include": {"type": "dict", "schema": registry.get("Include")},
            "Protocol": {"type": "dict", "schema": registry.get("Protocol")},
            "StudyEventDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("StudyEventDef")}},
            "FormDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormDef")}},
            "ItemGroupDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemGroupDef")}},
            "ItemDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemDef")}},
            "CodeList": {"type": "list", "schema": {"type": "dict", "schema": registry.get("CodeList")}},
            "Presentation": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Presentation")}},
            "ConditionDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ConditionDef")}},
            "MethodDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("MethodDef")}}
        })

        registry.add("MeasurementUnit", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Symbol": {"type": "dict", "schema" : {
                "TranslatedText": {"type": "list",
                                    "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}
            },
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("BasicDefinitions", {
            "MeasurementUnit": {"type": "list", "schema": {"type": "dict", "schema": registry.get("MeasurementUnit")}}
        })


        registry.add("Study", {
            "OID": {"type": "string", "required": True},
            "GlobalVariables": {"type": "dict", "required": True, "schema": {
                    "StudyName": {"schema": {"_content": {"type": "string", "required": True}}},
                    "StudyDescription": {"schema": {"_content": {"type": "string", "required": True}}},
                    "ProtocolName": {"schema": {"_content": {"type": "string", "required": True}}}
                }
            },
            "BasicDefinitions": {"type": "dict", "schema": registry.get("BasicDefinitions")},
            "MetaDataVersion": {"type": "list", "schema": {"type": "dict", "schema": registry.get("MetaDataVersion")}}
        })

        registry.add("ODM", {
            "Description": {"type": "string"},
            "FileType": {"type": "string", "required": True, "allowed": ["Snapshot", "Transactional"]},
            "Granularity": {"type": "string", "allowed": ["All", "Metadata", "AdminData", "ReferenceData",
                                                          "AllClinicalData", "SingleSite", "SingleSubject"]},
            "Archival": {"type": "string", "allowed": ["Yes", "No"]},
            "FileOID": {"type": "string", "required": True},
            "CreationDateTime": {"type": "string", "required": True},
            "PriorFileOID": {"type": "string"},
            "AsOfDateTime": {"type": "string"},
            "FileType": {"type": "string", "required": True, "allowed": ["Snapshot", "Transactional"]},
            "ODMVersion": {"type": "string", "allowed": ["1.3.2", "1.3"]},
            "Originator": {"type": "string"},
            "SourceSystem": {"type": "string"},
            "SourceSystemVersion": {"type": "string"},
            "ID": {"type": "string"},
            "schemaLocation": {"type": "string"},
            "Study": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Study")}}
        })
