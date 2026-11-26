"""Abstract base class for all odmlib document loaders.

Defines the interface that all concrete loaders
(:class:`~odmlib.odm_loader.XMLODMLoader`,
:class:`~odmlib.odm_loader.JSONODMLoader`,
:class:`~odmlib.define_loader.XMLDefineLoader`,
:class:`~odmlib.define_loader.JSONDefineLoader`,
:class:`~odmlib.arm_loader.XMLArmLoader`,
:class:`~odmlib.arm_loader.JSONArmLoader`).

Loaders are not typically used directly; pass an instance to
:class:`~odmlib.loader.ODMLoader` for a unified facade.
"""
from abc import ABC, abstractmethod

from odmlib.exceptions import OdmlibParsingError


def resolve_model_class(model_module, elem_name):
    """Return the model class for an element tag, or raise a clear error.

    Previously an unknown element in a document surfaced as a bare
    ``AttributeError`` from ``getattr`` deep inside the recursive load.

    Args:
        model_module: The imported model module (e.g. odmlib.odm_1_3_2.model).
        elem_name: The element tag / dict key naming the class.

    Raises:
        OdmlibParsingError: If the model has no class for ``elem_name``.
    """
    try:
        return getattr(model_module, elem_name)
    except AttributeError:
        raise OdmlibParsingError(
            f"Unknown element '{elem_name}' — the "
            f"{model_module.__name__} model has no matching class",
            hint="Check that the document matches the loader's model_package, "
                 "or use a custom extension model (local_model) that defines "
                 "this element.",
        ) from None


def register_model_namespaces(model_module):
    """Register the auxiliary namespace prefixes *model_module* declares.

    Calls the module's ``register_namespaces()`` (every bundled model has one, as
    of 0.3.0). A custom extension model without one is left alone.
    """
    register = getattr(model_module, "register_namespaces", None)
    if callable(register):
        register()


def child_namespace(ns_map, prefix, elem_class, child_name):
    """Return the ``{prefix: uri}`` map for an ElementTree ``find`` of a child.

    Args:
        ns_map: ``{prefix: uri}`` the document is being read with -- the snapshot
            a loader took when it opened the document.
        prefix: The child descriptor's namespace prefix.
        elem_class: The parent's model class, for the error message.
        child_name: The child element's local name, for the error message.

    Raises:
        OdmlibParsingError: If *prefix* is not in *ns_map*. ElementTree would
            otherwise raise a bare ``SyntaxError`` ("prefix ... not found").
    """
    uri = ns_map.get(prefix)
    if uri is None:
        raise OdmlibParsingError(
            f"Cannot read {elem_class.__name__}/{prefix}:{child_name}: the namespace "
            f"prefix '{prefix}' is not registered",
            hint=f"Register it before loading, e.g. NamespaceRegistry(prefix='{prefix}', "
                 f"uri='...'). NamespaceRegistry.reset() also removes the prefixes model "
                 f"packages register on import.",
        )
    return {prefix: uri}


def element_content(elem, elem_class):
    """Return the ``_content`` to load for XML element *elem*, or None for no content.

    Text with any non-whitespace character is always content. Whitespace-only text
    is content only for a class that models ``_content`` and an element with no
    child elements: ``<CheckValue> </CheckValue>`` carries a real value, while the
    whitespace before a child element is indentation.
    """
    text = elem.text
    if text is None:
        return None
    if not text.isspace():
        return text
    if "_content" in elem_class._fields and len(elem) == 0:
        return text
    return None


class DocumentLoader(ABC):
    """Abstract base class for odmlib document loaders.

       All concrete loaders implement this interface so they can be wrapped
       by the :class:`~odmlib.loader.ODMLoader` facade.
       """

    @abstractmethod
    def load_document(self, doc):
        """Recursively load a parsed document element or dict into odmlib objects.

        Args:
            doc: An XML ``Element`` (XML loaders) or ``dict`` (JSON loaders).

        Returns:
            An odmlib element object populated from ``doc``.
        """
        raise NotImplementedError("Attempted to execute an abstract method load_document in the DocumentLoader class")

    @abstractmethod
    def create_document(self, filename):
        """Parse a document file and store its contents internally.

        Args:
            filename (str): Path to the ODM file (XML or JSON).

        Returns:
            The parsed root element or dict.
        """
        raise NotImplementedError("Attempted to execute an abstract method create_document in the DocumentLoader class")

    @abstractmethod
    def create_document_from_string(self, odm_string):
        """Parse a document string and store its contents internally.

          Args:
              odm_string (str): XML or JSON string containing the ODM document.

          Returns:
              The parsed root element or dict.
          """
        raise NotImplementedError("Attempted to execute an abstract method create_document_from_string in the DocumentLoader class")

    @abstractmethod
    def load_metadataversion(self, idx):
        """Return the MetaDataVersion at the given index.

        Args:
            idx (int): Zero-based index of the MetaDataVersion to return.

        Returns:
            A ``MetaDataVersion`` odmlib object.
        """
        raise NotImplementedError("Attempted to execute an abstract method load_metadataversion in the DocumentLoader class")

    @abstractmethod
    def load_study(self, idx):
        """Return the Study at the given index.

        Args:
            idx (int): Zero-based index of the Study to return.

        Returns:
            A ``Study`` odmlib object.
        """

    @abstractmethod
    def load_odm(self):
        """Return the root ODM element loaded from the stored document.

        Returns:
            The root odmlib ``ODM`` object.
        """
        raise NotImplementedError("Attempted to execute an abstract method load_odm in the DocumentLoader class")

    def _ns_map(self):
        """The ``{prefix: uri}`` map an XML loader resolves child elements with.

        The snapshot the loader took when it opened the document (``_doc_namespaces``),
        so opening another document -- which changes the process-wide registry -- cannot
        change how this one is read. An element handed to ``load_document`` without
        opening a document falls back to the live registry.

        .. versionadded:: 0.3.0
        """
        snapshot = getattr(self, "_doc_namespaces", None)
        return snapshot if snapshot is not None else self.nsr.namespaces
