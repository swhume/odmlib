import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


#: Namespace prefixes this model uses besides its default ``odm`` namespace.
AUXILIARY_NAMESPACES = {**ODM.AUXILIARY_NAMESPACES, "def": "http://www.cdisc.org/ns/def/v2.1"}


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


register_namespaces()


class TranslatedText(ODM.TranslatedText):
    """Define-XML 2.1 TranslatedText element (identical to ODM 1.3.2).

    Inherits all attributes from the ODM 1.3.2 TranslatedText class.

    Attributes:
        lang (str): BCP 47 language tag (e.g., "en").
        _content (str, required): The translated text content.
    """

    lang = ODM.TranslatedText.lang
    _content = ODM.TranslatedText._content


class Alias(ODM.Alias):
    """Define-XML 2.1 Alias element (identical to ODM 1.3.2).

    Provides an alternate name or identifier for an element in a
    specific context, such as a terminology system.

    Attributes:
        Context (str, required): The context or system providing the alias
            (e.g., "nci:ExtCodeID").
        Name (str, required): The alias name or code within that context.
    """

    Context = ODM.Alias.Context
    Name = ODM.Alias.Name


class StudyDescription(ODM.StudyDescription):
    """Define-XML 2.1 StudyDescription element (identical to ODM 1.3.2).

    Contains a human-readable description of the study.

    Attributes:
        _content (str, required): The study description text.
    """

    _content = ODM.StudyDescription._content


class ProtocolName(ODM.ProtocolName):
    """Define-XML 2.1 ProtocolName element (identical to ODM 1.3.2).

    Contains the protocol identifier for the study.

    Attributes:
        _content (str, required): The protocol name or number.
    """

    _content = ODM.ProtocolName._content


class StudyName(ODM.StudyName):
    """Define-XML 2.1 StudyName element (identical to ODM 1.3.2).

    Contains the short name used to identify the study.

    Attributes:
        _content (str, required): The study name.
    """

    _content = ODM.StudyName._content


class GlobalVariables(ODM.GlobalVariables):
    """Define-XML 2.1 GlobalVariables element (identical to ODM 1.3.2).

    Groups study-level identification metadata: name, description,
    and protocol name.

    Attributes:
        StudyName: Child element containing the study name.
        StudyDescription: Child element containing the study description.
        ProtocolName: Child element containing the protocol name.
    """

    StudyName = ODM.GlobalVariables.StudyName
    StudyDescription = ODM.GlobalVariables.StudyDescription
    ProtocolName = ODM.GlobalVariables.ProtocolName


class Description(ODM.Description):
    """Define-XML 2.1 Description element (identical to ODM 1.3.2).

    Provides a human-readable description for a metadata element,
    containing one or more translated text strings.

    Attributes:
        TranslatedText (list, required): One or more TranslatedText
            child elements, each optionally tagged with a language code.
    """

    TranslatedText = ODM.Description.TranslatedText


class WhereClauseRef(OE.ODMElement):
    """References a WhereClauseDef from within an ItemRef.

    Used inside a Define-XML 2.1 ItemRef to indicate which
    WhereClauseDef applies to this value-list item row.

    Attributes:
        WhereClauseOID (str, required): OID reference to a
            WhereClauseDef element.
    """

    namespace = "def"
    WhereClauseOID = T.OIDRef(required=True)


class ItemRef(ODM.ItemRef):
    """Define-XML 2.1 extension of ODM 1.3.2 ItemRef.

    Extends the base ODM ItemRef with Define-XML specific attributes
    to support value-list filtering and non-standard item flagging.

    Additional Attributes (beyond ODM 1.3.2 ItemRef):
        IsNonStandard (str): "Yes" if this item is not part of the
            referenced CDISC standard (def: namespace).
        HasNoData (str): "Yes" if this item has no data in the
            submission dataset (def: namespace).
        WhereClauseRef (list, required): One or more WhereClauseRef
            child elements that restrict which rows of a ValueListDef
            this ItemRef applies to (def: namespace).
    """

    ItemOID = ODM.ItemRef.ItemOID
    OrderNumber = ODM.ItemRef.OrderNumber
    Mandatory = ODM.ItemRef.Mandatory
    KeySequence = ODM.ItemRef.KeySequence
    MethodOID = ODM.ItemRef.MethodOID
    Role = ODM.ItemRef.Role
    RoleCodeListOID = ODM.ItemRef.RoleCodeListOID
    IsNonStandard = T.ValueSetString(namespace="def")
    HasNoData = T.ValueSetString(namespace="def")
    WhereClauseRef = T.ODMListObject(required=True, element_class=WhereClauseRef, namespace="def")


