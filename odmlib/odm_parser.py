"""XML and JSON parsers for ODM documents.

This module provides parsers that sit between raw file I/O and the odmlib
object model:

- :class:`SchemaValidator` / :class:`ODMSchemaValidator` -- validate XML
  documents against the official CDISC XSD schemas using ``xmlschema``.
- :class:`BaseParser` -- shared ElementTree namespace setup and dynamic
  element-parsing via ``__getattr__``.
- :class:`ElementParser` -- element-access helpers (ODM, Study,
  MetaDataVersion, ClinicalData, …) for XML-parsed documents.
- :class:`ODMParser` -- parses an ODM-XML *file* into an ElementTree root.
- :class:`ODMStringParser` -- parses an ODM-XML *string* into an ElementTree
  root.
- :class:`ODMJSONStringParser` -- parses an ODM-JSON *string* into a Python
  dict with the same element-access helpers.

These classes are used internally by the concrete loaders in
:mod:`odmlib.odm_loader`, :mod:`odmlib.define_loader`, and
:mod:`odmlib.arm_loader`.  Most application code should use those loaders
(or the :class:`~odmlib.loader.ODMLoader` facade) rather than the parsers
directly.
"""
import xml.etree.ElementTree as ET
import xmlschema as XSD
import odmlib.ns_registry as NS
from abc import ABC, abstractmethod
import json
from . import schema_manager as SM

ODM_NS = {'odm': 'http://www.cdisc.org/ns/odm/v1.3'}
ODM_PREFIX = "odm:"


class SchemaValidator(ABC):
    """Abstract base class for XSD schema validators."""

    @abstractmethod
    def validate_tree(self, tree):
        """Validate an ElementTree against the schema.

        Args:
            tree: An ``xml.etree.ElementTree.ElementTree`` object.

        Returns:
            bool: True if valid, False otherwise.
        """
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_tree in the Validator class")

    @abstractmethod
    def validate_file(self, xml_file):
        """Validate an XML file against the schema.

        Args:
            xml_file (str): Path to the XML file to validate.

        Raises:
            OdmlibSchemaValidationError: If the document is not valid.
        """
        raise NotImplementedError(
            "Attempted to execute an abstract method validate_file in the Validator class")


class OdmlibSchemaValidationError(Exception):
    """Raised when an XML document fails XSD schema validation."""


class ODMSchemaValidator(SchemaValidator):
    """Validates ODM XML documents against a CDISC XSD schema.

    Uses ``xmlschema`` to perform full XSD validation. Packaged schemas
    are resolved automatically by standard and version if no explicit
    ``xsd_file`` path is provided.

    Args:
        xsd_file (str, optional): Explicit path to an XSD file. When
            omitted, the schema is resolved from the odmlib package using
            ``standard`` and ``version``.
        standard (str): Standard name used for schema lookup
            (default: ``"odm"``).
        version (str): Standard version used for schema lookup
            (default: ``"1.3.2"``).

    Example::

        validator = ODMSchemaValidator()
        is_valid = validator.validate_tree(ET.parse("study.xml"))
        validator.validate_file("study.xml")   # raises on failure
    """

    def __init__(self, xsd_file=None, standard: str = "odm", version: str = "1.3.2"):
        if xsd_file is None:
            xsd_file = SM.get_schema_path(standard, version)
        self.xsd = XSD.XMLSchema(xsd_file)

    def validate_tree(self, tree):
        """Validate an ElementTree against the XSD schema.

        Args:
            tree: An ``xml.etree.ElementTree.ElementTree`` object.

        Returns:
            bool: True if valid, False otherwise.
        """
        result = self.xsd.is_valid(tree)
        return result

    def validate_file(self, odm_file):
        """Validate an XML file against the XSD schema.

        Args:
            odm_file (str): Path to the XML file to validate.

        Returns:
            None on success.

        Raises:
            OdmlibSchemaValidationError: If the document fails validation.
        """
        try:
            result = self.xsd.validate(odm_file)
        except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ex:
            raise OdmlibSchemaValidationError(ex)
        return result


class BaseParser:
    """Base mixin providing namespace registration and dynamic element access.

    Registers all known namespaces with ElementTree so that XML serialization
    uses the correct prefixes. The ``__getattr__`` hook allows callers to
    dynamically retrieve any child elements by name::

        items = parser.ItemDef(parent=study_elem)

    Args:
        ns_registry: A :class:`~odmlib.ns_registry.NamespaceRegistry`
            instance, or ``None`` to create a default ODM 1.3.2 registry.
    """

    def __init__(self, ns_registry):
        if ns_registry:
            self.nsr = ns_registry
        else:
            self.nsr = NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)

    def register_namespaces(self):
        """Register all namespaces from the registry with ElementTree."""
        for prefix, url in self.nsr.namespaces.items():
            ET.register_namespace(prefix, url)

    def __getattr__(self, item):
        """Dynamically find child elements by name under a given parent.

        Returns a callable that searches ``parent`` for ``<ns_prefix:item>``
        elements and returns a list of attribute dicts (with ``"elem"`` key).

        Args:
            item (str): The element tag name to search for.

        Returns:
            callable: A function accepting ``parent`` and ``ns_prefix``
                keyword arguments.
        """
        def parse_method(*args, parent, ns_prefix="odm", **kwargs):
            elem_list = []
            for elem in parent.findall(ns_prefix + ":" + item, self.nsr.get_ns_entry_dict(ns_prefix)):
                elem_list.append({**elem.attrib, "elem": elem})
            return elem_list
        return parse_method


