import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    """A piece of text in a specific language, used inside Description and similar elements.

    .. note::

       **Known approximation.** The XSD types TranslatedText as
       ``mixed="true"`` with an optional ``xhtml:div`` child, so a document
       may mark the text up as XHTML. odmlib models the text-only form: an
       ``xhtml:div`` present in a source document is dropped on load, and
       cannot be written. Plain-text TranslatedText -- overwhelmingly the
       common case -- round-trips exactly.

       Two things stand behind this. Faithful XHTML would need a model class
       for every element ``ODM-xhtml.xsd`` allows (``p``, ``b``, ``table``
       and the rest, deeply recursive and themselves mixed), because the
       loader resolves children by tag name against this module. And odmlib
       never reads ElementTree's ``tail``, so text *following* a child
       element is lost silently even where the child is modelled. An opaque
       text-only ``div`` was tried in v0.2.1 and withdrawn: it could not
       carry markup either -- text assigned to it is XML-escaped on write --
       so it added a foreign-namespace dependency for no gain. Validate with
       :class:`~odmlib.odm_parser.ODMSchemaValidator` if a source document
       may contain markup.

    Attributes:
        lang (str): BCP 47 language tag (xml:lang attribute), e.g. "en".
        Type (str, required): Media-type qualifier for the text (XSD type
            ``text``, free-text, ``use="required"``), e.g. ``"text/plain"``.
            Required by the ODM 2.0 schema.
        _content (str, required): The actual text content.
    """

    lang = T.String(namespace="xml")
    Type = T.String(required=True)
    _content = T.String(required=True)


class Description(OE.ODMElement):
    """A human-readable description composed of one or more language-tagged text blocks.

    Attributes:
        TranslatedText (list, required): One or more TranslatedText children
            providing the description in different languages.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Title(OE.ODMElement):
    _content = T.String(required=False)


class Leaf(OE.ODMElement):
    """A document location referenced by DocumentRef/@LeafID.

    Attributes:
        ID (str, required): Identifier targeted by DocumentRef/@LeafID.
        href (str, required): URL of the document (``xlink:href``).
        Title (required): Human-readable document title.
    """

    ID = T.ID(required=True)
    href = T.String(required=True, namespace="xlink")
    Title = T.ODMObject(required=True, element_class=Title)


class PDFPageRef(OE.ODMElement):
    Type = T.ValueSetString(required=True)
    PageRefs = T.String()
    FirstPage = T.PositiveInteger()
    LastPage = T.PositiveInteger()
    Title = T.String()


class DocumentRef(OE.ODMElement):
    """A reference to a Leaf carrying the location of a supporting document.

    .. versionchanged:: 0.2.1
       The attribute was renamed ``leafID`` -> ``LeafID`` to match
       ``DocumentRefAttributeDefinition`` in the ODM 2.0 XSD. The lower-case
       spelling made every odm_2_0 document containing a DocumentRef fail
       schema validation. ODM 2.0's ``SourceItem`` keeps a lower-case
       ``leafID``, and Define-XML's DocumentRef is unaffected.

    Attributes:
        LeafID (str, required): ID of the Leaf holding the document location.
        PDFPageRef (list): Page references within the referenced PDF.
    """

    LeafID = T.IDRef(required=True)
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef)


class AnnotatedCRF(OE.ODMElement):
    """References to the annotated CRF documents for a MetaDataVersion.

    Attributes:
        DocumentRef (list, required): One or more document references.
    """

    DocumentRef = T.ODMListObject(required=True, element_class=DocumentRef)


class SupplementalDoc(OE.ODMElement):
    """References to supplemental documents for a MetaDataVersion.

    Attributes:
        DocumentRef (list, required): One or more document references.
    """

    DocumentRef = T.ODMListObject(required=True, element_class=DocumentRef)


class CommentDef(OE.ODMElement):
    """A reusable comment referenced by the CommentOID attributes in the metadata.

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD: ``Description`` became required
       (``minOccurs="1"``) and ``DocumentRef`` became a list
       (``maxOccurs="unbounded"``); it previously held a single reference.

    Attributes:
        OID (str, required): Unique identifier, targeted by CommentOID.
        Description (required): The comment text.
        DocumentRef (list): References to documents supporting the comment.
    """

    OID = T.OID(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef)


class Coding(OE.ODMElement):
    Code = T.String(required=False)
    System = T.String(required=True)
    SystemName = T.String()
    SystemVersion = T.String()
    Label = T.String()
    href = T.String()
    ref = T.String()
    CommentOID = T.OIDRef(required=False)


class Alias(OE.ODMElement):
    """An alternative name or identifier for an ODM element in an external context.

    Attributes:
        Context (str, required): The context in which the alias applies,
            e.g. the name of an external system or standard.
        Name (str, required): The alias value in that context.
    """

    Context = T.String(required=True)
    Name = T.String(required=True)


# class StudyDescription(OE.ODMElement):
#     Description = T.ODMObject(element_class=Description, required=True)


# class ProtocolName(OE.ODMElement):
#     _content = T.String(required=True)
#
#
# class StudyName(OE.ODMElement):
#     _content = T.String(required=True)


class Include(OE.ODMElement):
    """Includes the metadata from another study's MetaDataVersion into this one.

    Attributes:
        StudyOID (str, required): OID reference to the study whose metadata
            is being included.
        MetaDataVersionOID (str, required): OID reference to the specific
            MetaDataVersion being included.
        href (str): URL of the document holding the included metadata.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    href = T.String()


class Standard(OE.ODMElement):
    """A CDISC standard a MetaDataVersion conforms to.

    .. versionchanged:: 0.2.1
       ``Name``, ``Type``, ``PublishingSet`` and ``Status`` are value-set
       checked. All four have enumerated XSD types but were modelled as plain
       strings, so ``Standard(Type="Nonsense")`` built without complaint.
       ``Status`` is an *extensible* vocabulary in the XSD (a union with
       ``xs:string``), so its listed terms are documentation and other values
       are still accepted.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): The standard, e.g. "SDTMIG", "CDISC/NCI".
        Type (str, required): "IG" for an implementation guide, "CT" for
            controlled terminology.
        PublishingSet (str): The publishing set, e.g. "SDTM", "ADaM".
        Version (str, required): Version of the standard.
        Status (str, required): Development status, e.g. "Final"; extensible.
        CommentOID (str): OID of an associated CommentDef.
    """

    OID = T.OID(required=True)
    Name = T.ValueSetString(required=True)
    Type = T.ValueSetString(required=True)
    PublishingSet = T.ValueSetString(required=False)
    Version = T.String(required=True)
    Status = T.ValueSetString(required=True)
    CommentOID = T.OIDRef(required=False)


class Standards(OE.ODMElement):
    Standard = T.ODMListObject(required=True, element_class=Standard)


