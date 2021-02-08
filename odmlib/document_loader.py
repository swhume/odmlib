from abc import ABC, abstractmethod


class DocumentLoader(ABC):
    @abstractmethod
    def load_document(self, doc):
        raise NotImplementedError("Attempted to execute an abstract method load_document in the DocumentLoader class")

    @abstractmethod
    def create_document(self, filename):
        raise NotImplementedError("Attempted to execute an abstract method create_document in the DocumentLoader class")

    @abstractmethod
    def load_metadataversion(self, idx):
        raise NotImplementedError("Attempted to execute an abstract method load_metadataversion in the DocumentLoader class")

    @abstractmethod
    def load_odm(self):
        raise NotImplementedError("Attempted to execute an abstract method load_odm in the DocumentLoader class")