class title(OE.ODMElement):
    """Human-readable title for a leaf (external document reference).

    Child element of a leaf element providing a display name for the
    referenced external document.

    Attributes:
        _content (str, required): The title text.
    """

    namespace = "def"
    _content = T.String(required=True)


class leaf(OE.ODMElement):
    """References an external document file.

    Provides a URL or relative path reference to an external file such
    as a CRF PDF or supplemental documentation. Used in MetaDataVersion
    and referenced by ArchiveLocationID on ItemGroupDef.

    Attributes:
        ID (str, required): Unique identifier for this leaf element.
        href (str, required): URL or relative path to the document
            (xlink:href attribute).
        title (required): Human-readable title child element for the
            document.
    """

    namespace = "def"
    ID = T.ID(required=True)
    href = T.String(required=True, namespace="xlink")
    title = T.ODMObject(required=True, element_class=title, namespace="def")


class SubClass(OE.ODMElement):
    """Defines a subclass within a dataset class hierarchy.

    Child element of Class, used to specify a sub-level classification
    for an ItemGroupDef (e.g., SDTM class "Events" > "Adverse Events").

    Attributes:
        Name (str, required): The subclass name.
        ParentClass (str): Optional name of the parent class if this
            subclass is nested more than one level deep.
    """

    namespace = "def"
    Name = T.Name(required=True)
    ParentClass = T.String()


class Class(OE.ODMElement):
    """Defines the dataset class for an ItemGroupDef.

    Specifies the CDISC dataset classification (e.g., "FINDINGS",
    "EVENTS", "INTERVENTIONS") for a Define-XML 2.1 ItemGroupDef,
    and may include one or more SubClass child elements.

    Attributes:
        Name (str, required): The class name (e.g., "FINDINGS").
        SubClass (list): Optional SubClass child elements providing
            finer-grained classification.
    """

    namespace = "def"
    Name = T.Name(required=True)
    SubClass = T.ODMListObject(element_class=SubClass, namespace="def")


class ItemGroupDef(ODM.ItemGroupDef):
    """Define-XML 2.1 extension of ODM 1.3.2 ItemGroupDef.

    Extends the base ODM ItemGroupDef with Define-XML specific attributes
    for regulatory submission dataset metadata, including dataset structure,
    archive location, standard references, and class hierarchy.

    Additional Attributes (beyond ODM 1.3.2 ItemGroupDef):
        Structure (str, required): Dataset structure description
            (e.g., "One Record Per Subject Per Visit") (def: namespace).
        ArchiveLocationID (str): Reference to a leaf element ID for the
            dataset file location (def: namespace).
        CommentOID (str): OID reference to a CommentDef annotation
            (def: namespace).
        IsNonStandard (str): "Yes" if this is a non-standard dataset
            not part of the referenced CDISC standard (def: namespace).
        StandardOID (str): OID reference to a Standard element in the
            Standards section (def: namespace).
        HasNoData (str): "Yes" if this dataset has no data in the
            submission (def: namespace).
        Class: Child Class element specifying the dataset class
            (e.g., "FINDINGS"), with optional SubClass children
            (def: namespace).
        leaf (required): Child leaf element referencing the dataset
            file (def: namespace).
    """

    OID = ODM.ItemGroupDef.OID
    Name = ODM.ItemGroupDef.Name
    Repeating = ODM.ItemGroupDef.Repeating
    IsReferenceData = ODM.ItemGroupDef.IsReferenceData
    SASDatasetName = ODM.ItemGroupDef.SASDatasetName
    Domain = ODM.ItemGroupDef.Domain
    Purpose = ODM.ItemGroupDef.Purpose
    Structure = T.String(required=True, namespace="def")
    ArchiveLocationID = T.String(namespace="def")
    CommentOID = T.OIDRef(namespace="def")
    IsNonStandard = T.ValueSetString(namespace="def")
    StandardOID = T.OIDRef(namespace="def")
    HasNoData = T.ValueSetString(namespace="def")
    Description = ODM.ItemGroupDef.Description
    ItemRef = ODM.ItemGroupDef.ItemRef
    Alias = ODM.ItemGroupDef.Alias
    Class = T.ODMObject(element_class=Class, namespace="def")
    leaf = T.ODMObject(required=True, element_class=leaf, namespace="def")

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CheckValue(ODM.CheckValue):
    """Define-XML 2.1 CheckValue element.

    Contains a single value used in a RangeCheck comparison within a
    WhereClauseDef. Overrides the ODM 1.3.2 base to make content
    optional (not required) since empty check values are permitted.

    Attributes:
        _content (str): The check value string (not required in
            Define-XML 2.1).
    """

    _content = T.String(required=False)


