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
