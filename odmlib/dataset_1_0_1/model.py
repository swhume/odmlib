import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="data", uri="http://www.cdisc.org/ns/Dataset-XML/v1.0")


class ItemData(OE.ODMElement):
    ItemOID = T.OIDRef(required=True)
    Value = T.String(required=False)


class ItemGroupData(OE.ODMElement):
    ItemGroupOID = T.OIDRef(required=True)
    ItemGroupDataSeq = T.PositiveInteger(required=True, namespace="data")
    ItemData = T.ODMListObject(required=False, element_class=ItemData)

    def __len__(self):
        return len(self.ItemData)

    def __getitem__(self, position):
        return self.ItemData[position]

    def __iter__(self):
        return iter(self.ItemData)


class ClinicalData(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)


class ReferenceData(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)


class ODM(OE.ODMElement):
    Description = T.String(required=False)
    FileType = T.ValueSetString(required=True)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    PriorFileOID = T.OIDRef(required=False)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    DatasetXMLVersion = T.ExtendedValidValues(required=True, valid_values=["1.0.0", "1.0.1"])
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    schemaLocation = T.String(required=False, namespace="xs")
    ReferenceData = T.ODMListObject(element_class=ReferenceData)
    ClinicalData = T.ODMObject(element_class=ClinicalData)
