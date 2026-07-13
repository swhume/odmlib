"""Concrete loaders for standard ODM XML and JSON documents.

This module provides:

- :class:`JSONODMLoader` -- loads ODM-JSON files into the odmlib object model
- :class:`DictODMLoader` -- alias for JSONODMLoader (loads from Python dicts)
- :class:`XMLODMLoader` -- loads ODM-XML files into the odmlib object model

These loaders are typically used via the :class:`~odmlib.loader.ODMLoader`
facade rather than directly.
"""
from __future__ import annotations
from typing import Any, Optional
import odmlib.document_loader as DL
import odmlib.odm_parser as P
import odmlib.ns_registry as NS
import json
import importlib
import xml.etree.ElementTree as ET
from odmlib.exceptions import OdmlibLoaderStateError, OdmlibParsingError

ODM_PREFIX = "odm:"
ODM_NS = {'odm': 'http://www.cdisc.org/ns/odm/v1.3'}

_DEFAULT_ODM_NS_URI = {
    "odm_1_3_2": "http://www.cdisc.org/ns/odm/v1.3",
    "odm_2_0": "http://www.cdisc.org/ns/odm/v2.0",
}


class JSONODMLoader(DL.DocumentLoader):
    """Loads ODM-JSON documents into the odmlib object model.

    Recursively parses JSON dictionaries and instantiates odmlib model
    classes based on dictionary keys matching class names.

    Args:
        model_package (str): Package name to load models from
            (default: "odm_1_3_2"). Options: "odm_1_3_2", "odm_2_0",
            "dataset_1_0_1", "ct_1_1_1".
    """

    def __init__(self, model_package: str = "odm_1_3_2") -> None:
        self.filename: Optional[str] = None
        self.odm_dict: dict = {}
        self.ODM = importlib.import_module(f"odmlib.{model_package}.model")

    def load_document(self, odm_dict: dict, key: str) -> Any:
        """Recursively load a dict into an odmlib object tree.

        Instantiates the odmlib class named ``key`` with scalar attributes
        from ``odm_dict``, then recurses into nested dicts (ODMObject) and
        lists of dicts (ODMListObject).

        Args:
            odm_dict (dict): Dictionary containing the element's data.
            key (str): Class name to instantiate from the model package.

        Returns:
            An odmlib element object populated from ``odm_dict``.
        """
        attrib = {k: value for k, value in odm_dict.items() if not isinstance(value, (list, dict))}
        elem_class = DL.resolve_model_class(self.ODM, key)
        odm_obj = elem_class(**attrib)
        odm_obj_items = elem_class._elems.items()
        for k, v in odm_obj_items:
            if type(v).__name__ == "ODMObject":
                if k in odm_dict:
                    odm_child_obj = self.load_document(odm_dict[k], k)
                    setattr(odm_obj, k, odm_child_obj)
            elif type(v).__name__ == "ODMListObject":
                if k in odm_dict:
                    for val in odm_dict[k]:
                        odm_child_obj = self.load_document(val, k)
                        getattr(odm_obj, k).append(odm_child_obj)
        return odm_obj

    def create_document(self, filename: str) -> dict:
        """Parse a JSON file and store its contents internally.

        Args:
            filename (str): Path to the ODM JSON file.

        Returns:
            dict: The parsed JSON as a Python dictionary.
        """
        self.filename = filename
        # utf-8-sig tolerates a UTF-8 BOM and avoids platform-default encodings
        with open(self.filename, encoding="utf-8-sig") as json_in:
            try:
                self.odm_dict = json.load(json_in)
            except json.JSONDecodeError as ex:
                raise OdmlibParsingError(
                    f"Unable to parse JSON document {self.filename}: {ex}",
                    hint="Verify the file contains valid JSON.",
                ) from ex
        return self.odm_dict

    def create_document_from_string(self, odm_string: str) -> dict:
        """Parse an ODM JSON string and store its contents internally.

        Args:
            odm_string (str): JSON string containing the ODM document.

        Returns:
            dict: The parsed JSON as a Python dictionary.
        """
        try:
            self.odm_dict = json.loads(odm_string)
        except json.JSONDecodeError as ex:
            raise OdmlibParsingError(
                f"Unable to parse JSON document from string: {ex}",
                hint="Verify the string contains valid JSON.",
            ) from ex
        return self.odm_dict

    def load_odm(self) -> Any:
        """Return the root ODM object loaded from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Returns:
            An odmlib ``ODM`` root object.

        Raises:
            OdmlibLoaderStateError: If no document has been loaded yet.
        """
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_odm",
                hint="Call loader.open_odm_document(filename) or loader.load_odm_string(json_string) first",
            )
        odm_odmlib = self.load_document(self.odm_dict, "ODM")
        return odm_odmlib

    def load_metadataversion(self, idx: int = 0) -> Any:
        """Return the MetaDataVersion at index ``idx`` from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Args:
            idx (int): Zero-based index of the MetaDataVersion (default: 0).

        Returns:
            A ``MetaDataVersion`` odmlib object.

        Raises:
            OdmlibLoaderStateError: If no document has been loaded yet.
        """
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_metadataversion",
                hint="Call loader.open_odm_document(filename) first",
            )
        mdv_dict = self.odm_dict["Study"][0]["MetaDataVersion"][idx]
        mdv_odmlib = self.load_document(mdv_dict, "MetaDataVersion")
        return mdv_odmlib

    def load_study(self, idx: int = 0) -> Any:
        """Return the Study at index ``idx`` from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Args:
            idx (int): Zero-based index of the Study (default: 0).

        Returns:
            A ``Study`` odmlib object.

        Raises:
            OdmlibLoaderStateError: If no document has been loaded yet.
        """
        if not self.odm_dict:
            raise OdmlibLoaderStateError(
                "create_document must be used to create the document before executing load_study",
                hint="Call loader.open_odm_document(filename) first",
            )
        study_dict = self.odm_dict["Study"][idx]
        study_odmlib = self.load_document(study_dict, "Study")
        return study_odmlib