class FormalExpression(ODM.FormalExpression):
    """Define-XML 2.1 FormalExpression element (identical to ODM 1.3.2).

    Represents a formal expression (e.g., a programming language
    expression) used in a MethodDef to describe a derivation algorithm.

    Attributes:
        Context (str, required): The language or context of the
            expression (e.g., "SAS" or "R").
        _content (str, required): The expression text.
    """

    Context = ODM.FormalExpression.Context
    _content = ODM.FormalExpression._content


class RangeCheck(ODM.RangeCheck):
    """Define-XML 2.1 extension of ODM 1.3.2 RangeCheck.

    Used within a WhereClauseDef to define a logical condition on an
    item's value. The ItemOID attribute is moved to the def: namespace.

    Additional Attributes (beyond ODM 1.3.2 RangeCheck):
        ItemOID (str, required): OID reference to the ItemDef that is
            being checked; uses the def: namespace (replaces the base
            ODM RangeCheck's CheckValue child with a targeted item OID).
        CheckValue (list): One or more CheckValue elements containing
            the comparison values.
    """

    Comparator = ODM.RangeCheck.Comparator
    SoftHard = ODM.RangeCheck.SoftHard
    ItemOID = T.OIDRef(required=True, namespace="def")
    CheckValue = T.ODMListObject(element_class=CheckValue)


class CodeListRef(ODM.CodeListRef):
    """Define-XML 2.1 CodeListRef element (identical to ODM 1.3.2).

    References a CodeList element from within an ItemDef, indicating
    the controlled terminology for that item.

    Attributes:
        CodeListOID (str, required): OID reference to the CodeList.
    """

    CodeListOID = ODM.CodeListRef.CodeListOID


class ValueListRef(OE.ODMElement):
    """References a ValueListDef from an ItemDef.

    Used in a Define-XML 2.1 ItemDef to indicate that the item has
    variable-level metadata defined by a separate ValueListDef.

    Attributes:
        ValueListOID (str, required): OID reference to the ValueListDef
            element.
    """

    namespace = "def"
    ValueListOID = T.OIDRef(required=True)


class PDFPageRef(OE.ODMElement):
    """References specific pages within a PDF document.

    Child element of DocumentRef, identifying which pages within a
    referenced PDF are relevant (e.g., the CRF pages for a specific
    item).

    Attributes:
        Type (str, required): The page reference type ("PhysicalRef" or
            "NamedDestination").
        PageRefs (str): Space-separated list of physical page numbers or
            named destination labels.
        FirstPage (int): First page number in a page range.
        LastPage (int): Last page number in a page range.
        Title (str): Optional title for this page reference.
    """

    namespace = "def"
    Type = T.ValueSetString(required=True)
    PageRefs = T.String()
    FirstPage = T.PositiveInteger()
    LastPage = T.PositiveInteger()
    Title = T.String()


class DocumentRef(OE.ODMElement):
    """References an external document (leaf) with optional page references.

    Used in Origin, MethodDef, CommentDef, and WhereClauseDef to link
    a metadata element to a specific external document (e.g., a CRF
    PDF), optionally with specific page references.

    Attributes:
        leafID (str, required): Identifier matching the ID of a leaf
            element.
        PDFPageRef (list): Zero or more PDFPageRef child elements
            specifying relevant pages within the referenced PDF.
    """

    namespace = "def"
    leafID = T.String(required=True)
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef, namespace="def")


