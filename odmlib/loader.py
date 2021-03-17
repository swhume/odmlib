import odmlib.document_loader as DL


class ODMLoader:
    """ loads an ODM-XML document into the object model """
    def __init__(self, odm_loader):
        if not isinstance(odm_loader, DL.DocumentLoader):
            raise TypeError("odm_loader argument must implement DocumentLoader")
        self.loader = odm_loader

    def create_odmlib(self, odm_doc, odm_key=None):
        odm_obj = self.loader.load_document(odm_doc, odm_key)
        return odm_obj

    def open_odm_document(self, filename):
        root = self.loader.create_document(filename)
        return root

    def load_odm_string(self, odm_string):
        root = self.loader.create_document_from_string(odm_string)
        return root

    def root(self):
        odm = self.loader.load_odm()
        return odm

    def MetaDataVersion(self, idx=0):
        mdv = self.loader.load_metadataversion(idx)
        return mdv

    def Study(self):
        study = self.loader.load_study()
        return study