class DictODMLoader(JSONODMLoader):
    """Loads odmlib objects from Python dictionaries (same as JSONODMLoader)."""

    pass


class XMLODMLoader(DL.DocumentLoader):
    """Loads ODM-XML documents into the odmlib object model.

    Parses XML using ElementTree and dynamically instantiates odmlib model
    classes based on element tag names.

    Args:
        model_package (str): Package name (default: ``"odm_1_3_2"``).
            Options: ``"odm_1_3_2"``, ``"odm_2_0"``, ``"dataset_1_0_1"``,
            ``"ct_1_1_1"``.
        ns_uri (Optional[str]): ODM default namespace URI. When ``None``
            (the default), the URI is derived from ``model_package``
            (``odm_1_3_2`` -> ``.../v1.3``, ``odm_2_0`` -> ``.../v2.0``;
            other packages fall back to ``.../v1.3``). Passing an explicit
            value overrides the derived default and is preserved as-is,
            which is useful for custom extensions or non-standard schema
            variants.
        local_model (bool): If True, ``model_package`` is a full module path.
        nsr: Optional pre-configured NamespaceRegistry instance.
    """

    def __init__(self, model_package: str = "odm_1_3_2", ns_uri: Optional[str] = None,
                 local_model: bool = False, nsr: Optional[Any] = None) -> None:
        self.filename: Optional[str] = None
        self.parser: Optional[Any] = None
        if local_model:
            self.ODM = importlib.import_module(f"{model_package}.model")
        else:
            self.ODM = importlib.import_module(f"odmlib.{model_package}.model")
        if ns_uri is None:
            ns_uri = _DEFAULT_ODM_NS_URI.get(model_package, "http://www.cdisc.org/ns/odm/v1.3")
        self.ns_uri = ns_uri
        if nsr is not None:
            self._set_namespace(nsr)
        else:
            # Mirror XMLDefineLoader.__init__: empty Borg view, no global
            # mutation at construction time. Registration is deferred to
            # create_document / create_document_from_string so that callers
            # who pre-registered prefixes (e.g. "mdr") don't have their
            # global "odm" mapping silently overwritten when ns_uri is a
            # non-canonical wrapper URI.
            self.nsr = NS.NamespaceRegistry()

    def load_document(self, elem: ET.Element, *args: Any) -> Any:
        """Recursively load an XML element into an odmlib object tree.

        Strips the namespace URI from the tag name, instantiates the
        matching odmlib class, and recurses into child elements.

        Args:
            elem (ET.Element): The XML element to load.
            *args: Unused; present for interface compatibility.

        Returns:
            An odmlib element object populated from ``elem``.
        """
        elem_name = elem.tag[elem.tag.find('}') + 1:]
        elem_class = DL.resolve_model_class(self.ODM, elem_name)
        if elem.text and not elem.text.isspace():
            attrib = {**elem.attrib, **{"_content": elem.text}}
            odm_obj = elem_class(**attrib)
        else:
            odm_obj = elem_class(**elem.attrib)
        odm_obj_dict = elem_class._elems.items()
        for k, v in odm_obj_dict:
            if type(v).__name__ == "ODMObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                e = elem.find(v.namespace + ":" + k, namespace)
                if e is not None:
                    odm_child_obj = self.load_document(e)
                    setattr(odm_obj, k, odm_child_obj)
            elif type(v).__name__ == "ODMListObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                for e in elem.findall(v.namespace + ":" + k, namespace):
                    odm_child_obj = self.load_document(e)
                    getattr(odm_obj, k).append(odm_child_obj)
        return odm_obj

    def create_document(self, filename: str, namespace_registry: Optional[Any] = None) -> ET.Element:
        """Parse an ODM XML file and store the parsed tree internally.

        Args:
            filename (str): Path to the ODM XML file.
            namespace_registry: Optional pre-configured
                :class:`~odmlib.ns_registry.NamespaceRegistry` instance.

        Returns:
            ET.Element: The root XML element of the parsed document.
        """
        self.filename = filename
        # Unconditional, mirroring XMLDefineLoader.create_document. Required
        # because __init__ no longer populates self.nsr with the odm prefix.
        self._set_namespace(namespace_registry)
        self.parser = P.ODMParser(self.filename, self.nsr)
        root = self.parser.parse()
        return root

    def create_document_from_string(self, odm_string: str, namespace_registry: Optional[Any] = None) -> ET.Element:
        """Parse an ODM XML string and store the parsed tree internally.

        Args:
            odm_string (str): XML string containing the ODM document.
            namespace_registry: Optional pre-configured
                :class:`~odmlib.ns_registry.NamespaceRegistry` instance.

        Returns:
            ET.Element: The root XML element of the parsed document.
        """
        self._set_namespace(namespace_registry)
        self.parser = P.ODMStringParser(odm_string, self.nsr)
        root = self.parser.parse()
        return root

    def _set_namespace(self, namespace_registry: Optional[Any]) -> None:
        """Configure the namespace registry for parsing.

        Args:
            namespace_registry: An existing
                :class:`~odmlib.ns_registry.NamespaceRegistry` to use, or
                ``None`` to register a new default ODM namespace using
                ``self.ns_uri`` (which was derived from ``model_package``
                or set explicitly in the constructor).
        """
        if namespace_registry is not None:
            self.nsr = namespace_registry
        else:
            self.nsr = NS.NamespaceRegistry(prefix="odm", uri=self.ns_uri, is_default=True)

    def load_odm(self) -> Any:
        """Return the root ODM object loaded from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Returns:
            An odmlib ``ODM`` root object.
        """
        root = self.parser.ODM()
        root_odmlib = self.load_document(root)
        return root_odmlib

    def load_metadataversion(self, idx: int = 0) -> Any:
        """Return the MetaDataVersion at index ``idx`` from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Args:
            idx (int): Zero-based index of the MetaDataVersion (default: 0).

        Returns:
            A ``MetaDataVersion`` odmlib object.
        """
        self.parser.set_namespaces(self.nsr)
        mdv = self.parser.MetaDataVersion()
        mdv_odmlib = self.load_document(mdv[idx])
        return mdv_odmlib

    def load_study(self, idx: int = 0) -> Any:
        """Return the Study at index ``idx`` from the stored document.

        Must be called after :meth:`create_document` or
        :meth:`create_document_from_string`.

        Args:
            idx (int): Zero-based index of the Study (default: 0).

        Returns:
            A ``Study`` odmlib object.
        """
        self.parser.set_namespaces(self.nsr)
        study = self.parser.Study()
        study_odmlib = self.load_document(study[idx])
        return study_odmlib