class Origin(OE.ODMElement):
    """Describes the origin or source of data for an ItemDef.

    Specifies how the data value for an item was obtained (e.g.,
    collected from a CRF, derived by a computation, or assigned from
    a protocol).

    Attributes:
        Type (str, required): The origin type. One of "Collected",
            "Derived", "Assigned", "Protocol", "Predecessor", or
            "Not Available".
        Source (str): The data source. One of "Subject",
            "Investigator", "Vendor", or "Sponsor".
        Description: Optional Description child element providing
            additional context about the origin.
        DocumentRef (list): Zero or more DocumentRef elements
            linking to CRF pages or other source documents.
    """

    namespace = "def"
    Type = T.ExtendedValidValues(required=True, valid_values=["Collected", "Derived", "Assigned", "Protocol",
                                                              "Predecessor", "Not Available"])
    Source = T.ExtendedValidValues(valid_values=["Subject", "Investigator", "Vendor", "Sponsor"])
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class ItemDef(ODM.ItemDef):
    """Define-XML 2.1 extension of ODM 1.3.2 ItemDef.

    Extends the base ODM ItemDef with Define-XML specific attributes
    for regulatory submission variable metadata, including display
    format, comments, origin, and value-list references.

    Additional Attributes (beyond ODM 1.3.2 ItemDef):
        DisplayFormat (str): SAS display format string for the item
            (def: namespace).
        CommentOID (str): OID reference to a CommentDef annotation for
            this item (def: namespace).
        Origin (list): One or more Origin child elements describing
            how the data was obtained (def: namespace).
        ValueListRef: A single ValueListRef child element referencing a
            ValueListDef for variable-level metadata (def: namespace).
        Alias (list): Zero or more Alias elements providing alternate
            names in external terminologies.
    """

    OID = ODM.ItemDef.OID
    Name = ODM.ItemDef.Name
    DataType = ODM.ItemDef.DataType
    Length = ODM.ItemDef.Length
    SignificantDigits = ODM.ItemDef.SignificantDigits
    SASFieldName = ODM.ItemDef.SASFieldName
    DisplayFormat = T.String(namespace="def")
    CommentOID = T.OIDRef(namespace="def")
    Description = ODM.ItemDef.Description
    CodeListRef = ODM.ItemDef.CodeListRef
    Origin = T.ODMListObject(element_class=Origin, namespace="def")
    ValueListRef = T.ODMObject(element_class=ValueListRef, namespace="def")
    Alias = T.ODMListObject(element_class=Alias)


class Decode(ODM.Decode):
    """Define-XML 2.1 Decode element (identical to ODM 1.3.2).

    Contains the human-readable decoded text for a CodeListItem,
    with support for multiple languages via TranslatedText children.

    Attributes:
        TranslatedText (list, required): One or more TranslatedText
            child elements providing the decoded label.
    """

    TranslatedText = ODM.Decode.TranslatedText


class CodeListItem(ODM.CodeListItem):
    """Define-XML 2.1 extension of ODM 1.3.2 CodeListItem.

    Extends the base ODM CodeListItem with Define-XML specific attributes
    for indicating extended/non-standard coded values and item-level
    descriptions.

    Additional Attributes (beyond ODM 1.3.2 CodeListItem):
        ExtendedValue (str): "Yes" if the coded value is an extended
            (non-standard) value not in the referenced CDISC terminology
            (def: namespace).
        Description: Optional Description child element providing
            additional context for this code list item (from
            ODM.CodeList.Description).
    """

    CodedValue = ODM.CodeListItem.CodedValue
    Rank = ODM.CodeListItem.Rank
    OrderNumber = ODM.CodeListItem.OrderNumber
    ExtendedValue = T.ValueSetString(namespace="def")
    Description = ODM.CodeList.Description
    Decode = ODM.CodeListItem.Decode
    Alias = ODM.CodeListItem.Alias


