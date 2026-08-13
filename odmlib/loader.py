"""Facade loader for ODM, Define-XML, and ARM documents.

This module provides :class:`ODMLoader`, a unified interface that wraps
any specialized loader (:class:`~odmlib.odm_loader.XMLODMLoader`,
:class:`~odmlib.odm_loader.JSONODMLoader`,
:class:`~odmlib.define_loader.XMLDefineLoader`,
:class:`~odmlib.define_loader.JSONDefineLoader`,
:class:`~odmlib.arm_loader.XMLArmLoader`, or
:class:`~odmlib.arm_loader.JSONArmLoader`) and delegates all
document loading operations to it.
"""
from __future__ import annotations
from typing import Any, Optional
import odmlib.document_loader as DL
import odmlib.ns_registry as NS
from odmlib.exceptions import OdmlibTypeError


class ODMLoader:
    """Facade providing a unified interface for loading ODM documents.

    Wraps a specialized loader (:class:`~odmlib.odm_loader.XMLODMLoader`,
    :class:`~odmlib.odm_loader.JSONODMLoader`,
    :class:`~odmlib.define_loader.XMLDefineLoader`,
    :class:`~odmlib.define_loader.JSONDefineLoader`,
    :class:`~odmlib.arm_loader.XMLArmLoader`, or
    :class:`~odmlib.arm_loader.JSONArmLoader`) and delegates
    all operations to it.

    Args:
        odm_loader (DocumentLoader): A specialized loader instance.

    Raises:
        OdmlibTypeError: If ``odm_loader`` is not a DocumentLoader instance.

    Example::

        import odmlib.odm_loader as OL
        import odmlib.loader as LD

        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
        loader.open_odm_document("study.xml")
        odm = loader.root()
        mdv = loader.MetaDataVersion()
    """

    def __init__(self, odm_loader: DL.DocumentLoader) -> None:
        if not isinstance(odm_loader, DL.DocumentLoader):
            raise OdmlibTypeError(
                "odm_loader argument must implement DocumentLoader",
                expected_type="DocumentLoader",
                actual_value=type(odm_loader).__name__,
                hint="Pass an instance of XMLODMLoader, JSONODMLoader, XMLDefineLoader, JSONDefineLoader, XMLArmLoader, or JSONArmLoader",
            )
        self.loader = odm_loader
        self._ns_snapshot: Optional[dict] = None

    def _bind_namespaces(self, odm_obj: Any) -> Any:
        """Attach the document-open-time namespace snapshot to *odm_obj*.

        The NamespaceRegistry is shared process-wide, so opening another
        document later can change it; binding a snapshot lets write_xml /
        to_xml_string serialize this document with the namespaces it was
        actually loaded under.
        """
        if odm_obj is not None:
            NS.bind_document_namespaces(odm_obj, snapshot=self._ns_snapshot)
        return odm_obj

    def create_odmlib(self, odm_doc: Any, odm_key: Optional[str] = None) -> Any:
        """Load an odmlib object from an existing document dict or element.

        Delegates to the wrapped loader's ``load_document`` method.

        Args:
            odm_doc: The document dict (JSON loaders) or XML Element
                (XML loaders) to load from.
            odm_key: The element key/class name to use when loading from
                a dict (JSON loaders only).

        Returns:
            An odmlib element object populated from ``odm_doc``.
        """
        odm_obj = self.loader.load_document(odm_doc, odm_key)
        return self._bind_namespaces(odm_obj)

    def open_odm_document(self, filename: str) -> Any:
        """Parse an ODM document file and prepare for loading.

        Args:
            filename (str): Path to the ODM XML or JSON file.

        Returns:
            The parsed root element or dict, depending on the loader type.
        """
        root = self.loader.create_document(filename)
        self._ns_snapshot = NS.NamespaceRegistry().snapshot()
        return root

    def load_odm_string(self, odm_string: str) -> Any:
        """Parse an ODM document from a string and prepare for loading.

        Args:
            odm_string (str): XML or JSON string containing the ODM document.

        Returns:
            The parsed root element or dict, depending on the loader type.
        """
        root = self.loader.create_document_from_string(odm_string)
        self._ns_snapshot = NS.NamespaceRegistry().snapshot()
        return root

    def root(self) -> Any:
        """Return the root ODM element.

        Must be called after :meth:`open_odm_document` or
        :meth:`load_odm_string`.

        Returns:
            The root odmlib ODM object (e.g., an ``ODM`` instance).
        """
        odm = self.loader.load_odm()
        return self._bind_namespaces(odm)

    def MetaDataVersion(self, idx: int = 0) -> Any:
        """Return the MetaDataVersion at the specified index.

        Must be called after :meth:`open_odm_document` or
        :meth:`load_odm_string`.

        Args:
            idx (int): Zero-based index of the MetaDataVersion to return
                (default: 0, the first one).

        Returns:
            A ``MetaDataVersion`` odmlib object.
        """
        mdv = self.loader.load_metadataversion(idx)
        return self._bind_namespaces(mdv)

    def Study(self, idx: int = 0) -> Any:
        """Return the Study at the specified index.

        Must be called after :meth:`open_odm_document` or
        :meth:`load_odm_string`.

        Args:
            idx (int): Zero-based index of the Study to return
                (default: 0, the first one).

        Returns:
            A ``Study`` odmlib object.
        """
        study = self.loader.load_study(idx)
        return self._bind_namespaces(study)

    def __getattr__(self, attr: str) -> Any:
        """Delegate unknown method calls to the wrapped loader.

        Allows calling loader-specific methods (e.g., ``load_odm_dataset``)
        directly on the facade without explicitly exposing them.

        Args:
            attr (str): Name of the attribute or method to look up.

        Returns:
            The callable attribute from the wrapped loader.

        Raises:
            AttributeError: If the attribute does not exist on the loader,
                or exists but is not callable.
        """
        if hasattr(self.loader, attr):
            load_func = getattr(self.loader, attr, None)
            if callable(load_func):
                return load_func
            else:
                raise AttributeError(f"{attr} is not callable in the loader {self.loader.__class__.__name__}")
        else:
            raise AttributeError(f"The {attr} method does not exist in the loader {self.loader.__class__.__name__}")