class ElementParser:
    """Mixin providing named element-access helpers for a parsed XML document.

    Works with :class:`BaseParser` subclasses (via multiple inheritance) to
    provide convenient access to top-level ODM elements from the root.
    """

    def __init__(self):
        self.nsr = None
        self.root = None
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []

    def set_namespaces(self, ns_registry):
        """Set the namespace registry to use for element lookups.

        Args:
            ns_registry: A :class:`~odmlib.ns_registry.NamespaceRegistry` instance.
        """
        self.nsr = ns_registry

    def ODM(self):
        """Return the root ODM XML element.

        Returns:
            ET.Element: The root ``<ODM>`` element.
        """
        return self.root

    def Study(self):
        """Return all ``<Study>`` elements from the root.

        Returns:
            list[ET.Element]: All Study elements.
        """
        if self.nsr:
            study = self.root.findall(ODM_PREFIX + "Study", self.nsr.default_namespace)
        else:
            study = self.root.findall(ODM_PREFIX + "Study", ODM_NS)
        return study

    def MetaDataVersion(self, idx=0):
        """Return all ``<MetaDataVersion>`` elements for the Study at ``idx``.

        Args:
            idx (int): Zero-based index of the Study to look in (default: 0).

        Returns:
            list[ET.Element]: All MetaDataVersion elements in that Study.
        """
        if self.nsr:
            study = self.root.findall(ODM_PREFIX + "Study", self.nsr.default_namespace)
            self.mdv = study[idx].findall(ODM_PREFIX + "MetaDataVersion", self.nsr.default_namespace)
        else:
            study = self.root.findall(ODM_PREFIX + "Study", ODM_NS)
            self.mdv = study[idx].findall(ODM_PREFIX + "MetaDataVersion", ODM_NS)
        return self.mdv

    def AdminData(self):
        """Return all ``<AdminData>`` elements from the root.

        Returns:
            list[ET.Element]: All AdminData elements.
        """
        self.admin_data = self.root.findall(ODM_PREFIX + "AdminData", ODM_NS)
        return self.admin_data

    def ClinicalData(self):
        """Return all ``<ClinicalData>`` elements from the root.

        Returns:
            list[ET.Element]: All ClinicalData elements.
        """
        self.clinical_data = self.root.findall(ODM_PREFIX + "ClinicalData", ODM_NS)
        return self.clinical_data

    def ReferenceData(self):
        """Return all ``<ReferenceData>`` elements from the root.

        Returns:
            list[ET.Element]: All ReferenceData elements.
        """
        self.reference_data = self.root.findall(ODM_PREFIX + "ReferenceData", ODM_NS)
        return self.reference_data


class ODMParser(BaseParser, ElementParser):
    """Parses an ODM-XML file into an ElementTree root.

    Args:
        odm_file (str): Path to the ODM XML file.
        namespace_registry: Optional pre-configured
            :class:`~odmlib.ns_registry.NamespaceRegistry` instance.
    """

    def __init__(self, odm_file, namespace_registry=None):
        self.odm_file = odm_file
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        """Parse the ODM file and return the root element.

        Returns:
            ET.Element: The root ``<ODM>`` element.
        """
        self.register_namespaces()
        odm_tree = ET.parse(self.odm_file)
        self.root = odm_tree.getroot()
        return self.root

    def parse_tree(self):
        """Parse the ODM file and return the full ElementTree.

        Returns:
            ET.ElementTree: The parsed document tree.
        """
        self.register_namespaces()
        return ET.parse(self.odm_file)


class ODMStringParser(BaseParser, ElementParser):
    """Parses an ODM-XML string into an ElementTree root.

    Args:
        odm_string (str): XML string containing the ODM document.
        namespace_registry: Optional pre-configured
            :class:`~odmlib.ns_registry.NamespaceRegistry` instance.
    """

    def __init__(self, odm_string, namespace_registry=None):
        self.odm_string = odm_string
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        """Parse the ODM string and return the root element.

        Returns:
            ET.Element: The root ``<ODM>`` element.
        """
        self.register_namespaces()
        self.root = ET.fromstring(self.odm_string)
        return self.root

    def parse_tree(self):
        """Parse the ODM string and return the root element as a tree.

        Returns:
            ET.Element: The root element.
        """
        self.register_namespaces()
        return ET.fromstring(self.odm_string)


class ODMJSONStringParser:
    """Parses an ODM-JSON string into a Python dict with element-access helpers.

    Args:
        odm_string (str): JSON string containing the ODM document.
    """

    def __init__(self, odm_string):
        self.root = json.loads(odm_string)
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []
        self.reference_data = []

    def parse(self):
        """Return the parsed JSON dict (already done in ``__init__``).

        Returns:
            dict: The full ODM document as a Python dictionary.
        """
        return self.root

    def ODM(self):
        """Return the root ODM dict.

        Returns:
            dict: The full ODM document dict.
        """
        return self.root

    def Study(self):
        """Return the list of Study dicts.

        Returns:
            list[dict]: All Study entries.
        """
        study = self.root["Study"]
        return study

    def MetaDataVersion(self):
        """Return the list of MetaDataVersion dicts for the first Study.

        Returns:
            list[dict]: All MetaDataVersion entries in the first Study.
        """
        study = self.root["Study"]
        self.mdv = study[0]["MetaDataVersion"]
        return self.mdv

    def AdminData(self):
        """Return the list of AdminData dicts.

        Returns:
            list[dict]: All AdminData entries.
        """
        self.admin_data = self.root["AdminData"]
        return self.admin_data

    def ClinicalData(self):
        """Return the list of ClinicalData dicts.

        Returns:
            list[dict]: All ClinicalData entries.
        """
        self.clinical_data = self.root["ClinicalData"]
        return self.clinical_data

    def ReferenceData(self):
        """Return the list of ReferenceData dicts.

        Returns:
            list[dict]: All ReferenceData entries.
        """
        self.reference_data = self.root["ReferenceData"]
        return self.reference_data