class EnumeratedItem(ODM.EnumeratedItem):
    """Define-XML 2.1 extension of ODM 1.3.2 EnumeratedItem.

    Extends the base ODM EnumeratedItem (a code list item without a
    separate Decode child) with Define-XML specific attributes for
    non-standard coded values and item-level descriptions.

    Additional Attributes (beyond ODM 1.3.2 EnumeratedItem):
        ExtendedValue (str): "Yes" if the coded value is an extended
            (non-standard) value not in the referenced CDISC terminology
            (def: namespace).
        Description: Optional Description child element providing
            additional context for this enumerated item (from
            ODM.CodeList.Description).
    """

    CodedValue = ODM.EnumeratedItem.CodedValue
    Rank = ODM.EnumeratedItem.Rank
    OrderNumber = ODM.EnumeratedItem.OrderNumber
    ExtendedValue = T.ValueSetString(namespace="def")
    Description = ODM.CodeList.Description
    Alias = ODM.EnumeratedItem.Alias


class ExternalCodeList(ODM.ExternalCodeList):
    """Define-XML 2.1 ExternalCodeList element (identical to ODM 1.3.2).

    References an externally maintained code list (e.g., MedDRA, SNOMED)
    rather than enumerating individual items inline.

    Attributes:
        Dictionary (str): Name of the external dictionary or terminology
            (e.g., "MedDRA").
        Version (str): Version of the external dictionary.
        ref (str): Reference identifier within the external dictionary.
        href (str): URL pointing to the external dictionary resource.
    """

    Dictionary = ODM.ExternalCodeList.Dictionary
    Version = ODM.ExternalCodeList.Version
    ref = ODM.ExternalCodeList.ref
    href = ODM.ExternalCodeList.href


class CodeList(ODM.CodeList):
    """Define-XML 2.1 extension of ODM 1.3.2 CodeList.

    Extends the base ODM CodeList with Define-XML specific attributes
    for indicating non-standard code lists and standard references.

    Additional Attributes (beyond ODM 1.3.2 CodeList):
        IsNonStandard (str): "Yes" if this code list is not part of
            the referenced CDISC standard (def: namespace).
        StandardOID (str): Reference to the Standard element for the
            CDISC terminology that this code list belongs to
            (def: namespace).
        CommentOID (str): OID reference to a CommentDef annotation
            for this code list (def: namespace).
    """

    OID = ODM.CodeList.OID
    Name = ODM.CodeList.Name
    DataType = ODM.CodeList.DataType
    IsNonStandard = T.ValueSetString(namespace="def")
    StandardOID = T.String(namespace="def")
    SASFormatName = ODM.CodeList.SASFormatName
    CommentOID = T.OIDRef(namespace="def")
    Description = ODM.CodeList.Description
    CodeListItem = ODM.CodeList.CodeListItem
    EnumeratedItem = ODM.CodeList.EnumeratedItem
    ExternalCodeList = ODM.CodeList.ExternalCodeList
    Alias = ODM.CodeList.Alias


class MethodDef(ODM.MethodDef):
    """Define-XML 2.1 extension of ODM 1.3.2 MethodDef.

    Extends the base ODM MethodDef with the ability to reference
    external documents that describe the derivation algorithm.

    Additional Attributes (beyond ODM 1.3.2 MethodDef):
        DocumentRef (list): Zero or more DocumentRef elements linking
            to external documents (e.g., SAP sections) that describe
            this method (def: namespace).
    """

    OID = ODM.MethodDef.OID
    Name = ODM.MethodDef.Name
    Type = ODM.MethodDef.Type
    Description = ODM.MethodDef.Description
    FormalExpression = ODM.MethodDef.FormalExpression
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class AnnotatedCRF(OE.ODMElement):
    """References the annotated Case Report Form (CRF) document.

    A MetaDataVersion-level element pointing to the annotated CRF
    PDF that shows variable annotations on the original CRF pages.

    Attributes:
        DocumentRef (required): A single DocumentRef child element
            pointing to the annotated CRF leaf document.
    """

    namespace = "def"
    DocumentRef = T.ODMObject(required=True, element_class=DocumentRef, namespace="def")


class SupplementalDoc(OE.ODMElement):
    """References supplemental documentation documents.

    A MetaDataVersion-level element that lists references to
    supplemental documents (e.g., SAP, programming specifications)
    associated with the submission.

    Attributes:
        DocumentRef (list, required): One or more DocumentRef child
            elements, each pointing to a supplemental document leaf.
    """

    namespace = "def"
    DocumentRef = T.ODMListObject(required=True, element_class=DocumentRef, namespace="def")


