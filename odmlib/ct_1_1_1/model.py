import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


#: Namespace prefixes this model uses besides its default ``odm`` namespace.
AUXILIARY_NAMESPACES = {
    "nciodm": "http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC",
    "xs": "http://www.w3.org/2001/XMLSchema-instance",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xlink": "http://www.w3.org/1999/xlink",
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


class TranslatedText(OE.ODMElement):
    """A piece of text in a specific language, used inside Description elements.

    Attributes:
        lang (str): BCP 47 language tag (xml:lang attribute), e.g. "en".
        _content (str, required): The actual text content.
    """

    lang = T.Language(namespace="xml")
    _content = T.String(required=True)


class Alias(OE.ODMElement):
    """An alternative name or identifier for a CT-XML element in an external context.

    Attributes:
        Context (str, required): The context in which the alias applies,
            e.g. the name of an external system or coding standard.
        Name (str, required): The alias value in that context.
    """

    Context = T.String(required=True)
    Name = T.String(required=True)


class StudyDescription(OE.ODMElement):
    """A plain-text description of the study in a CT-XML GlobalVariables element.

    Attributes:
        _content (str, required): The study description text.
    """

    _content = T.String(required=True)


class ProtocolName(OE.ODMElement):
    """The name of the protocol associated with a CT-XML study.

    Attributes:
        _content (str, required): The protocol name string.
    """

    _content = T.String(required=True)


class StudyName(OE.ODMElement):
    """The short name of the study in a CT-XML GlobalVariables element.

    Attributes:
        _content (str, required): The study name string.
    """

    _content = T.String(required=True)


class GlobalVariables(OE.ODMElement):
    """Study-level identification variables for a CT-XML document.

    Holds the study name, description, and protocol name that identify
    the controlled terminology package.

    Attributes:
        StudyName: Short name of the study/package.
        StudyDescription: Description of the study/package.
        ProtocolName: Name of the associated protocol.
    """

    StudyName = T.ODMObject(element_class=StudyName)
    StudyDescription = T.ODMObject(element_class=StudyDescription)
    ProtocolName = T.ODMObject(element_class=ProtocolName)


class Description(OE.ODMElement):
    """A human-readable description composed of one or more language-tagged text blocks.

    Attributes:
        TranslatedText (list, required): One or more TranslatedText children
            providing the description in different languages.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CDISCSynonym(OE.ODMElement):
    """A CDISC synonym for a controlled terminology term.

    Multiple CDISCSynonym elements may appear within a single EnumeratedItem
    or CodeList to list all recognized synonyms.

    Attributes:
        _content (str, required): The synonym text string.
    """

    namespace = "nciodm"
    _content = T.String(required=True)


class CDISCDefinition(OE.ODMElement):
    """The CDISC-authored definition of a controlled terminology term.

    Attributes:
        _content (str, required): The full definition text for the term as
            published by CDISC.
    """

    namespace = "nciodm"
    _content = T.String(required=True)


class CDISCSubmissionValue(OE.ODMElement):
    """The CDISC submission value (the value to use in regulatory submissions) for a CodeList.

    Appears as a child of CodeList to provide the canonical submission
    value for the entire controlled terminology concept.

    Attributes:
        _content (str, required): The submission value string.
    """

    namespace = "nciodm"
    _content = T.String(required=True)


class PreferredTerm(OE.ODMElement):
    """The NCI preferred term for a controlled terminology concept.

    The preferred term is the primary human-readable label used by NCI/EVS
    for this concept.

    Attributes:
        _content (str, required): The NCI preferred term string.
    """

    namespace = "nciodm"
    _content = T.String(required=True)


class EnumeratedItem(OE.ODMElement):
    """A single coded term (enumerated value) in a CT-XML CodeList.

    Represents one controlled terminology concept with its NCI code,
    CDISC synonyms, definition, and NCI preferred term. Uses the
    ``nciodm:`` namespace for NCI-specific attributes and child elements.

    Attributes:
        CodedValue (str, required): The submission value for this term
            (the value written into datasets).
        ExtCodeID (str, required): NCI concept code for this term
            (nciodm:ExtCodeID attribute).
        CDISCSynonym (list): Zero or more CDISC synonyms
            (nciodm:CDISCSynonym elements).
        CDISCDefinition (required): CDISC definition of this term
            (nciodm:CDISCDefinition element).
        PreferredTerm (required): NCI preferred term
            (nciodm:PreferredTerm element).
    """

    CodedValue = T.String(required=True)
    ExtCodeID = T.String(required=True, namespace="nciodm")
    CDISCSynonym = T.ODMListObject(element_class=CDISCSynonym, namespace="nciodm")
    CDISCDefinition = T.ODMObject(required=True, element_class=CDISCDefinition, namespace="nciodm")
    PreferredTerm = T.ODMObject(required=True, element_class=PreferredTerm, namespace="nciodm")


class CodeList(OE.ODMElement):
    """A CDISC controlled terminology code list in a CT-XML 1.1.1 document.

    Represents a single controlled terminology concept (e.g. the RACE
    code list) with all its coded values. NCI-specific metadata
    (ExtCodeID, CodeListExtensible, CDISCSubmissionValue, CDISCSynonym,
    PreferredTerm) uses the ``nciodm:`` namespace.

    Attributes:
        OID (str, required): Unique identifier for this code list.
        Name (str, required): Human-readable name of the code list.
        DataType (str, required): Data type of the coded values
            (e.g. "text").
        ExtCodeID (str, required): NCI concept code for the code list
            itself (nciodm:ExtCodeID attribute).
        CodeListExtensible (str, required): Whether sponsors may add
            additional terms ("Yes" or "No")
            (nciodm:CodeListExtensible attribute).
        Description: Optional human-readable description.
        EnumeratedItem (list): The coded terms that belong to this code list.
        CDISCSubmissionValue (required): The canonical submission value for
            the overall code list concept (nciodm:CDISCSubmissionValue).
        CDISCSynonym (required): A CDISC synonym for the code list concept
            (nciodm:CDISCSynonym).
        PreferredTerm (required): NCI preferred term for the code list
            concept (nciodm:PreferredTerm).
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    ExtCodeID = T.String(required=True, namespace="nciodm")
    CodeListExtensible = T.ValueSetString(required=True, namespace="nciodm")
    Description = T.ODMObject(element_class=Description)
    EnumeratedItem = T.ODMListObject(element_class=EnumeratedItem)
    CDISCSubmissionValue = T.ODMObject(required=True, element_class=CDISCSubmissionValue, namespace="nciodm")
    CDISCSynonym = T.ODMObject(required=True, element_class=CDISCSynonym, namespace="nciodm")
    PreferredTerm = T.ODMObject(required=True, element_class=PreferredTerm, namespace="nciodm")


class MetaDataVersion(OE.ODMElement):
    """A versioned container for all controlled terminology code lists in a CT-XML document.

    Attributes:
        OID (str, required): Unique identifier for this metadata version.
        Name (str, required): Human-readable name.
        Description (str): Optional plain-text description of this version.
        CodeList (list): Zero or more CodeList elements defining the
            controlled terminology for this version.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.String(required=False)
    CodeList = T.ODMListObject(element_class=CodeList)


class Study(OE.ODMElement):
    """The study element in a CT-XML 1.1.1 document.

    Identifies the controlled terminology package and contains the
    GlobalVariables and one or more MetaDataVersion elements with the
    code lists.

    Attributes:
        OID (str, required): Unique identifier for the study/package.
        GlobalVariables (required): Study identification variables (name,
            description, protocol name).
        MetaDataVersion (list): Zero or more versioned containers of
            controlled terminology code lists.
    """

    OID = T.String(required=True)
    GlobalVariables = T.ODMObject(required=True, element_class=GlobalVariables)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class ODM(OE.ODMElement):
    """The root element of a CT-XML 1.1.1 controlled terminology document.

    A CT-XML file distributes CDISC/NCI controlled terminology packages.
    It uses the base ODM namespace (``http://www.cdisc.org/ns/odm/v1.3``)
    and the NCI extension namespace
    (``http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC``, prefix ``nciodm:``).

    Attributes:
        Description (str): Human-readable description of the file.
        FileType (str, required): "Snapshot" or "Transactional".
        Granularity (str): Level of data included.
        FileOID (str, required): Globally unique OID for this file.
        CreationDateTime (str, required): ISO 8601 datetime of file creation.
        AsOfDateTime (str): ISO 8601 datetime indicating currency of the
            terminology.
        ODMVersion (str): Version of the ODM standard.
        Originator (str): Organization that produced the file.
        SourceSystem (str): Software system that generated the file.
        SourceSystemVersion (str): Version of the source system.
        schemaLocation (str): xs:schemaLocation for schema validation.
        Study (list): One or more Study elements containing code lists.
    """

    Description = T.String(required=False)
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    schemaLocation = T.String(required=False, namespace="xs")
    Study = T.ODMListObject(element_class=Study)
