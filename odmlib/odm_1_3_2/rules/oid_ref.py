class OIDRef:
    def __init__(self, skip_attrs=None, skip_elems=None):
        self.oid = {}
        self.oid_ref = {}
        self._init_oid_ref()
        self.ref_def = {}
        self._init_ref_def()
        self.def_ref = {}
        self._init_def_ref()
        self.skip_attr = (skip_attrs if skip_attrs else []) + ["FileOID", "PriorFileOID"]
        self.skip_elem = (skip_elems if skip_elems else []) + ["ODM"]
        self.is_verified = False
        self.is_verified = False

    def add_oid(self, oid, element):
        """odmlib expects all OIDs to be unique within the scope of an ODM document"""
        if oid in self.oid:
            raise ValueError(f"OID {oid} is not unique - element {element}")
        if element not in self.skip_elem:
            self.oid[oid] = element

    def add_oid_ref(self, oid, attr):
        if attr not in self.skip_attr:
            self.oid_ref[attr].add(oid)

    def is_oids_verified(self):
        if self.oid and self.is_verified:
            return True
        else:
            return False

    def check_oid_refs(self):
        self.is_verified = True
        for attr, oid_set in self.oid_ref.items():
            for oid in oid_set:
                if oid not in self.oid:
                    raise ValueError(
                        f"OID {oid} referenced in the attribute {attr} is not found."
                    )
                elif self.ref_def.get(attr) != self.oid.get(oid):
                    raise ValueError(
                        f"OID reference for attribute {attr} element types do not match: "
                        f"{self.ref_def.get(attr)} and {self.oid.get(oid)}"
                    )
        return True

    def check_unreferenced_oids(self):
        """identify ELEMENTS that are defined but not used"""
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
        # self.oid_ref["FileOID"] = set()
        # self.oid_ref["PriorFileOID"] = set()
        self.oid_ref["ArchiveLayoutOID"] = set()
        self.oid_ref["UserOID"] = set()

    def _init_ref_def(self):
        self.ref_def["MetaDataVersionOID"] = "MetaDataVersion"
        self.ref_def["StudyOID"] = "Study"
        self.ref_def["StudyEventOID"] = "StudyEventDef"
        self.ref_def["FormOID"] = "FormDef"
        self.ref_def["ItemGroupOID"] = "ItemGroupDef"
        self.ref_def["ItemOID"] = "ItemDef"
        self.ref_def["MethodOID"] = "MethodDef"
        self.ref_def["CodeListOID"] = "CodeList"
        self.ref_def["CollectionExceptionConditionOID"] = "ConditionDef"
        self.ref_def["PresentationOID"] = "Presentation"
        self.ref_def["LocationOID"] = "Location"
        self.ref_def["ArchiveLayoutOID"] = "ArchiveLayout"
        self.ref_def["MeasurementUnitOID"] = "MeasurementUnit"
        self.ref_def["UserOID"] = "User"
        self.ref_def["SignatureOID"] = "SignatureRef"

    def _init_def_ref(self):
        self.def_ref["MetaDataVersion"] = ["MetaDataVersionOID"]
        self.def_ref["Study"] = ["StudyOID"]
        self.def_ref["StudyEventDef"] = ["StudyEventOID"]
        self.def_ref["FormDef"] = ["FormOID"]
        self.def_ref["ItemGroupDef"] = ["ItemGroupOID"]
        self.def_ref["ItemDef"] = ["ItemOID"]
        self.def_ref["MethodDef"] = ["MethodOID"]
        self.def_ref["CodeList"] = ["CodeListOID"]
        self.def_ref["ConditionDef"] = ["CollectionExceptionConditionOID"]
        self.def_ref["Presentation"] = ["PresentationOID"]
        self.def_ref["ODM"] = ["FileOID", "PriorFileOID"]
        self.def_ref["Location"] = ["LocationOID"]
        self.def_ref["ArchiveLayout"] = ["ArchiveLayoutOID"]
        self.def_ref["MeasurementUnit"] = ["MeasurementUnitOID"]
        self.def_ref["User"] = ["UserOID"]
        self.def_ref["UserRef"] = ["UserOID"]
        self.def_ref["FlagType"] = ["CodeListOID"]
        self.def_ref["FlagValue"] = ["CodeListOID"]
        self.def_ref["StudyEventData"] = ["StudyEventOID"]
        self.def_ref["FormData"] = ["FormOID"]
        self.def_ref["ItemGroupData"] = ["ItemGroupOID"]
        self.def_ref["ItemData"] = ["ItemOID"]
        self.def_ref["SiteRef"] = ["LocationOID"]
        self.def_ref["InvestigatorRef"] = ["UserOID"]
        self.def_ref["AdminData"] = ["StudyOID"]
        self.def_ref["SignatureRef"] = ["SignatureOID "]
        self.def_ref["Association"] = ["StudyOID", "MetaDataVersionOID"]
        self.def_ref["ReferenceData"] = ["StudyOID", "MetaDataVersionOID"]
        self.def_ref["ClinicalData"] = ["StudyOID", "MetaDataVersionOID"]
        self.def_ref["KeySet"] = [
            "StudyOID",
            "StudyEventOID",
            "FormOID",
            "ItemGroupOID",
            "ItemOID ",
        ]