class WhereClauseDef(OE.ODMElement):
    """Defines a logical condition (where clause) for a ValueListDef.

    Specifies one or more range check conditions that filter which
    rows of a ValueListDef apply, based on the value of a referenced
    item. Used to implement variable-level metadata (e.g., different
    metadata for AESTDTC depending on the value of AETERM).

    Attributes:
        OID (str, required): Unique identifier for this WhereClauseDef.
        CommentOID (str): Optional OID reference to a CommentDef
            annotation (def: namespace).
        RangeCheck (list, required): One or more RangeCheck child
            elements that together define the logical condition.
    """

    namespace = "def"
    OID = T.OID(required=True)
    CommentOID = T.OIDRef(namespace="def")
    RangeCheck = T.ODMListObject(required=True, element_class=RangeCheck)


class ValueListDef(OE.ODMElement):
    """Defines variable-level (value-level) metadata for an ItemDef.

    Contains a list of ItemRef elements, each paired with a
    WhereClauseRef, to provide different metadata (e.g., different
    labels, code lists, or methods) depending on the value of a
    controlling variable.

    Attributes:
        OID (str, required): Unique identifier for this ValueListDef.
        Description: Optional Description child element.
        ItemRef (list, required): One or more ItemRef child elements
            each referencing an ItemDef and containing a
            WhereClauseRef that specifies when that metadata applies.
    """

    namespace = "def"
    OID = T.OID(required=True)
    Description = T.ODMObject(element_class=Description)
    ItemRef = T.ODMListObject(element_class=ItemRef, required=True)

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CommentDef(OE.ODMElement):
    """Provides an annotation comment for a metadata element.

    Referenced by OID from ItemDef, ItemGroupDef, CodeList, and other
    elements via their CommentOID attribute, allowing shared
    annotations to be defined once and reused.

    Attributes:
        OID (str, required): Unique identifier for this CommentDef.
        Description: A Description child element containing the comment
            text as one or more TranslatedText elements.
        DocumentRef (list): Zero or more DocumentRef elements linking
            to supporting external documents.
    """

    namespace = "def"
    OID = T.OID(required=True)
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class Standard(OE.ODMElement):
    """Defines a CDISC standard referenced in the submission.

    Represents a specific version of a CDISC standard (e.g., SDTM 1.7,
    ADaM 1.1, CDASH 2.0) that is referenced by ItemGroupDef and
    CodeList elements via their StandardOID attribute.

    Attributes:
        OID (str, required): Unique identifier for this Standard.
        Name (str, required): The standard name (e.g., "SDTM-IG",
            "ADaMIG", "CDASHIG").
        Type (str, required): The standard type (e.g., "IG" for
            Implementation Guide, "CT" for Controlled Terminology).
        PublishingSet (str): Optional publishing set identifier
            (e.g., "SDTM", "ADaM").
        Version (str, required): The version of the standard
            (e.g., "3.3", "1.1").
        Status (str): The publication status (e.g., "Final",
            "Provisional").
        CommentOID (str): Optional OID reference to a CommentDef
            annotation (def: namespace).
    """

    namespace = "def"
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.String(required=True)
    PublishingSet = T.String()
    Version = T.String(required=True)
    Status = T.String()
    CommentOID = T.OIDRef(namespace="def")


class Standards(OE.ODMElement):
    """Container for all Standard elements in a MetaDataVersion.

    Groups all CDISC standard references (SDTM, ADaM, CDASH, CT)
    used in the submission. Only present in Define-XML 2.1 (not 2.0).

    Attributes:
        Standard (list, required): One or more Standard child elements
            each describing a referenced CDISC standard.
    """

    namespace = "def"
    Standard = T.ODMListObject(element_class=Standard, required=True, namespace="def")

    def __len__(self):
        return len(self.Standard)

    def __getitem__(self, position):
        return self.Standard[position]

    def __iter__(self):
        return iter(self.Standard)


