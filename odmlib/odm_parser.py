import xml.etree.ElementTree as ET
import xmlschema as XSD
import odmlib.ns_registry as NS
from abc import ABC, abstractmethod

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
        self.nsr = ns_registry

    def __getattr__(self, item):
        """ enables the parser to dynamically parse any element given it's parent """
        def parse_method(*args, parent, ns_prefix="odm", **kwargs):
            elem_list = []
            for elem in parent.findall(ns_prefix + ":" + item, self.nsr.get_ns_entry_dict(ns_prefix)):
                elem_list.append({**elem.attrib, "elem": elem})
            return elem_list
        return parse_method


class ODMParser(BaseParser):
    #def __init__(self, odm_file, odm_type="ODM_1_3_2"): changed to parse different extensions
    def __init__(self, odm_file, namespace_registry=None):
        self.odm_file = odm_file
        if namespace_registry:
            self.nsr = namespace_registry
        else:
            self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
        super().__init__(ns_registry=self.nsr)
        self.root = None
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []

    def parse(self):
        self._register_namespaces()
        odm_tree = ET.parse(self.odm_file)
        self.root = odm_tree.getroot()
        return self.root

    def parse_tree(self):
        self._register_namespaces()
        return ET.parse(self.odm_file)

    def _register_namespaces(self):
        for prefix, url in self.nsr.namespaces.items():
            ET.register_namespace(prefix, url)

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
