import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


#: Namespace prefixes this model uses besides its default ``odm`` namespace.
AUXILIARY_NAMESPACES = {
    "xs": "http://www.w3.org/2001/XMLSchema-instance",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "data": "http://www.cdisc.org/ns/Dataset-XML/v1.0",
}


def register_namespaces():
    """Register the auxiliary namespace prefixes this model uses (not its default).

    The model registers them once, when it is imported, and
    ``NamespaceRegistry.reset()`` removes them again. The loaders call this from
    ``create_document`` so that a document loaded after a reset still resolves
    and declares these prefixes. Safe to call repeatedly. Registering the
    default namespace is the loader's job.

    .. versionadded:: 0.3.0
    """
    for prefix, uri in AUXILIARY_NAMESPACES.items():
        NS.NamespaceRegistry(prefix=prefix, uri=uri)


NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
register_namespaces()


class ItemData(OE.ODMElement):
    """A single data value for one item (variable) in a Dataset-XML document.

    Each ItemData element holds the actual collected or derived value for
    one variable in a row of tabular clinical data.

    Attributes:
        ItemOID (str, required): OID reference to the corresponding ItemDef
            in the associated ODM metadata.
        Value (str): The actual data value for this item. May be omitted
            when the item has no value for this row.
    """

    ItemOID = T.OIDRef(required=True)
    Value = T.String(required=False)


class ItemGroupData(OE.ODMElement):
    """One row (record) of data within a Dataset-XML dataset.

    Corresponds to a single observation row in a tabular dataset. Contains
    one ItemData child for every variable in that row that has a value.
    The ``data:ItemGroupDataSeq`` attribute provides the row number for
    ordering records within the dataset.

    Attributes:
        ItemGroupOID (str, required): OID reference to the ItemGroupDef that
            describes the dataset structure.
        ItemGroupDataSeq (int, required): Sequential row number for ordering
            records; stored in the ``data:`` namespace.
        ItemData (list): Zero or more ItemData children, each carrying one
            variable value for this row.
    """

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
    """A container for subject-level (clinical) tabular data in a Dataset-XML file.

    ClinicalData groups all ItemGroupData rows that belong to the same study
    and metadata version. It is used for SDTM/ADaM datasets containing
    actual subject observations.

    Attributes:
        StudyOID (str, required): OID reference to the Study in the
            associated ODM metadata.
        MetaDataVersionOID (str, required): OID reference to the
            MetaDataVersion that describes the dataset structure.
        ItemGroupData (list): Zero or more ItemGroupData rows.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)


class ReferenceData(OE.ODMElement):
    """A container for reference (non-subject) tabular data in a Dataset-XML file.

    ReferenceData is used for datasets that contain study-level reference
    information rather than per-subject observations, such as trial design
    or arm/epoch lookup tables.

    Attributes:
        StudyOID (str, required): OID reference to the Study in the
            associated ODM metadata.
        MetaDataVersionOID (str, required): OID reference to the
            MetaDataVersion that describes the dataset structure.
        ItemGroupData (list): Zero or more ItemGroupData rows.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)


class ODM(OE.ODMElement):
    """The root element of a Dataset-XML 1.0.1 document.

    A Dataset-XML file carries tabular clinical or reference data for
    submission. It references ODM metadata via StudyOID and
    MetaDataVersionOID and uses namespace
    ``http://www.cdisc.org/ns/Dataset-XML/v1.0`` (prefix ``data:``) for
    Dataset-XML-specific attributes such as ``ItemGroupDataSeq``.

    Attributes:
        Description (str): Human-readable description of the file.
        FileType (str, required): "Snapshot" or "Transactional".
        FileOID (str, required): Globally unique OID for this specific file.
        CreationDateTime (str, required): ISO 8601 datetime when the file
            was created.
        PriorFileOID (str): OID of the preceding file in a sequence.
        AsOfDateTime (str): ISO 8601 datetime indicating currency of the
            data.
        ODMVersion (str): Version of the base ODM standard being used.
        DatasetXMLVersion (str, required): Version of the Dataset-XML
            standard; one of "1.0.0" or "1.0.1".
        Originator (str): Organization that created the file.
        SourceSystem (str): Software system that generated the file.
        SourceSystemVersion (str): Version of the source system.
        schemaLocation (str): xs:schemaLocation attribute for schema
            validation.
        ReferenceData (list): Zero or more ReferenceData sections.
        ClinicalData: A single ClinicalData section.
    """

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
