
class OIDIndex:
    def __init__(self):
        self.oid_index = {}

    def add_oid(self, oid, element):
        """ odmlib expects all OIDs to be unique within the scope of an ODM document """
        if oid not in self.oid_index:
            self.oid_index[oid] = []
        self.oid_index[oid].append(element)

    def find_all(self, oid):
        if not self.oid_index:
            raise ValueError(f"The OID index is empty. Build the index prior to using find_all. OID {oid} not found.")
        elif oid not in self.oid_index:
            raise ValueError(f"OID {oid} not found in the OID index.")
        return self.oid_index[oid]
