
OID_SKIP_LIST = ["FileOID"]

class OIDRef:
    def __init__(self):
        self.oid = {}
        self.oid_ref = {}
        self._init_oid_ref()
        self.ref_def = {}
        self._init_ref_def()
        self.def_ref = {}
        self._init_def_ref()

    def add_oid(self, oid, element):
        """ ODMLIB expects all OIDs to be unique within the scope of an ODM document """
        if oid in self.oid:
            raise ValueError(f"OID {oid} is not unique - element {element}")
        self.oid[oid] = element

    def add_oid_ref(self, oid, attr):
        self.oid_ref[attr].add(oid)

    def check_oid_refs(self):
        for attr, oid_set in self.oid_ref.items():
            for oid in oid_set:
                if attr not in OID_SKIP_LIST:
                    if oid not in self.oid:
                        raise ValueError(f"OID {oid} referenced in the attribute {attr} is not found.")
                    elif self.ref_def.get(attr) != self.oid.get(oid):
                        raise ValueError(f"OID reference for attribute {attr} element types do not match: "
                                         f"{self.ref_def.get(attr)} and {self.oid.get(oid)}")
        return True

    def check_unreferenced_oids(self):
        """ identify ELEMENTS that are defined but not used """
        orphans = {}
        for oid, elem in self.oid.items():
            for ref in self.def_ref[elem]:
                if oid not in self.oid_ref[ref]:
                    orphans[oid] = ref
        return orphans

    def _init_oid_ref(self):
        self.oid_ref["MetaDataVersionOID"] = set()
        self.oid_ref["StudyOID"] = set()
        self.oid_ref["StudyEventOID"] = set()
        self.oid_ref["FormOID"] = set()
        self.oid_ref["ItemGroupOID"] = set()
        self.oid_ref["ItemOID"] = set()
        self.oid_ref["MethodOID"] = set()
        self.oid_ref["CollectionExceptionConditionOID"] = set()
        self.oid_ref["PresentationOID"] = set()
        self.oid_ref["RoleCodeListOID"] = set()
        self.oid_ref["MeasurementUnitOID"] = set()
        self.oid_ref["CodeListOID"] = set()
        self.oid_ref["LocationOID"] = set()
        self.oid_ref["FileOID"] = set()
        self.oid_ref["PriorFileOID"] = set()
        self.oid_ref["ArchiveLayoutOID"] = set()
        self.oid_ref["WhereClauseOID"] = set()
        self.oid_ref["ValueListOID"] = set()
        self.oid_ref["CommentOID"] = set()

    def _init_ref_def(self):
        self.ref_def["MetaDataVersionOID"] = "MetaDataVersion"
        self.ref_def["StudyOID"] = "Study"
        self.ref_def["ItemGroupOID"] = "ItemGroupDef"
        self.ref_def["ItemOID"] = "ItemDef"
        self.ref_def["MethodOID"] = "MethodDef"
        self.ref_def["CodeListOID"] = "CodeList"
        self.ref_def["FileOID"] = "ODM"
        self.ref_def["PriorFileOID"] = "ODM"
        self.ref_def["LocationOID"] = "Location"
        self.ref_def["WhereClauseOID"] = "WhereClauseDef"
        self.ref_def["ValueListOID"] = "ValueListDef"
        self.ref_def["CommentOID"] = "CommentDef"

    def _init_def_ref(self):
        self.def_ref["MetaDataVersion"] = ["MetaDataVersionOID"]
        self.def_ref["Study"] = ["StudyOID"]
        self.def_ref["ItemGroupDef"] = ["ItemGroupOID"]
        self.def_ref["ItemDef"] = ["ItemOID"]
        self.def_ref["MethodDef"] = ["MethodOID"]
        self.def_ref["CodeList"] = ["CodeListOID"]
        self.def_ref["ConditionDef"] = ["CollectionExceptionConditionOID"]
        self.def_ref["Presentation"] = ["PresentationOID"]
        self.def_ref["ODM"] = ["FileOID", "PriorFileOID"]
        self.def_ref["Location"] = ["LocationOID"]
        self.def_ref["WhereClauseDef"] = ["WhereClauseOID"]
        self.def_ref["ValueListDef"] = ["ValueListOID"]
        self.def_ref["CommentDef"] = ["CommentOID"]
