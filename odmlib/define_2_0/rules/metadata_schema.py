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
    """ The metadata schema for Define-XML v2.0 to aid in conformance checking """
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
        registry.add("TranslatedText", {"lang": {"type": "string"},
                                                 "_content": {"type": "string", "required": True}})

        registry.add("Alias", {
            "Context": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True}
        })

        registry.add("Description", {"TranslatedText": {"type": "list",
                            "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}})

        registry.add("title", {"_content": {"type": "string", "required": True}})

        registry.add("leaf", {
            "ID": {"type": "string", "required": True},
            "href": {"type": "string", "required": True},
            "title": {"type": "dict", "schema": registry.get("title")}})

        registry.add("WhereClauseRef", {
            "WhereClauseOID": {"type": "string", "required": True}
        })

        registry.add("ValueListRef", {
            "ValueListOID": {"type": "string", "required": True}
        })

        registry.add("PDFPageRef", {
            "Type": {"type": "string", "required": True, "allowed": ["PhysicalRef", "NamedDestination"]},
            "PageRefs": {"type": "string"},
            "FirstPage": {"type": "integer"},
            "LastPage": {"type": "integer"}
        })

        registry.add("DocumentRef", {
            "leafID": {"type": "string", "required": True},
            "PDFPageRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("PDFPageRef")}}
        })

        registry.add("ItemRef", {
            "ItemOID": {"type": "string", "required": True},
            "OrderNumber":  { "type": "integer", "required": False},
            "Mandatory": { "type": "string", "required": False, "allowed": ["Yes", "No"]},
            "KeySequence": { "type": "integer", "required": False},
            "MethodOID": {"type": "string", "required": False},
            "Role": {"type": "string", "required": False},
            "RoleCodeListOID": {"type": "string", "required": False},
            "WhereClauseRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("WhereClauseRef")}}
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
            "Structure": {"type": "string", "required": True},
            "Class": {"type": "string", "required": True},
            "ArchiveLocationID": {"type": "string", "required": True},
            "CommentOID": {"type": "string"},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemRef")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}},
            "leaf": {"type": "dict", "schema": registry.get("leaf")}
        })

        registry.add("FormalExpression", {
            "Context": {"type": "string", "required": True},
            "_content": {"type": "string", "required": True}
        })

        registry.add("RangeCheck", {
            "Comparator": {"type": "string", "allowed": ["LT", "LE", "GT", "GE", "EQ", "NE", "IN", "NOTIN"]},
            "SoftHard": {"type": "string", "allowed": ["Soft", "Hard"]},
            "ItemOID": {"type": "string", "required": True},
            "CheckValue": {"type": "list", "schema": {"type": "dict", "schema": {"_content": {"type": "string"}}}}
        })

        registry.add("Origin", {
            "Type": {"type": "string", "required": True,
                     "allowed": ["CRF", "Derived", "Assigned", "Assigned", "Protocol", "eDT", "Predecessor"]},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("DocumentRef")}},
            "Description": {"type": "dict", "schema": registry.get("Description")}
        })

        registry.add("CodeListRef", {
            "CodeListOID": {"type": "string"}
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
            "DisplayFormat": {"type": "string"},
            "CommentOID": {"type": "string"},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "CodeListRef": {"type": "dict", "schema": registry.get("CodeListRef")},
            "Origin": {"type": "dict", "schema": registry.get("Origin")},
            "ValueListRef": {"type": "dict", "schema": registry.get("ValueListRef")},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("CodeListItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "ExtendedValue": {"type": "string", "allowed": ["Yes"]},
            "Decode": {"type": "dict", "schema": {"TranslatedText": {"type": "list",
                       "schema": {"type": "dict", "schema": registry.get("TranslatedText")}}}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}}
        })

        registry.add("EnumeratedItem", {
            "CodedValue": {"type": "string", "required": True},
            "Rank": {"type": "float"},
            "OrderNumber": {"type": "integer"},
            "ExtendedValue": {"type": "string", "allowed": ["Yes"]},
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

        registry.add("AnnotatedCRF", {
            "DocumentRef": {"type": "dict", "schema": registry.get("DocumentRef")}
        })

        registry.add("SupplementalDoc", {
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("DocumentRef")}}
        })

        registry.add("WhereClauseDef", {
            "OID": {"type": "string", "required": True},
            "CommentOID": {"type": "string"},
            "RangeCheck": {"type": "list", "schema": {"type": "dict", "schema": registry.get("RangeCheck")}}
        })

        registry.add("ValueListDef", {
            "OID": {"type": "string", "required": True},
            "ItemRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemRef")}}
        })

        registry.add("CommentDef", {
            "OID": {"type": "string", "required": True},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("DocumentRef")}}
        })

        registry.add("MethodDef", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Type": {"type": "string", "required": True, "allowed": ["Computation", "Imputation", "Transpose", "Other"]},
            "Description": {"type": "dict", "schema": registry.get("Description")},
            "FormalExpression": {"type": "list", "schema": {"type": "dict", "schema": registry.get("FormalExpression")}},
            "Alias": {"type": "list", "schema": {"type": "dict", "schema": registry.get("Alias")}},
            "DocumentRef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("DocumentRef")}}
        })

        registry.add("MetaDataVersion", {
            "OID": {"type": "string", "required": True},
            "Name": {"type": "string", "required": True},
            "Description": {"type": "string"},
            "DefineVersion": {"type": "string", "required": True},
            "StandardName": {"type": "string", "required": True},
            "StandardVersion": {"type": "string", "required": True},
            "AnnotatedCRF": {"type": "dict", "schema": registry.get("AnnotatedCRF")},
            "SupplementalDoc": {"type": "dict", "schema": registry.get("SupplementalDoc")},
            "ValueListDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ValueListDef")}},
            "WhereClauseDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("WhereClauseDef")}},
            "ItemGroupDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemGroupDef")}},
            "ItemDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("ItemDef")}},
            "CodeList": {"type": "list", "schema": {"type": "dict", "schema": registry.get("CodeList")}},
            "MethodDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("MethodDef")}},
            "CommentDef": {"type": "list", "schema": {"type": "dict", "schema": registry.get("CommentDef")}},
            "leaf": {"type": "list", "schema": {"type": "dict", "schema": registry.get("leaf")}}
        })

        registry.add("StudyName", {"_content": {"type": "string", "required": True}})

        registry.add("StudyDescription", {"_content": {"type": "string", "required": True}})

        registry.add("ProtocolName", {"_content": {"type": "string", "required": True}})

        registry.add("GlobalVariables", {
            "StudyName": {"type": "dict", "schema": registry.get("StudyName")},
            "StudyDescription": {"type": "dict", "schema": registry.get("StudyDescription")},
            "ProtocolName": {"type": "dict", "schema": registry.get("ProtocolName")}
        })

        registry.add("Study", {
            "OID": {"type": "string", "required": True},
            "GlobalVariables": {"type": "dict", "schema": registry.get("GlobalVariables")},
            "MetaDataVersion": {"type": "dict", "schema": registry.get("MetaDataVersion")}
        })

        registry.add("ODM", {
            "FileType": {"type": "string", "required": True, "allowed": ["Snapshot"]},
            "FileOID": {"type": "string", "required": True},
            "CreationDateTime": {"type": "string", "required": True},
            "AsOfDateTime": {"type": "string"},
            "ODMVersion": {"type": "string", "required": True, "allowed": ["1.3.2"]},
            "Originator": {"type": "string"},
            "SourceSystem": {"type": "string"},
            "SourceSystemVersion": {"type": "string"},
            "schemaLocation": {"type": "string"},
            "ID": {"type": "string"},
            "Study": {"type": "dict", "required": True, "schema": registry.get("Study")}
        })