class MetaDataVersion(ODM.MetaDataVersion):
    """Define-XML 2.1 extension of ODM 1.3.2 MetaDataVersion.

    The primary container for all Define-XML 2.1 metadata, extending
    the base ODM MetaDataVersion with Define-XML specific elements
    for regulatory submission dataset specifications.

    Additional Attributes (beyond ODM 1.3.2 MetaDataVersion):
        DefineVersion (str, required): The Define-XML specification
            version (must be "2.1.n") (def: namespace).
        CommentOID (str): OID reference to a CommentDef annotation
            for this MetaDataVersion (def: namespace).
        Standards: A Standards child element listing all referenced
            CDISC standards (def: namespace; Define-XML 2.1 only).
        AnnotatedCRF: Reference to the annotated CRF document
            (def: namespace).
        SupplementalDoc: References to supplemental documents
            (def: namespace).
        ValueListDef (list): Zero or more ValueListDef elements for
            variable-level metadata (def: namespace).
        WhereClauseDef (list): Zero or more WhereClauseDef elements
            defining filter conditions (def: namespace).
        CommentDef (list): Zero or more CommentDef annotation elements
            (def: namespace).
        leaf (list): Zero or more leaf elements referencing external
            documents (def: namespace).
    """

    OID = ODM.MetaDataVersion.OID
    Name = ODM.MetaDataVersion.Name
    Description = ODM.MetaDataVersion.Description
    DefineVersion = T.ValueSetString(required=True, namespace="def")
    CommentOID = T.OIDRef(namespace="def")
    Standards = T.ODMObject(element_class=Standards, namespace="def")
    AnnotatedCRF = T.ODMObject(element_class=AnnotatedCRF, namespace="def")
    SupplementalDoc = T.ODMObject(element_class=SupplementalDoc, namespace="def")
    ValueListDef = T.ODMListObject(element_class=ValueListDef, namespace="def")
    WhereClauseDef = T.ODMListObject(element_class=WhereClauseDef, namespace="def")
    ItemGroupDef = ODM.MetaDataVersion.ItemGroupDef
    ItemDef = ODM.MetaDataVersion.ItemDef
    CodeList = ODM.MetaDataVersion.CodeList
    MethodDef = ODM.MetaDataVersion.MethodDef
    CommentDef = T.ODMListObject(element_class=CommentDef, namespace="def")
    leaf = T.ODMListObject(element_class=leaf, namespace="def")


class Study(ODM.Study):
    """Define-XML 2.1 Study element.

    Extends the ODM 1.3.2 Study element to use the Define-XML 2.1
    MetaDataVersion class. In Define-XML, Study contains exactly one
    MetaDataVersion (not a list as in ODM clinical data).

    Attributes:
        OID (str): Study OID, inherited from ODM 1.3.2 Study.
        GlobalVariables: Child element containing study identification
            metadata (inherited from ODM 1.3.2 Study).
        MetaDataVersion (required): A single MetaDataVersion child
            element (not a list) containing all Define-XML metadata.
    """

    OID = ODM.Study.OID
    GlobalVariables = ODM.Study.GlobalVariables
    MetaDataVersion = T.ODMObject(required=True, element_class=MetaDataVersion)


class ODM(ODM.ODM):
    """Define-XML 2.1 root ODM element.

    The root element for a Define-XML 2.1 document. Extends the base
    ODM 1.3.2 ODM element with Define-XML specific constraints and
    the required Context attribute that identifies the submission
    context (e.g., "Submission").

    Additional Attributes (beyond ODM 1.3.2 ODM):
        FileType (str, required): Restricted to "Snapshot" for
            Define-XML documents.
        ODMVersion (str, required): Restricted to "1.3.2" for
            Define-XML documents.
        Context (str, required): The Define-XML submission context
            (e.g., "Submission") (def: namespace).
        Study (required): A single Study child element containing
            the Define-XML metadata (not a list as in ODM).
    """

    FileType = T.ExtendedValidValues(required=True, valid_values=["Snapshot"])
    FileOID = ODM.ODM.FileOID
    CreationDateTime = ODM.ODM.CreationDateTime
    AsOfDateTime = ODM.ODM.AsOfDateTime
    ODMVersion = T.ExtendedValidValues(required=True, valid_values=["1.3.2"])
    Originator = ODM.ODM.Originator
    SourceSystem = ODM.ODM.SourceSystem
    SourceSystemVersion = ODM.ODM.SourceSystemVersion
    schemaLocation = ODM.ODM.schemaLocation
    Context = T.ValueSetString(required=True, namespace="def")
    ID = ODM.ODM.ID
    Study = T.ODMObject(required=True, element_class=Study)
