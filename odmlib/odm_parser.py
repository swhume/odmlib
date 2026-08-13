import os
import xml.etree.ElementTree as ET
import xmlschema as XSD
import odmlib.ns_registry as NS
from abc import ABC, abstractmethod
from typing import Optional
import json
from . import schema_manager as SM
from odmlib.exceptions import OdmlibParsingError
from odmlib.exceptions import OdmlibSchemaValidationError  # noqa: F401  re-exported

ODM_NS = {'odm': 'http://www.cdisc.org/ns/odm/v1.3'}
ODM_PREFIX = "odm:"

# compiled XSDs are expensive (the ODM/Define schemas import many
# sub-schemas); cache them by path so validating many files does not
# recompile the schema per ODMSchemaValidator instance
_SCHEMA_CACHE: dict = {}


def _compiled_schema(xsd_file):
    if xsd_file not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[xsd_file] = XSD.XMLSchema(xsd_file)
    return _SCHEMA_CACHE[xsd_file]


class _DoctypeFound(Exception):
    pass


class _PrologScanned(Exception):
    pass


def _reject_doctype(chunks):
    """Scan the XML prolog and raise if a DOCTYPE declaration is present.

    ODM documents never need a DTD, and internal entity definitions enable
    entity-expansion denial-of-service attacks (billion laughs / quadratic
    blowup) that the stdlib parser does not defend against. A DOCTYPE can
    only appear before the root element, so scanning stops as soon as the
    root element opens; a malformed prolog is left for the real parser to
    report.

    Args:
        chunks: Iterable of str or bytes chunks of the document.
    """
    from xml.parsers import expat

    parser = expat.ParserCreate()

    def _on_doctype(name, sysid, pubid, has_internal_subset):
        raise _DoctypeFound

    def _on_root_element(name, attrs):
        raise _PrologScanned

    parser.StartDoctypeDeclHandler = _on_doctype
    parser.StartElementHandler = _on_root_element
    try:
        chunk = b""
        for chunk in chunks:
            parser.Parse(chunk, False)
        parser.Parse(b"" if isinstance(chunk, bytes) else "", True)
    except _PrologScanned:
        return
    except _DoctypeFound:
        raise OdmlibParsingError(
            "DOCTYPE declarations are not allowed in ODM documents",
            hint="Remove the <!DOCTYPE ...> declaration; DTDs enable "
                 "entity-expansion attacks and are never required by ODM.",
        ) from None
    except expat.ExpatError:
        return