class StudyEventRef(OE.ODMElement):
    """A reference to a StudyEventDef within a Protocol or ExceptionEvent.

    Attributes:
        StudyEventOID (str, required): OID of the referenced StudyEventDef.
        OrderNumber (int): Position of this event in the sequence.
        Mandatory (str, required): Whether collection of this event is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this event.
    """

    StudyEventOID = T.OIDRef(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class WorkflowRef(OE.ODMElement):
    WorkflowOID = T.OIDRef(required=True)


class Arm(OE.ODMElement):
    """Defines a study arm (treatment arm) in the trial design.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the arm.
        Description: Optional description.
        WorkflowRef: Reference to the workflow that defines this arm's event
            sequence.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)


class Epoch(OE.ODMElement):
    """Defines a study epoch (a named period of the trial).

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the epoch.
        SequenceNumber (int, required): Ordinal position of this epoch in the
            overall trial timeline.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SequenceNumber = T.PositiveInteger(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyStructure(OE.ODMElement):
    """Defines the high-level arms and epochs that constitute the study design.

    Attributes:
        Description: Optional description of the study structure.
        Arm (list): One or more arms (treatment groups) in the trial.
        Epoch (list): One or more epochs (time periods) in the trial.
        WorkflowRef: Reference to the workflow associated with the overall
            study structure.
    """

    Description = T.ODMObject(element_class=Description)
    Arm = T.ODMListObject(element_class=Arm)
    Epoch = T.ODMListObject(element_class=Epoch)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)


class ItemGroupRef(OE.ODMElement):
    """A reference to an ItemGroupDef within a StudyEventDef or ItemGroupDef.

    In ODM 2.0 the FormDef/FormRef layer is removed; StudyEventDef
    references ItemGroupDef directly via ItemGroupRef.

    Attributes:
        ItemGroupOID (str, required): OID of the referenced ItemGroupDef.
        OrderNumber (int): Position of this item group in the sequence.
        Mandatory (str, required): Whether collection of this item group is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this item group.
    """

    ItemGroupOID = T.OIDRef(required=True)
    MethodOID = T.OIDRef()
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class StudyEventDef(OE.ODMElement):
    """ represents ODM v2.0 StudyEventDef and can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Type = T.ValueSetString(required=True)
    Category = T.String(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        """ returns the number of ItemGroupRefs in an StudyEventDef object as the length """
        return len(self.ItemGroupRef)

    def __getitem__(self, position):
        """
        creates an iterator from an StudyEventDef object that returns the ItemGroupRef in position
        """
        return self.ItemGroupRef[position]

    def __iter__(self):
        return iter(self.ItemGroupRef)


class Selection(OE.ODMElement):
    """A path expression selecting a value within a Resource.

    .. versionadded:: 0.2.1
       Added so SourceItem can satisfy the ODM 2.0 XSD. The path previously
       lived on the non-XSD ``SourceItem.Path`` attribute.

    Attributes:
        Path (str, required): Path expression locating the source value.
    """

    Path = T.String(required=True)


class Resource(OE.ODMElement):
    """A named source of data referenced by a SourceItem.

    .. versionadded:: 0.2.1
       Added so SourceItem can satisfy the ODM 2.0 XSD, where Resource is a
       required child element. Its Name/Attribute/Label previously lived on
       the non-XSD ``SourceItem`` attributes of the same names.

    Attributes:
        Type (str, required): Kind of resource, e.g. a system or file type.
        Name (str, required): Name of the source resource.
        Attribute (str): Name of the source attribute within the resource.
        Label (str): Human-readable label for the resource.
        Selection (list): Path expressions locating values in the resource.
    """

    Type = T.String(required=True)
    Name = T.Name(required=True)
    Attribute = T.String()
    Label = T.String()
    Selection = T.ODMListObject(element_class=Selection)


class SourceItem(OE.ODMElement):
    """Identifies the source of an item's data within an Origin element.

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD. The attribute set now matches
       SourceItemAttributeDefinition: ``leadID`` was corrected to ``leafID``
       (and retyped from IDRef to OIDRef, matching ``type="oidref"``), and
       the missing ``ItemOID``, ``MetaDataVersionOID``, ``StudyOID`` and
       ``Name`` were added.

       The content model was corrected too. ``Resource``, ``Attribute``,
       ``Path`` and ``Label`` were **removed as attributes** -- they appear
       nowhere in the XSD -- and replaced by the required ``Resource`` child
       element (``minOccurs="1"``), which carries ``Type``/``Name``/
       ``Attribute``/``Label`` and holds ``Selection`` children carrying
       ``Path``. The optional ``Coding`` child was added at its XSD
       position. Before this a SourceItem could not be serialized in
       schema-valid form.

       **Breaking within draft ODM 2.0:** code setting
       ``SourceItem(Resource=..., Attribute=..., Path=..., Label=...)`` must
       move those values onto a ``Resource`` element, and ``Path`` onto a
       ``Selection`` beneath it.

    Attributes:
        ItemOID (str): OID of the source ItemDef.
        ItemGroupOID (str): OID of the source ItemGroupDef.
        MetaDataVersionOID (str): OID of the source MetaDataVersion.
        StudyOID (str): OID of the source Study.
        leafID (str): Reference to the Leaf holding the source document.
        Name (str): Name of the source item.
        Resource (list, required): One or more source resources.
        Coding (list): External terminology codings for this source item.
    """

    ItemOID = T.OIDRef()
    ItemGroupOID = T.OIDRef()
    MetaDataVersionOID = T.OIDRef()
    StudyOID = T.OIDRef()
    leafID = T.OIDRef()
    Name = T.Name()
    Resource = T.ODMListObject(required=True, element_class=Resource)
    Coding = T.ODMListObject(element_class=Coding)


class SourceItems(OE.ODMElement):
    """A container holding one or more SourceItem elements.

    Attributes:
        SourceItem (list, required): One or more SourceItem children
            describing where the data originated.
    """

    SourceItem = T.ODMListObject(element_class=SourceItem, required=True)
    Coding = T.ODMListObject(element_class=Coding)


class Origin(OE.ODMElement):
    """Describes the origin or provenance of an item's data.

    .. versionchanged:: 0.2.1
       Children reordered to the XSD sequence -- ``Description``,
       ``SourceItems``, ``DocumentRef``. odmlib serializes in declaration
       order, so the previous order emitted DocumentRef first and the
       document failed schema validation.

    Attributes:
        Type (str, required): Category of origin, e.g. "CRF", "Derived",
            "Predecessor", "Protocol", "eDT".
        Source (str): More specific source within the Type category.
        Description: Human-readable description of the origin.
        SourceItems: Structured source location details.
        DocumentRef (list): References to source documents.
    """

    Type = T.ValueSetString(required=True)
    Source = T.ValueSetString()
    Description = T.ODMObject(element_class=Description)
    SourceItems = T.ODMObject(element_class=SourceItems)
    Coding = T.ODMListObject(element_class=Coding)
    DocumentRef = T.ODMListObject(element_class=DocumentRef)


class WhereClauseRef(OE.ODMElement):
    WhereClauseOID = T.OIDRef(required=True)


class CheckValue(OE.ODMElement):
    """A single value used in a RangeCheck comparison.

    Attributes:
        _content (str, required): The check value as a string.
    """

    _content = T.String(required=True)


class ErrorMessage(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Code(OE.ODMElement):
    """The inline source text of a FormalExpression.

    Attributes:
        _content (str, required): The expression source, written in the
            language named by the parent FormalExpression's Context.
    """

    _content = T.String(required=True)


class ExternalCodeLib(OE.ODMElement):
    """A reference to a FormalExpression held in an external code library.

    Attributes:
        Library (str, required): Name of the external code library.
        Method (str): Name of the method or function within the library.
        Version (str): Version of the library.
        ref (str): Identifier of the expression within the library.
        href (str): URL locating the library or the expression.
    """

    Library = T.Name(required=True)
    Method = T.Name()
    Version = T.String()
    ref = T.String()
    href = T.String()


class FormalExpression(OE.ODMElement):
    """A formal expression (e.g. a computation or condition) in a specified language.

    In ODM 2.0 the expression is element-based: the XSD requires a choice of
    exactly one Code (inline source) or ExternalCodeLib (a reference to an
    external library).

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD. ``_content`` was removed -- the
       expression text now lives in a ``Code`` child. ODM 1.3.2
       FormalExpression is unchanged and remains text-based.

    .. note::

       **Known approximation.** The XSD requires exactly one of ``Code`` or
       ``ExternalCodeLib``. odmlib has no way to express an ``xs:choice`` --
       the metaclass sorts descriptors into attributes and children and has
       no concept of mutual exclusion -- so both are declared optional here.
       Setting neither, or both, builds an object odmlib accepts and the
       schema rejects. There is no Cerberus conformance schema for
       ``odm_2_0`` to enforce it in either, so
       :class:`~odmlib.odm_parser.ODMSchemaValidator` is the check that
       catches it.

    Attributes:
        Context (str): The language or context of the expression, e.g. an
            XPath version string.
        Code: The inline expression source.
        ExternalCodeLib: A reference to the expression in an external library.
    """

    Context = T.String()
    Code = T.ODMObject(element_class=Code)
    ExternalCodeLib = T.ODMObject(element_class=ExternalCodeLib)


class Parameter(OE.ODMElement):
    """Declares an input parameter for a MethodDef signature.

    Attributes:
        Name (str, required): Name of the parameter.
        Definition (str): Human-readable definition of the parameter.
        DataType (str, required): Data type of the parameter value.
        OrderNumber (int): Position of this parameter in the signature.
    """

    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class ReturnValue(OE.ODMElement):
    """Declares a return value for a MethodDef signature.

    Attributes:
        Name (str, required): Name of the return value.
        Definition (str): Human-readable definition of the return value.
        DataType (str, required): Data type of the return value.
        OrderNumber (int): Position of this return value in the signature.
    """

    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class MethodSignature(OE.ODMElement):
    """Describes the formal input/output signature of a MethodDef.

    Attributes:
        Parameter (list): Zero or more input parameters.
        ReturnValue (list): Zero or more return values.
    """

    Parameter = T.ODMListObject(element_class=Parameter)
    ReturnValue = T.ODMListObject(element_class=ReturnValue)


class RangeCheck(OE.ODMElement):
    """ represents ODM v2.0 RangeCheck element that is a child of ItemDef and can serialize as JSON or XML """

    Comparator = T.ValueSetString(required=False)
    SoftHard = T.ValueSetString()
    ItemOID = T.OIDRef()
    CheckValue = T.ODMListObject(element_class=CheckValue)
    MethodSignature = T.ODMObject(element_class=MethodSignature)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    ErrorMessage = T.ODMObject(element_class=ErrorMessage)


class WhereClauseDef(OE.ODMElement):
    OID = T.OID(required=True)
    CommentOID = T.OIDRef(required=False)
    RangeCheck = T.ODMListObject(required=True, element_class=RangeCheck)


class ItemRef(OE.ODMElement):
    """A reference to an ItemDef within an ItemGroupDef.

    Attributes:
        ItemOID (str, required): OID of the referenced ItemDef.
        OrderNumber (int): Position of this item within the item group.
        Mandatory (str, required): Whether collection is mandatory
            ("Yes" or "No").
        KeySequence (int): Position in the composite key, if this item is
            a key variable.
        MethodOID (str): OID of the MethodDef used to derive this item.
        Role (str): Semantic role of this item, e.g. "IDENTIFIER".
        RoleCodeListOID (str): OID of a CodeList that constrains Role values.
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this item.
        UnitsItemOID (str): OID of the item that carries the units for this item.
        PreSpecifiedValue (str): A pre-specified value for this item.
    """

    ItemOID = T.OIDRef(required=True)
    Mandatory = T.ValueSetString(required=True)
    Core = T.ValueSetString(required=False)
    OrderNumber = T.PositiveInteger(required=False)
    KeySequence = T.PositiveInteger(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    HasNoData = T.ValueSetString(required=False)
    MethodOID = T.OIDRef(required=False)
    UnitsItemOID = T.OIDRef(required=False)
    PreSpecifiedValue = T.String(required=False)
    Repeat = T.ValueSetString(required=False)
    Other = T.ValueSetString(required=False)
    Role = T.String(required=False)
    RoleCodeListOID = T.OIDRef(required=False)
    CollectionExceptionConditionOID = T.OIDRef(required=False)
    Origin = T.ODMListObject(element_class=Origin)
    WhereClauseRef = T.ODMListObject(element_class=WhereClauseRef)


class ValueListDef(OE.ODMElement):
    OID = T.OID(required=True)
    Description = T.ODMObject(required=False, element_class=Description)
    ItemRef = T.ODMListObject(required=True, element_class=ItemRef)


class SubClass(OE.ODMElement):
    """A subclass within a dataset class hierarchy.

    .. versionadded:: 0.2.1

    .. note::

       The ODM 2.0 XSD models the hierarchy through the flat ``ParentClass``
       attribute rather than by nesting SubClass elements, so this class has
       no children.

    Attributes:
        Name (str, required): The subclass name, e.g. "ADVERSE EVENT".
        ParentClass (str): The class or subclass this one sits beneath.
    """

    Name = T.ValueSetString(required=True)
    ParentClass = T.ValueSetString()


class Class(OE.ODMElement):
    """The general observation class of an ItemGroupDef.

    .. versionadded:: 0.2.1
       ODM 2.0 models the dataset class as a child *element* with a ``Name``
       attribute, not as the Define-XML-style ``ItemGroupDef/@Class``
       attribute.

    Attributes:
        Name (str, required): The class name, e.g. "FINDINGS".
        SubClass (list): Subclasses beneath this class.
    """

    Name = T.ValueSetString(required=True)
    SubClass = T.ODMListObject(element_class=SubClass)


class ItemGroupDef(OE.ODMElement):
    """ represents ODM v2.0 ItemGroupDef and can serialize as JSON or XML"""

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    RepeatingLimit = T.PositiveInteger(required=False)
    IsReferenceData = T.ValueSetString(required=False)
    DatasetName = T.Name(required=False)
    Domain = T.String(required=False)
    Type = T.ValueSetString(required=True)
    Purpose = T.String(required=False)
    Structure = T.String(required=False)
    ArchiveLocationID = T.OIDRef(required=False)
    StandardOID = T.OIDRef(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    HasNoData = T.ValueSetString(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Class = T.ODMObject(element_class=Class)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    ItemRef = T.ODMListObject(element_class=ItemRef)
    Coding = T.ODMListObject(element_class=Coding)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    Origin = T.ODMListObject(element_class=Origin)
    Alias = T.ODMListObject(element_class=Alias)
    Leaf = T.ODMObject(element_class=Leaf)

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class Definition(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Question(OE.ODMElement):
    """The question text shown to a data entry operator for an ItemDef.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks containing the question text.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


# TODO Deprecated
# class ExternalQuestion(OE.ODMElement):
#     """A reference to a question defined in an external dictionary or instrument.
#
#     Attributes:
#         Dictionary (str): Name of the external dictionary or instrument.
#         Version (str): Version of the dictionary or instrument.
#         Code (str): Code that identifies the question within the dictionary.
#     """
#
#     Dictionary = T.String(required=False)
#     Version = T.String(required=False)
#     Code = T.String(required=False)


class Prompt(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)

# TODO Deprecated
# class MeasurementUnitRef(OE.ODMElement):
#     """A reference to a MeasurementUnit defined in the BasicDefinitions section.
#
#     Attributes:
#         MeasurementUnitOID (str, required): OID of the referenced
#             MeasurementUnit.
#     """
#
#     MeasurementUnitOID = T.String(required=True)

class CRFCompletionInstructions(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class ImplementationNotes(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CDISCNotes(OE.ODMElement):
    """A human-readable error message associated with a RangeCheck.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks containing the error message.
    """
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListRef(OE.ODMElement):
    """A reference from an ItemDef to its associated CodeList.

    Attributes:
        CodeListOID (str, required): OID of the referenced CodeList.
    """

    CodeListOID = T.OIDRef("CodeListOID", required=True)


class ValueListRef(OE.ODMElement):
    """A reference from an ItemDef to a ValueListDef.

    .. versionadded:: 0.2.1

    Attributes:
        ValueListOID (str, required): OID of the referenced ValueListDef.
    """

    ValueListOID = T.OIDRef(required=True)


class ItemDef(OE.ODMElement):
    """ represents ODM v2.0 ItemDef and can serialize as JSON or XML - ordering of properties matters """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    Length = T.PositiveInteger()
    DisplayFormat = T.String()
    VariableSet = T.String()
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Definition = T.ODMObject(element_class=Definition)
    Question = T.ODMObject(element_class=Question)
    Prompt = T.ODMObject(element_class=Prompt)
    CRFCompletionInstructions = T.ODMObject(element_class=CRFCompletionInstructions)
    ImplementationNotes = T.ODMObject(element_class=ImplementationNotes)
    CDISCNotes = T.ODMObject(element_class=CDISCNotes)
    RangeCheck = T.ODMListObject(element_class=RangeCheck)
    CodeListRef = T.ODMObject(element_class=CodeListRef)
    ValueListRef = T.ODMObject(element_class=ValueListRef)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


class Decode(OE.ODMElement):
    """The decoded (display) text for a CodeListItem value.

    Attributes:
        TranslatedText (list, required): One or more language-tagged text
            blocks with the decoded label for the coded value.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListItem(OE.ODMElement):
    """ represents ODM CodeListItem element that is a child of CodeList and can serialize as JSON or XML """

    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    Other = T.ValueSetString(required=False)
    OrderNumber = T.PositiveInteger(required=False)
    ExtendedValue = T.ValueSetString(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Decode = T.ODMObject(element_class=Decode)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


# TODO Deprecated
# class ExternalCodeList(OE.ODMElement):
#     """A reference to a code list defined externally, outside the ODM document.
#
#     Attributes:
#         Dictionary (str): Name of the external dictionary or terminology.
#         Version (str): Version of the external dictionary.
#         ref (str): A reference identifier within the external dictionary.
#         href (str): A URL pointing to the external code list resource.
#     """
#
#     Dictionary = T.String(required=False)
#     Version = T.String(required=False)
#     ref = T.String(required=False)
#     href = T.String(required=False)

class CodeList(OE.ODMElement):
    """ represents ODM CodeList element that can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    CommentOID = T.OIDRef(required=False)
    StandardOID = T.OIDRef(required=False)
    IsNonStandard = T.ValueSetString(required=False)
    Description = T.ODMObject(element_class=Description)
    CodeListItem = T.ODMListObject(element_class=CodeListItem)
    Coding = T.ODMListObject(element_class=Coding)
    Alias = T.ODMListObject(element_class=Alias)


class ConditionDef(OE.ODMElement):
    """Defines a Boolean condition used to control collection of items or events.

    ConditionDef is referenced by CollectionExceptionConditionOID attributes
    on ItemRef, ItemGroupRef, StudyEventRef, and StudyEventGroupRef.

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD: ``MethodSignature`` was added and
       ``Description`` became required. Both are ``minOccurs="1"`` in the
       XSD.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        CommentOID (str): OID of an associated CommentDef.
        Description (required): Description of the condition.
        MethodSignature (required): The formal input/output signature of the
            condition's expressions.
        FormalExpression (list): One or more formal expressions encoding the
            condition logic.
        Alias (list): Alternative identifiers in external contexts.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(required=True, element_class=Description)
    MethodSignature = T.ODMObject(required=True, element_class=MethodSignature)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class MethodDef(OE.ODMElement):
    """ represents ODM v2.0 MethodDef and can serialize as JSON or XML """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString()
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(required=True, element_class=Description)
    MethodSignature = T.ODMObject(required=True, element_class=MethodSignature)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)
    DocumentRef = T.ODMListObject(element_class=DocumentRef)


class StudyEventGroupRef(OE.ODMElement):
    """A reference to a StudyEventGroupDef within an ExceptionEvent or similar element.

    Attributes:
        StudyEventGroupOID (str, required): OID of the referenced
            StudyEventGroupDef.
        OrderNumber (int): Position of this reference in the sequence.
        Mandatory (str, required): Whether this study event group is
            mandatory ("Yes" or "No").
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, suppresses collection of this event group.
        Description: Optional description.
    """

    StudyEventGroupOID = T.OIDRef(required=True)
    OrderNumber = T.Integer()
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)


class WorkflowStart(OE.ODMElement):
    """Identifies the starting point of a WorkflowDef.

    Attributes:
        StartOID (str, required): OID reference to the first study event
            group or study event in the workflow.
    """

    StartOID = T.OIDRef(required=True)


class Transition(OE.ODMElement):
    """Defines a directed edge (transition) between two nodes in a workflow.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        SourceOID (str, required): OID reference to the source workflow node.
        TargetOID (str, required): OID reference to the target workflow node.
        StartConditionOID (str): OID of a ConditionDef that must be true to
            enter this transition.
        EndConditionOID (str): OID of a ConditionDef that must be true to
            leave this transition.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SourceOID = T.OIDRef(required=True)
    TargetOID = T.OIDRef(required=True)
    StartConditionOID = T.OIDRef()
    EndConditionOID = T.OIDRef()


class TargetTransition(OE.ODMElement):
    """Associates a conditional transition with a branching decision point.

    Attributes:
        TargetTransitionOID (str, required): OID reference to the Transition
            that should be taken.
        ConditionOID (str): OID of the ConditionDef that must be true to
            take this transition.
    """

    TargetTransitionOID = T.OIDRef(required=True)
    ConditionOID = T.OIDRef()


class DefaultTransition(OE.ODMElement):
    """Specifies the fallback transition taken when no other branch condition is met.

    Attributes:
        TargetTransitionOID (str, required): OID reference to the Transition
            used when none of the conditional branches apply.
    """

    TargetTransitionOID = T.OIDRef(required=True)


class Branching(OE.ODMElement):
    """Defines a branching decision point within a workflow.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Type (str, required): Branching type; controls whether one or
            multiple branches may be taken simultaneously.
        TargetTransition (list, required): One or more conditional
            transitions that may be taken at this branch.
        DefaultTransition (list): Zero or more default transitions taken
            when no conditional branch applies.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    TargetTransition = T.ODMListObject(element_class=TargetTransition, required=True)
    DefaultTransition = T.ODMListObject(element_class=DefaultTransition)


class WorkflowEnd(OE.ODMElement):
    """Identifies an endpoint of a WorkflowDef.

    .. versionchanged:: 0.2.1
       Added ``_content``. The XSD types WorkflowEnd as ``xs:simpleContent``
       over ``text``, and the model had no text member at all.

    Attributes:
        EndOID (str, required): OID reference to the last study event group
            or study event in this workflow path.
        _content (str): Optional text describing the endpoint.
    """

    EndOID = T.OIDRef(required=True)
    _content = T.String()


class WorkflowDef(OE.ODMElement):
    """Defines a workflow (sequence of study events) in ODM 2.0.

    A workflow defines the possible paths through study events,
    including transitions, branching, and timing constraints.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Description: Optional description.
        WorkflowStart (required): Starting point OID reference.
        Transition (list): Directed edges between workflow nodes.
        Branching (list): Decision points where the path may branch.
        WorkflowEnd (list, required): One or more workflow end points.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowStart = T.ODMObject(element_class=WorkflowStart, required=True)
    Transition = T.ODMListObject(element_class=Transition)
    Branching = T.ODMListObject(element_class=Branching)
    WorkflowEnd = T.ODMListObject(element_class=WorkflowEnd, required=True)


class AbsoluteTimingConstraint(OE.ODMElement):
    """Defines an absolute time-based constraint for a study event.

    Specifies when a study event should occur relative to an absolute
    date/time, with allowed pre- and post-windows.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        StudyEventGroupOID (str): OID of the constrained study event group.
        StudyEventOID (str): OID of the constrained study event.
        TimepointTarget (str, required): Incomplete datetime target for when
            the event should occur.
        TimepointPreWindow (str): ISO 8601 duration for the allowable
            window before the target.
        TimepointPostWindow (str): ISO 8601 duration for the allowable
            window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StudyEventGroupOID = T.OIDRef()
    StudyEventOID = T.OIDRef()
    TimepointTarget = T.IncompleteDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString()
    TimepointPostWindow = T.DurationDateTimeString()
    Description = T.ODMObject(element_class=Description)


class RelativeTimingConstraint(OE.ODMElement):
    """Defines a relative time-based constraint between two study events.

    Specifies when a successor event should occur relative to a predecessor
    event, with allowed pre- and post-windows.

    .. versionchanged:: 0.2.1
       The four ``Predecessor*``/``Successor*`` OID attributes were replaced
       by ``PredecessorOID`` and ``SuccessorOID``. The XSD names only those
       two, and either may reference any structural element, so the split by
       event-vs-group was both wrong and unnecessary.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        PredecessorOID (str): OID of the predecessor structural element.
        SuccessorOID (str): OID of the successor structural element.
        Type (str): The type of relative timing relationship.
        TimepointRelativeTarget (str, required): ISO 8601 duration from the
            predecessor to the target timepoint.
        TimepointPreWindow (str): ISO 8601 duration for the allowable
            window before the target.
        TimepointPostWindow (str): ISO 8601 duration for the allowable
            window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    PredecessorOID = T.OIDRef()
    SuccessorOID = T.OIDRef()
    Type = T.ValueSetString()
    TimepointRelativeTarget = T.DurationDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString()
    TimepointPostWindow = T.DurationDateTimeString()
    Description = T.ODMObject(element_class=Description)


class TransitionTimingConstraint(OE.ODMElement):
    """Defines a timing constraint on a workflow transition.

    Specifies how long after a predecessor event a given workflow
    transition should occur.

    .. versionchanged:: 0.2.1
       ``TimepointRelativeTarget`` was replaced by the XSD's
       ``TimepointTarget``, and the missing ``Type`` attribute was added.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        TransitionOID (str, required): OID of the Transition being constrained.
        MethodOID (str): OID of a MethodDef used to compute the target time.
        Type (str): The type of relative timing relationship.
        TimepointTarget (str, required): ISO 8601 duration for the nominal
            timepoint relative to the predecessor.
        TimepointPreWindow (str): ISO 8601 duration for the allowable
            window before the target.
        TimepointPostWindow (str): ISO 8601 duration for the allowable
            window after the target.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    TransitionOID = T.OIDRef(required=True)
    MethodOID = T.OIDRef()
    Type = T.ValueSetString()
    TimepointTarget = T.DurationDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString()
    TimepointPostWindow = T.DurationDateTimeString()
    Description = T.ODMObject(element_class=Description)


class DurationTimingConstraint(OE.ODMElement):
    """Defines a constraint on the expected duration of a structural element.

    Specifies the nominal duration for an arm, epoch, or similar structural
    element, with allowed pre- and post-windows.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        StructuralElementOID (str, required): OID of the structural element
            (e.g. an Arm or Epoch) whose duration is constrained.
        DurationTarget (str, required): ISO 8601 duration for the expected
            length of the structural element.
        DurationPreWindow (str): ISO 8601 duration for the allowable
            window before the target duration.
        DurationPostWindow (str): ISO 8601 duration for the allowable
            window after the target duration.
        Description: Optional description.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StructuralElementOID = T.OIDRef(required=True)
    DurationTarget = T.DurationDateTimeString(required=True)
    DurationPreWindow = T.DurationDateTimeString()
    DurationPostWindow = T.DurationDateTimeString()
    Description = T.ODMObject(element_class=Description)


class StudyTiming(OE.ODMElement):
    """A named container grouping all timing constraints for a study.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        AbsoluteTimingConstraint (list): Absolute time-based constraints.
        RelativeTimingConstraint (list): Relative time-based constraints
            between events.
        TransitionTimingConstraint (list): Timing constraints on workflow
            transitions.
        DurationTimingConstraint (list): Duration constraints on structural
            elements.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    AbsoluteTimingConstraint = T.ODMListObject(element_class=AbsoluteTimingConstraint)
    RelativeTimingConstraint = T.ODMListObject(element_class=RelativeTimingConstraint)
    TransitionTimingConstraint = T.ODMListObject(element_class=TransitionTimingConstraint)
    DurationTimingConstraint = T.ODMListObject(element_class=DurationTimingConstraint)


class StudyTimings(OE.ODMElement):
    """The set of StudyTiming containers belonging to a Protocol.

    .. versionadded:: 0.2.1
       Added to align with the ODM 2.0 XSD, where timing lives under
       ``Protocol/StudyTimings`` rather than directly on MetaDataVersion.

    Attributes:
        StudyTiming (list, required): One or more StudyTiming containers.
    """

    StudyTiming = T.ODMListObject(required=True, element_class=StudyTiming)


class ParameterValue(OE.ODMElement):
    """The value of a StudyParameter.

    .. versionadded:: 0.2.1

    Attributes:
        Value (str, required): The parameter value.
        Coding (list): External terminology codings for the value.
    """

    Value = T.String(required=True)
    Coding = T.ODMListObject(element_class=Coding)


class StudyParameter(OE.ODMElement):
    """A single named parameter in the StudySummary.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Term (str, required): The parameter's term, e.g. "Trial Blinding Schema".
        ShortName (str): A short form of the term.
        ParameterValue (required): The parameter's value.
        Coding (list): External terminology codings for the parameter.
    """

    OID = T.OID(required=True)
    Term = T.Name(required=True)
    ShortName = T.Name()
    ParameterValue = T.ODMObject(required=True, element_class=ParameterValue)
    Coding = T.ODMListObject(element_class=Coding)


class StudySummary(OE.ODMElement):
    """The set of summary parameters describing a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyParameter (list, required): One or more study parameters.
    """

    StudyParameter = T.ODMListObject(required=True, element_class=StudyParameter)


class TrialPhase(OE.ODMElement):
    """The phase of the trial.

    .. versionadded:: 0.2.1

    Attributes:
        Value (str, required): The trial phase, e.g. "PHASE III TRIAL".
        Description: Optional description.
    """

    Value = T.ValueSetString(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyIndication(OE.ODMElement):
    """A condition the study is intended to address.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Description (required): Description of the indication.
        Coding (list): External terminology codings.
    """

    OID = T.OID(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    Coding = T.ODMListObject(element_class=Coding)


class StudyIndications(OE.ODMElement):
    """The set of indications for a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyIndication (list, required): One or more indications.
    """

    StudyIndication = T.ODMListObject(required=True,
                                      element_class=StudyIndication)


class StudyIntervention(OE.ODMElement):
    """A treatment or procedure administered during the study.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Description (required): Description of the intervention.
        Coding (list): External terminology codings.
    """

    OID = T.OID(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    Coding = T.ODMListObject(element_class=Coding)


class StudyInterventions(OE.ODMElement):
    """The set of interventions for a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyIntervention (list, required): One or more interventions.
    """

    StudyIntervention = T.ODMListObject(required=True,
                                        element_class=StudyIntervention)


class StudyInterventionRef(OE.ODMElement):
    """A reference to a StudyIntervention.

    .. versionadded:: 0.2.1

    Attributes:
        StudyInterventionOID (str, required): OID of the referenced
            StudyIntervention.
    """

    StudyInterventionOID = T.OIDRef(required=True)


class StudyEndPoint(OE.ODMElement):
    """A measurable outcome used to assess a study objective.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Type (str): Endpoint category, e.g. "Simple", "Composite".
        Level (str): "Primary", "Secondary" or "Exploratory".
        Description (required): Description of the endpoint.
        FormalExpression (list): Expressions defining the endpoint.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString()
    Level = T.ValueSetString()
    Description = T.ODMObject(required=True, element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)


class StudyEndPoints(OE.ODMElement):
    """The set of endpoints for a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyEndPoint (list, required): One or more endpoints.
    """

    StudyEndPoint = T.ODMListObject(required=True, element_class=StudyEndPoint)


class StudyEndPointRef(OE.ODMElement):
    """A reference to a StudyEndPoint.

    .. versionadded:: 0.2.1

    Attributes:
        StudyEndPointOID (str, required): OID of the referenced StudyEndPoint.
        OrderNumber (int): Position of this reference in the sequence.
    """

    StudyEndPointOID = T.OIDRef(required=True)
    OrderNumber = T.PositiveInteger()


class StudyObjective(OE.ODMElement):
    """A stated aim of the study.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Level (str): "Primary", "Secondary" or "Exploratory".
        Description: Optional description.
        StudyEndPointRef (list): Endpoints assessing this objective.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Level = T.ValueSetString()
    Description = T.ODMObject(element_class=Description)
    StudyEndPointRef = T.ODMListObject(element_class=StudyEndPointRef)


class StudyObjectives(OE.ODMElement):
    """The set of objectives for a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyObjective (list, required): One or more objectives.
    """

    StudyObjective = T.ODMListObject(required=True,
                                     element_class=StudyObjective)


class StudyTargetPopulation(OE.ODMElement):
    """The population the study is intended to enrol.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Description (required): Description of the population.
        Coding (list): External terminology codings.
        FormalExpression (list): Expressions defining the population.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    Coding = T.ODMListObject(element_class=Coding)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)


class StudyTargetPopulationRef(OE.ODMElement):
    """A reference to the StudyTargetPopulation.

    .. versionadded:: 0.2.1

    Attributes:
        StudyTargetPopulationOID (str, required): OID of the referenced
            StudyTargetPopulation.
    """

    StudyTargetPopulationOID = T.OIDRef(required=True)


class IntercurrentEvent(OE.ODMElement):
    """An event occurring after treatment start that affects an estimand.

    .. versionadded:: 0.2.1

    Attributes:
        Description (required): Description of the event and its handling.
    """

    Description = T.ODMObject(required=True, element_class=Description)


class SummaryMeasure(OE.ODMElement):
    """The population-level summary an estimand reports.

    .. versionadded:: 0.2.1

    Attributes:
        Description (required): Description of the summary measure.
    """

    Description = T.ODMObject(required=True, element_class=Description)


class StudyEstimand(OE.ODMElement):
    """A precise description of the treatment effect the study estimates.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        Level (str): "Primary", "Secondary" or "Exploratory".
        Description: Optional description.
        StudyTargetPopulationRef: The population the estimand applies to.
        StudyInterventionRef: The intervention under study.
        StudyEndPointRef: The endpoint being estimated.
        IntercurrentEvent (list): Events affecting the estimand and how they
            are handled.
        SummaryMeasure: The population-level summary reported.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Level = T.ValueSetString()
    Description = T.ODMObject(element_class=Description)
    StudyTargetPopulationRef = T.ODMObject(
        element_class=StudyTargetPopulationRef)
    StudyInterventionRef = T.ODMObject(element_class=StudyInterventionRef)
    StudyEndPointRef = T.ODMObject(element_class=StudyEndPointRef)
    IntercurrentEvent = T.ODMListObject(element_class=IntercurrentEvent)
    SummaryMeasure = T.ODMObject(element_class=SummaryMeasure)


class StudyEstimands(OE.ODMElement):
    """The set of estimands for a study.

    .. versionadded:: 0.2.1

    Attributes:
        StudyEstimand (list, required): One or more estimands.
    """

    StudyEstimand = T.ODMListObject(required=True, element_class=StudyEstimand)


class Criterion(OE.ODMElement):
    """A single inclusion or exclusion criterion.

    .. versionadded:: 0.2.1

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        ConditionOID (str, required): OID of the ConditionDef encoding the
            criterion.
        Description: Optional description.
        Coding (list): External terminology codings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ConditionOID = T.OIDRef(required=True)
    Description = T.ODMObject(element_class=Description)
    Coding = T.ODMListObject(element_class=Coding)


class InclusionCriteria(OE.ODMElement):
    """The criteria a subject must meet to enter the study.

    .. versionadded:: 0.2.1

    Attributes:
        Criterion (list, required): One or more criteria.
    """

    Criterion = T.ODMListObject(required=True, element_class=Criterion)


class ExclusionCriteria(OE.ODMElement):
    """The criteria that disqualify a subject from the study.

    .. versionadded:: 0.2.1

    Attributes:
        Criterion (list, required): One or more criteria.
    """

    Criterion = T.ODMListObject(required=True, element_class=Criterion)


class InclusionExclusionCriteria(OE.ODMElement):
    """The study's eligibility criteria.

    .. versionadded:: 0.2.1

    Attributes:
        InclusionCriteria: Criteria for entering the study.
        ExclusionCriteria: Criteria that disqualify a subject.
    """

    InclusionCriteria = T.ODMObject(element_class=InclusionCriteria)
    ExclusionCriteria = T.ODMObject(element_class=ExclusionCriteria)


class Protocol(OE.ODMElement):
    """Defines the overall structure of the study protocol in ODM 2.0.

    Lists the study event groups that constitute the protocol, together with
    the study structure, its timing constraints, its workflow and any
    aliases.

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD: ``StudyEventRef`` was removed -- the XSD
       reaches study events through ``StudyEventGroupRef`` ->
       ``StudyEventGroupDef`` -- and ``StudyTimings``, ``StudyEventGroupRef``
       and ``WorkflowRef`` were added.

    .. versionchanged:: 0.2.1
       The nine optional study-design children the XSD defines --
       ``StudySummary``, ``TrialPhase``, ``StudyIndications``,
       ``StudyInterventions``, ``StudyObjectives``, ``StudyEndPoints``,
       ``StudyTargetPopulation``, ``StudyEstimands`` and
       ``InclusionExclusionCriteria`` -- were added. All are
       ``minOccurs="0"``, so existing documents are unaffected.

    Attributes:
        Description: Optional human-readable description.
        StudySummary: Named summary parameters describing the study.
        StudyStructure: The arms and epochs that make up the study design.
        TrialPhase: The phase of the trial.
        StudyTimings: Container for the study's timing constraints.
        StudyIndications: The conditions the study addresses.
        StudyInterventions: The treatments administered during the study.
        StudyObjectives: The study's stated aims.
        StudyEndPoints: The outcomes used to assess the objectives.
        StudyTargetPopulation: The population the study intends to enrol.
        StudyEstimands: The treatment effects the study estimates.
        InclusionExclusionCriteria: The study's eligibility criteria.
        StudyEventGroupRef (list): Ordered references to the
            StudyEventGroupDef elements that make up this protocol.
        WorkflowRef: Reference to the workflow that governs the protocol.
        Alias (list): Alternative names for this protocol in external contexts.
    """

    Description = T.ODMObject(element_class=Description)
    StudySummary = T.ODMObject(element_class=StudySummary)
    StudyStructure = T.ODMObject(element_class=StudyStructure)
    TrialPhase = T.ODMObject(element_class=TrialPhase)
    StudyTimings = T.ODMObject(element_class=StudyTimings)
    StudyIndications = T.ODMObject(element_class=StudyIndications)
    StudyInterventions = T.ODMObject(element_class=StudyInterventions)
    StudyObjectives = T.ODMObject(element_class=StudyObjectives)
    StudyEndPoints = T.ODMObject(element_class=StudyEndPoints)
    StudyTargetPopulation = T.ODMObject(element_class=StudyTargetPopulation)
    StudyEstimands = T.ODMObject(element_class=StudyEstimands)
    InclusionExclusionCriteria = T.ODMObject(
        element_class=InclusionExclusionCriteria)
    StudyEventGroupRef = T.ODMListObject(element_class=StudyEventGroupRef)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    Alias = T.ODMListObject(element_class=Alias)


class StudyEventGroupDef(OE.ODMElement):
    """Defines a group of study events associated with a specific arm and epoch.

    StudyEventGroupDef maps a set of study events to their position in the
    trial by linking them to a particular Arm and Epoch.

    .. versionchanged:: 0.2.1
       Aligned with the ODM 2.0 XSD. The required child group and the
       optional WorkflowRef and Coding children were added -- before this
       the element could not satisfy its own content model. On the attribute
       side ``CommentOID`` was added, and ``ArmOID`` and ``EpochOID`` were
       relaxed from required to optional to match ``use="optional"`` in the
       XSD's StudyEventGroupDefAttributeDefinition group.

    .. note::

       **Known approximation.** The XSD models the children as a repeating
       group, ``(StudyEventGroupRef?, StudyEventRef?)`` with
       ``maxOccurs="unbounded"``, which permits the two to interleave.
       odmlib has no repeating-group descriptor -- a descriptor maps to one
       homogeneous list -- so this is approximated with two parallel lists.
       Serialization emits every StudyEventGroupRef and then every
       StudyEventRef, which is one valid instance of the XSD group but
       cannot reproduce an interleaved ordering. Reading is affected too:
       the loader collects children by tag name, so an interleaved source
       document loads correctly but re-serializes grouped. Both forms are
       schema-valid; only the original ordering is lost.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name.
        ArmOID (str): OID of the Arm this event group belongs to.
        EpochOID (str): OID of the Epoch this event group belongs to.
        CommentOID (str): OID of an associated CommentDef.
        Description: Optional description.
        StudyEventGroupRef (list): References to nested study event groups.
        StudyEventRef (list): References to the study events in this group.
        WorkflowRef: Reference to the workflow governing this event group.
        Coding (list): External terminology codings for this event group.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ArmOID = T.OIDRef(required=False)
    EpochOID = T.OIDRef(required=False)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    StudyEventGroupRef = T.ODMListObject(element_class=StudyEventGroupRef)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    Coding = T.ODMListObject(element_class=Coding)


class MetaDataVersion(OE.ODMElement):
    """A versioned snapshot of all metadata for a study in ODM 2.0.

    MetaDataVersion holds the complete metadata definition including
    the protocol, study structure, workflows, event/item group/item
    definitions, code lists, conditions, and methods. Timing constraints
    hang off Protocol/StudyTimings, not off MetaDataVersion.

    .. versionchanged:: 0.2.1
       ``StudyTiming`` was removed; the ODM 2.0 XSD has no such
       MetaDataVersion child. Use ``Protocol.StudyTimings.StudyTiming``.
       ``CommentDef`` was added at its XSD position, making it possible for
       a ``CommentOID`` reference to resolve under ``verify_oids()``.
       ``Leaf`` was added at its XSD position (last), so a ``DocumentRef``
       can point at a Leaf that actually exists in the document -- the XSD
       types ``DocumentRef/@LeafID`` as ``xs:IDREF``, so without a Leaf any
       DocumentRef-bearing document failed schema validation.

    Attributes:
        OID (str, required): Unique identifier for this metadata version.
        Name (str, required): Human-readable name.
        Description: Optional description.
        Include: Reference to metadata imported from another study.
        Protocol: The protocol defining the ordered set of study events.
        StudyStructure: Arms and epochs that make up the study design.
        WorkflowDef (list): Workflow definitions.
        StudyEventGroupDef (list): Study event group definitions.
        StudyEventDef (list): Study event definitions.
        ItemGroupDef (list): Item group (dataset) definitions.
        ItemDef (list): Item (variable) definitions.
        CodeList (list): Controlled terminology code lists.
        ConditionDef (list): Condition definitions used for collection
            exception logic.
        MethodDef (list): Method (derivation/computation) definitions.
        CommentDef (list): Comment definitions targeted by the CommentOID
            attributes elsewhere in the metadata.
        Leaf (list): Document locations targeted by DocumentRef/@LeafID.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    CommentOID = T.OIDRef(required=False)
    Description = T.ODMObject(element_class=Description)
    Include = T.ODMObject(element_class=Include)
    Standards = T.ODMObject(element_class=Standards)
    AnnotatedCRF = T.ODMObject(element_class=AnnotatedCRF)
    SupplementalDoc = T.ODMObject(element_class=SupplementalDoc)
    ValueListDef = T.ODMListObject(element_class=ValueListDef)
    WhereClauseDef = T.ODMListObject(element_class=WhereClauseDef)
    Protocol = T.ODMObject(element_class=Protocol)
    WorkflowDef = T.ODMListObject(element_class=WorkflowDef)
    StudyEventGroupDef = T.ODMListObject(element_class=StudyEventGroupDef)
    StudyEventDef = T.ODMListObject(element_class=StudyEventDef)
    ItemGroupDef = T.ODMListObject(element_class=ItemGroupDef)
    ItemDef = T.ODMListObject(element_class=ItemDef)
    CodeList = T.ODMListObject(element_class=CodeList)
    ConditionDef = T.ODMListObject(element_class=ConditionDef)
    MethodDef = T.ODMListObject(element_class=MethodDef)
    CommentDef = T.ODMListObject(element_class=CommentDef)
    Leaf = T.ODMListObject(element_class=Leaf)


class UserName(OE.ODMElement):
    """The login name (username) used by a User to authenticate.

    Attributes:
        _content (str, required): The login name string.
    """

    _content = T.String(required=True)


class Prefix(OE.ODMElement):
    """An honorific preceding a User's name, e.g. "Dr".

    .. versionadded:: 0.2.1
       The XSD models Prefix as a User child *element*; the model previously
       carried it as a User attribute.

    Attributes:
        _content (str, required): The prefix string.
    """

    _content = T.String(required=True)


class Suffix(OE.ODMElement):
    """A qualifier following a User's name, e.g. "PhD".

    .. versionadded:: 0.2.1
       The XSD models Suffix as a User child *element*; the model previously
       carried it as a User attribute.

    Attributes:
        _content (str, required): The suffix string.
    """

    _content = T.String(required=True)


class FullName(OE.ODMElement):
    """The full legal name of a User.

    Attributes:
        _content (str, required): The full name string.
    """

    _content = T.String(required=True)


class GivenName(OE.ODMElement):
    """The first (given) name of a User.

    Attributes:
        _content (str, required): The first name string.
    """

    _content = T.String(required=True)


class FamilyName(OE.ODMElement):
    """The last (family) name of a User.

    Attributes:
        _content (str, required): The last name string.
    """

    _content = T.String(required=True)


class StreetName(OE.ODMElement):
    """A line of a street address for a User's Address.

    Attributes:
        _content (str, required): One street address line.
    """

    _content = T.String(required=True)


class City(OE.ODMElement):
    """The city component of a User's Address.

    Attributes:
        _content (str, required): The city name.
    """

    _content = T.String(required=True)


class StateProv(OE.ODMElement):
    """The state or province component of a User's Address.

    Attributes:
        _content (str, required): The state or province name or code.
    """

    _content = T.String(required=True)


class Country(OE.ODMElement):
    """The country component of a User's Address.

    Attributes:
        _content (str, required): ISO 3166-1 alpha-2 country code.
    """

    _content = T.ValueSetString(required=True)


class PostalCode(OE.ODMElement):
    """The postal or ZIP code component of a User's Address.

    Attributes:
        _content (str, required): The postal code string.
    """

    _content = T.String(required=True)


class OtherText(OE.ODMElement):
    """Additional free-form address text not captured by other Address children.

    Attributes:
        _content (str, required): Free-form address text.
    """

    _content = T.String(required=True)


class HouseNumber(OE.ODMElement):
    """The house or building number part of an Address.

    .. versionadded:: 0.2.1

    Attributes:
        _content (str, required): The house number.
    """

    _content = T.String(required=True)


class GeoPosition(OE.ODMElement):
    """The geographic coordinates of an Address.

    .. versionadded:: 0.2.1

    Attributes:
        Longitude (float): Degrees east of the prime meridian.
        Latitude (float): Degrees north of the equator.
        Altitude (float): Height above sea level.
    """

    Longitude = T.Float()
    Latitude = T.Float()
    Altitude = T.Float()


class Address(OE.ODMElement):
    """A postal address for a User.

    Attributes:
        StreetName: The street address line.
        City: City name.
        StateProv: State or province.
        Country: Country code.
        PostalCode: Postal or ZIP code.
        OtherText: Any additional address information.
    """

    StreetName = T.ODMObject(element_class=StreetName)
    HouseNumber = T.ODMObject(element_class=HouseNumber)
    City = T.ODMObject(element_class=City)
    StateProv = T.ODMObject(element_class=StateProv)
    Country = T.ODMObject(element_class=Country)
    PostalCode = T.ODMObject(element_class=PostalCode)
    GeoPosition = T.ODMObject(element_class=GeoPosition)
    OtherText = T.ODMObject(element_class=OtherText)


class LocationRef(OE.ODMElement):
    """A reference to a Location where a User is associated.

    Attributes:
        LocationOID (str, required): OID of the referenced Location.
    """

    LocationOID = T.OIDRef(required=True)


# TODO deprecated
# class Certificate(OE.ODMElement):
#     """A digital certificate associated with a User for signature purposes.
#
#     Attributes:
#         _content (str, required): The certificate data (typically base64-encoded).
#     """
#
#     _content = T.String(required=True)


class Image(OE.ODMElement):
    """An image associated with a User."""
    ImageFileName = T.FileName(required=False)
    href = T.String(required=False)
    MimeType = T.String(required=False)

# TODO ensure the type information for TelecomType is there
class Telecom(OE.ODMElement):
    """Telecommunications contact information for a User or Organization.

    .. versionchanged:: 0.2.1
       ``value`` was corrected to ``Value`` to match
       TelecomAttributeDefinition in the ODM 2.0 XSD. The lower-case spelling
       made every document containing a Telecom schema-invalid.

    Attributes:
        TelecomType (str, required): Kind of contact, e.g. "Email", "Phone".
        Value (str, required): The address or number itself.
    """

    TelecomType = T.ValueSetString(required=True)
    Value = T.String(required=True)


class Organization(OE.ODMElement):
    """An organization taking part in the study, held in AdminData.

    .. versionchanged:: 0.2.1
       Replaced a text-only leaf carried over from ODM 1.3.2 -- orphaned in
       the ODM 2.0 model, referenced by nothing -- with the element the ODM
       2.0 XSD defines. Organization is now an AdminData child in its own
       right; a User links to one through ``OrganizationOID``.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Name of the organization.
        Role (str): The organization's role in the study.
        Type (str, required): Category, e.g. "Sponsor", "Site", "CRO".
        LocationOID (str): OID of the organization's Location.
        PartOfOrganizationOID (str): OID of a parent Organization.
        Description: Optional description.
        Address (list): One or more postal addresses.
        Telecom (list): One or more contact points.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Role = T.String()
    Type = T.ValueSetString(required=True)
    LocationOID = T.OIDRef()
    PartOfOrganizationOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)
    Address = T.ODMListObject(element_class=Address)
    Telecom = T.ODMListObject(element_class=Telecom)


class User(OE.ODMElement):
    """A user (person) who can be referenced in an ODM administrative context.

    User records appear in the AdminData section and are referenced by
    AuditRecord and Signature elements within clinical data.

    .. versionchanged:: 0.2.1
       ``Prefix`` and ``Suffix`` became child elements, matching the XSD;
       they were modelled as attributes. ``DisplayName`` was removed -- it
       is not part of the ODM 2.0 XSD.

    Attributes:
        OID (str, required): Unique identifier.
        UserType (str): Role category of the user, e.g. "Sponsor",
            "Investigator", "Lab", "Other".
        OrganizationOID (str): OID of the Organization the user belongs to.
        LocationOID (str): OID of the user's Location.
        UserName: The user's login name.
        Prefix: Honorific preceding the name.
        Suffix: Qualifier following the name.
        FullName: Full legal name.
        GivenName: Given (first) name.
        FamilyName: Family (last) name.
        Image: Picture of the user.
        Address (list): One or more postal addresses.
        Telecom (list): One or more contact points.
    """

    OID = T.OID(required=True)
    UserType = T.ValueSetString()
    OrganizationOID = T.OIDRef()
    LocationOID = T.OIDRef()
    UserName = T.ODMObject(element_class=UserName)
    Prefix = T.ODMObject(element_class=Prefix)
    Suffix = T.ODMObject(element_class=Suffix)
    FullName = T.ODMObject(element_class=FullName)
    GivenName = T.ODMObject(element_class=GivenName)
    FamilyName = T.ODMObject(element_class=FamilyName)
    Image = T.ODMObject(element_class=Image)
    Address = T.ODMListObject(element_class=Address)
    Telecom = T.ODMListObject(element_class=Telecom)


class MetaDataVersionRef(OE.ODMElement):
    """Associates a Location with a specific MetaDataVersion and its effective date.

    Attributes:
        StudyOID (str, required): OID reference to the Study whose metadata
            is referenced.
        MetaDataVersionOID (str, required): OID reference to the
            MetaDataVersion.
        EffectiveDate (str, required): ISO 8601 date from which this metadata
            version became effective at the location.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    EffectiveDate = T.DateString(required=True)


class Location(OE.ODMElement):
    """Defines a physical or logical location (e.g. a site) in the administrative data.

    Attributes:
        OID (str, required): Unique identifier.
        Name (str, required): Human-readable name of the location.
        LocationType (str): Category of location, e.g. "Sponsor", "Site",
            "CRO", "Lab".
        MetaDataVersionRef (list, required): One or more references to the
            metadata versions effective at this location.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Role = T.String(required=False)
    OrganizationOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)
    MetaDataVersionRef = T.ODMListObject(required=True, element_class=MetaDataVersionRef)
    Address = T.ODMListObject(element_class=Address)
    Telecom = T.ODMListObject(element_class=Telecom)


class Meaning(OE.ODMElement):
    """A human-readable description of the meaning of an electronic signature.

    Attributes:
        _content (str, required): Text describing what the signature signifies,
            e.g. "Approval" or "Author".
    """

    _content = T.String(required=True)


class LegalReason(OE.ODMElement):
    """The legal basis or reason for an electronic signature.

    Attributes:
        _content (str, required): Text describing the legal reason for the
            signature, e.g. "I approve this document".
    """

    _content = T.String(required=True)


class SignatureDef(OE.ODMElement):
    """Defines the type and meaning of an electronic signature in an ODM document.

    Attributes:
        OID (str, required): Unique identifier.
        Methodology (str): The methodology used (e.g. "Electronic" or
            "Digital").
        Meaning (required): Human-readable meaning of the signature.
        LegalReason (required): Legal reason text presented to the signer.
    """

    OID = T.OID(required=True)
    Methodology = T.ValueSetString()
    Meaning = T.ODMObject(required=True, element_class=Meaning)
    LegalReason = T.ODMObject(required=True, element_class=LegalReason)


class AdminData(OE.ODMElement):
    """Administrative data for a study, including users, locations, and signatures.

    Attributes:
        StudyOID (str): OID reference to the Study this admin data belongs to.
        User (list): User (person) records.
        Organization (list): Organization records.
        Location (list): Location (site) records.
        SignatureDef (list): Signature definition records.
    """

    StudyOID = T.OIDRef()
    User = T.ODMListObject(element_class=User)
    Organization = T.ODMListObject(element_class=Organization)
    Location = T.ODMListObject(element_class=Location)
    SignatureDef = T.ODMListObject(element_class=SignatureDef)


class Study(OE.ODMElement):
    """The root study element in an ODM 2.0 document.

    In ODM 2.0, StudyName and ProtocolName are scalar string attributes on
    Study itself rather than child elements, making the structure flatter
    than ODM 1.3.2.

    Attributes:
        OID (str, required): Unique identifier for the study.
        StudyName (str, required): Short name of the study.
        ProtocolName (str, required): Name of the protocol governing the study.
        Description: Optional human-readable description.
        MetaDataVersion (list): One or more versioned metadata snapshots.
    """

    OID = T.OID(required=True)
    StudyName = T.Name(required=True)
    ProtocolName = T.Name(required=True)
    VersionID = T.Name(required=False)
    VersionName = T.Name(required=False)
    Status = T.Name(required=False)
    Description = T.ODMObject(required=False, element_class=Description)
    MetaDataVersion = T.ODMListObject(required=True, element_class=MetaDataVersion)


class ODM(OE.ODMElement):
    """The root element of an ODM 2.0 document.

    The ODM element carries file-level metadata (file type, creation time,
    originating system) and contains the Study elements that hold all
    study data and metadata. Uses namespace
    ``http://www.cdisc.org/ns/odm/v2.0``.

    Attributes:
        Description (str): A human-readable description of the file.
        FileType (str, required): "Snapshot" for a complete file or
            "Transactional" for an incremental update.
        Granularity (str): Level of data included, e.g. "All", "Metadata",
            "AdminData", "ReferenceData", "AllClinicalData".
        FileOID (str, required): A globally unique OID for this specific file.
        CreationDateTime (str, required): ISO 8601 datetime when the file
            was created.
        PriorFileOID (str): OID of the preceding file in a sequence.
        AsOfDateTime (str): ISO 8601 datetime indicating the currency of
            the data.
        ODMVersion (str): Version of the ODM standard, e.g. "2.0".
        Originator (str): Name of the organization that created the file.
        SourceSystem (str): Name of the software system that generated the
            file.
        SourceSystemVersion (str): Version of the source system.
        Description (Description): Human-readable description of the file.
        Study (list): One or more Study elements.
        AdminData: Administrative data for the study.
    """
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    Context = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    PriorFileOID = T.OIDRef(required=False)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    Description = T.ODMObject(required=False, element_class=Description)
    Study = T.ODMListObject(required=False, element_class=Study)
    AdminData = T.ODMListObject(required=False, element_class=AdminData)
    # ReferenceData = T.ODMListObject(element_class=ReferenceData)
    # ClinicalData = T.ODMListObject(element_class=ClinicalData)
    # Association = T.ODMListObject(element_class=Association)
