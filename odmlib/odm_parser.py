import xml.etree.ElementTree as ET
import xmlschema as XSD
import odmlib.ns_registry as NS
from abc import ABC, abstractmethod
import json

ODM_NS = {'odm': 'http://www.cdisc.org/ns/odm/v1.3'}
ODM_PREFIX = "odm:"


class SchemaValidator(ABC):
    @abstractmethod
    def validate_tree(self, tree):
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_tree in the Validator class")

    @abstractmethod
    def validate_file(self, xml_file):
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_file in the Validator class")


class ODMSchemaValidator(SchemaValidator):
    def __init__(self, xsd_file):
        self.xsd = XSD.XMLSchema(xsd_file)

    def validate_tree(self, tree):
        result = self.xsd.is_valid(tree)
        return result

    def validate_file(self, odm_file):
        result = self.xsd.validate(odm_file)
        return result


class BaseParser:
    def __init__(self, ns_registry):
        if ns_registry:
            self.nsr = ns_registry
        else:
            self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)

    def register_namespaces(self):
        for prefix, url in self.nsr.namespaces.items():
            ET.register_namespace(prefix, url)

    def __getattr__(self, item):
        """ enables the parser to dynamically parse any element given it's parent """
        def parse_method(*args, parent, ns_prefix="odm", **kwargs):
            elem_list = []
            for elem in parent.findall(ns_prefix + ":" + item, self.nsr.get_ns_entry_dict(ns_prefix)):
                elem_list.append({**elem.attrib, "elem": elem})
            return elem_list
        return parse_method


class ElementParser:
    def __init__(self):
        self.root = None
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []

    def ODM(self):
        return self.root

    def Study(self):
        study = self.root.find(ODM_PREFIX + "Study", ODM_NS)
        return study

    def MetaDataVersion(self):
        study = self.root.find(ODM_PREFIX + "Study", ODM_NS)
        self.mdv = study.findall(ODM_PREFIX + "MetaDataVersion", ODM_NS)
        return self.mdv

    def AdminData(self):
        self.admin_data = self.root.findall(ODM_PREFIX + "AdminData", ODM_NS)
        return self.admin_data

    def ClinicalData(self):
        self.clinical_data = self.root.findall(ODM_PREFIX + "ClinicalData", ODM_NS)
        return self.clinical_data

    def ReferenceData(self):
        self.reference_data = self.root.findall(ODM_PREFIX + "ReferenceData", ODM_NS)
        return self.reference_data


class ODMParser(BaseParser, ElementParser):
    def __init__(self, odm_file, namespace_registry=None):
        self.odm_file = odm_file
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        self.register_namespaces()
        odm_tree = ET.parse(self.odm_file)
        self.root = odm_tree.getroot()
        return self.root

    def parse_tree(self):
        self.register_namespaces()
        return ET.parse(self.odm_file)


class ODMStringParser(BaseParser, ElementParser):
    def __init__(self, odm_string, namespace_registry=None):
        self.odm_string = odm_string
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        self.register_namespaces()
        self.root = ET.fromstring(self.odm_string)
        return self.root

    def parse_tree(self):
        self.register_namespaces()
        return ET.fromstring(self.odm_string)


class ODMJSONStringParser:
    def __init__(self, odm_string):
        self.root = json.loads(odm_string)
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []
        self.reference_data = []

    def parse(self):
        return self.root

    def ODM(self):
        return self.root

    def Study(self):
        study = self.root["Study"]
        return study

    def MetaDataVersion(self):
        study = self.root["Study"]
        self.mdv = study[0]["MetaDataVersion"]
        return self.mdv

    def AdminData(self):
        self.admin_data = self.root["AdminData"]
        return self.admin_data

    def ClinicalData(self):
        self.clinical_data = self.root["ClinicalData"]
        return self.clinical_data

    def ReferenceData(self):
        self.reference_data = self.root["ReferenceData"]
        return self.reference_data