def _reject_doctype_in_file(odm_file):
    """Run :func:`_reject_doctype` over a file path (skips file-like objects)."""
    if not isinstance(odm_file, (str, bytes, os.PathLike)):
        return
    with open(odm_file, "rb") as xml_in:
        _reject_doctype(iter(lambda: xml_in.read(65536), b""))


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
    def __init__(self, xsd_file=None, standard: Optional[str] = None,
                 version: Optional[str] = None):
        """Initialize the ODM schema validator.

        Provide either an explicit ``xsd_file`` path, or both ``standard``
        and ``version`` so the packaged schema can be resolved via
        :func:`odmlib.schema_manager.get_schema_path`.

        Users with custom or local schemas (anything not registered in
        :data:`odmlib.schema_manager._MAIN_SCHEMA`) should pass
        ``xsd_file=<path>`` directly — the ``(standard, version)`` lookup
        only resolves to the schemas bundled with odmlib.

        Args:
            xsd_file: Optional path to an XSD file. When provided, takes
                precedence and ``standard``/``version`` are ignored. This is
                the supported entry point for custom/local schemas.
            standard: Standard name (e.g. ``"odm"``, ``"define"``). Required
                together with ``version`` when ``xsd_file`` is omitted.
            version: Version string (e.g. ``"1.3.2"``, ``"2.1"``). Required
                together with ``standard`` when ``xsd_file`` is omitted.

        Raises:
            ValueError: If ``xsd_file`` is not provided and ``standard``
                and ``version`` are not both provided. Previously this
                silently fell back to ODM 1.3.2, which could mask schema
                version mismatches; an explicit choice is now required.
        """
        if xsd_file is None:
            if standard is None or version is None:
                raise ValueError(
                    "ODMSchemaValidator requires either an 'xsd_file' path, "
                    "or both 'standard' and 'version' to look up a packaged "
                    "schema. Got xsd_file=None, "
                    f"standard={standard!r}, version={version!r}. "
                    "Hint: for a packaged schema pass e.g. "
                    "standard='odm', version='1.3.2' (ODM 1.3.2) or "
                    "standard='define', version='2.1' (Define-XML 2.1). "
                    "For a custom or local schema not bundled with odmlib, "
                    "pass xsd_file='/path/to/your/schema.xsd' instead."
                )
            xsd_file = SM.get_schema_path(standard, version)
        self.xsd = _compiled_schema(str(xsd_file))

    def validate_tree(self, tree):
        result = self.xsd.is_valid(tree)
        return result

    def validate_file(self, odm_file):
        try:
            result = self.xsd.validate(odm_file)
        except XSD.validators.exceptions.XMLSchemaChildrenValidationError as ex:
            raise OdmlibSchemaValidationError(ex)
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
        self.nsr = None
        self.root = None
        self.mdv = []
        self.admin_data = []
        self.clinical_data = []

    def set_namespaces(self, ns_registry):
        self.nsr = ns_registry

    def ODM(self):
        return self.root

    def Study(self):
        if self.nsr:
            study = self.root.findall(ODM_PREFIX + "Study", self.nsr.default_namespace)
        else:
            study = self.root.findall(ODM_PREFIX + "Study", ODM_NS)
        return study

    def MetaDataVersion(self, idx=0):
        if self.nsr:
            study = self.root.findall(ODM_PREFIX + "Study", self.nsr.default_namespace)
            self.mdv = study[idx].findall(ODM_PREFIX + "MetaDataVersion", self.nsr.default_namespace)
        else:
            study = self.root.findall(ODM_PREFIX + "Study", ODM_NS)
            self.mdv = study[idx].findall(ODM_PREFIX + "MetaDataVersion", ODM_NS)
        return self.mdv

    def AdminData(self):
        ns = self.nsr.default_namespace if self.nsr else ODM_NS
        self.admin_data = self.root.findall(ODM_PREFIX + "AdminData", ns)
        return self.admin_data

    def ClinicalData(self):
        ns = self.nsr.default_namespace if self.nsr else ODM_NS
        self.clinical_data = self.root.findall(ODM_PREFIX + "ClinicalData", ns)
        return self.clinical_data

    def ReferenceData(self):
        ns = self.nsr.default_namespace if self.nsr else ODM_NS
        self.reference_data = self.root.findall(ODM_PREFIX + "ReferenceData", ns)
        return self.reference_data


class ODMParser(BaseParser, ElementParser):
    def __init__(self, odm_file, namespace_registry=None):
        self.odm_file = odm_file
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        self.register_namespaces()
        _reject_doctype_in_file(self.odm_file)
        try:
            odm_tree = ET.parse(self.odm_file)
        except ET.ParseError as ex:
            raise OdmlibParsingError(
                f"Unable to parse XML document {self.odm_file}: {ex}",
                hint="Verify the file is well-formed XML.",
            ) from ex
        self.root = odm_tree.getroot()
        return self.root

    def parse_tree(self):
        self.register_namespaces()
        _reject_doctype_in_file(self.odm_file)
        try:
            return ET.parse(self.odm_file)
        except ET.ParseError as ex:
            raise OdmlibParsingError(
                f"Unable to parse XML document {self.odm_file}: {ex}",
                hint="Verify the file is well-formed XML.",
            ) from ex


class ODMStringParser(BaseParser, ElementParser):
    def __init__(self, odm_string, namespace_registry=None):
        self.odm_string = odm_string
        super().__init__(ns_registry=namespace_registry)

    def parse(self):
        self.register_namespaces()
        _reject_doctype([self.odm_string])
        try:
            self.root = ET.fromstring(self.odm_string)
        except ET.ParseError as ex:
            raise OdmlibParsingError(
                f"Unable to parse XML document from string: {ex}",
                hint="Verify the string is well-formed XML.",
            ) from ex
        return self.root

    def parse_tree(self):
        self.register_namespaces()
        _reject_doctype([self.odm_string])
        try:
            return ET.fromstring(self.odm_string)
        except ET.ParseError as ex:
            raise OdmlibParsingError(
                f"Unable to parse XML document from string: {ex}",
                hint="Verify the string is well-formed XML.",
            ) from ex


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
