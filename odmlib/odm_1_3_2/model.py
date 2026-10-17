import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    """A text string associated with a specific language.

    Used throughout ODM to provide human-readable labels and descriptions
    that may be localized into multiple languages.

    Attributes:
        lang (str): The ISO 639-1 language code (e.g., "en", "de"), carried
            in the xml:lang XML attribute.
        _content (str, required): The translated text content.
    """

    lang = T.String(namespace="xml")
    _content = T.String(required=True)


class Alias(OE.ODMElement):
    """An alternative name for an ODM element in an external context.

    Aliases allow ODM elements to be identified by names used in external
    systems or coding dictionaries (e.g., CDASH, CDISC Controlled Terminology).

    Attributes:
        Context (str, required): The naming context or external system
            (e.g., "CDASH", "CDISC/NCI").
        Name (str, required): The name of the element in that context.
    """

    Context = T.String(required=True)
    Name = T.String(required=True)


class StudyDescription(OE.ODMElement):
    """A textual description of the clinical study.

    Attributes:
        _content (str, required): The study description text.
    """

    _content = T.String(required=True)


class ProtocolName(OE.ODMElement):
    """The name of the study protocol.

    Attributes:
        _content (str, required): The protocol name text.
    """

    _content = T.String(required=True)


class StudyName(OE.ODMElement):
    """The name of the clinical study.

    Attributes:
        _content (str, required): The study name text.
    """

    _content = T.String(required=True)


class GlobalVariables(OE.ODMElement):
    """Container for global study identification variables.

    Holds the three required elements that identify a clinical study within
    an ODM document.

    Attributes:
        StudyName: The name of the study.
        StudyDescription: A textual description of the study.
        ProtocolName: The name of the study protocol.
    """

    StudyName = T.ODMObject(element_class=StudyName)
    StudyDescription = T.ODMObject(element_class=StudyDescription)
    ProtocolName = T.ODMObject(element_class=ProtocolName)


class Symbol(OE.ODMElement):
    """A human-readable symbol or label for a measurement unit.

    Contains one or more TranslatedText elements to support multiple
    languages.

    Attributes:
        TranslatedText (list, required): One or more translated text
            representations of the symbol.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class MeasurementUnit(OE.ODMElement):
    """Defines a unit of measurement used in the study.

    Measurement units are defined in BasicDefinitions and referenced by
    ItemDef and ItemData elements to indicate the unit of a collected value.

    Attributes:
        OID (str, required): Unique identifier for this measurement unit.
        Name (str, required): The name of the measurement unit (e.g., "kg").
        Symbol (Symbol, required): The human-readable symbol for the unit,
            with optional translations.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    # the XSD types MeasurementUnit/@Name as free text, not name, so "" is valid
    Name = T.String(required=True)
    Symbol = T.ODMObject(required=True, element_class=Symbol)
    Alias = T.ODMListObject(element_class=Alias)


class BasicDefinitions(OE.ODMElement):
    """Container for basic definitions shared across the ODM document.

    Currently holds MeasurementUnit definitions that can be referenced
    throughout the study metadata.

    Attributes:
        MeasurementUnit (list): List of MeasurementUnit definitions.
    """

    MeasurementUnit = T.ODMListObject(element_class=MeasurementUnit)


class Include(OE.ODMElement):
    """A reference to another MetaDataVersion to be included.

    Allows a MetaDataVersion to incorporate all definitions from a
    previously defined MetaDataVersion in the same or another study.

    Attributes:
        StudyOID (str, required): OID of the study containing the
            MetaDataVersion to include.
        MetaDataVersionOID (str, required): OID of the MetaDataVersion
            to include.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)


class Description(OE.ODMElement):
    """A human-readable description of an ODM element.

    Contains one or more TranslatedText elements to provide descriptions
    in multiple languages.

    Attributes:
        TranslatedText (list, required): One or more translated descriptions.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class StudyEventRef(OE.ODMElement):
    """A reference to a StudyEventDef within a Protocol.

    Defines the inclusion of a study event (visit) in the study protocol,
    along with its ordering and whether collection is mandatory.

    Attributes:
        StudyEventOID (str, required): OID of the referenced StudyEventDef.
        OrderNumber (int): Optional display order of the event in the protocol.
        Mandatory (str, required): "Yes" if collection of this event is
            required, "No" otherwise.
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, indicates this event should be skipped.
    """

    StudyEventOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class Protocol(OE.ODMElement):
    """The study protocol defining the sequence of study events.

    Contains references to all StudyEventDef elements in the order they
    occur in the clinical trial protocol.

    Attributes:
        Description: Optional Description element with TranslatedText.
        StudyEventRef (list): Ordered list of StudyEventRef elements
            defining the protocol structure.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    Description = T.ODMObject(element_class=Description)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)
    Alias = T.ODMListObject(element_class=Alias)


class FormRef(OE.ODMElement):
    """A reference to a FormDef within a StudyEventDef.

    Defines which CRF forms are collected at a study event and in what order.

    Attributes:
        FormOID (str, required): OID of the referenced FormDef.
        OrderNumber (int): Optional display order of the form within
            the study event.
        Mandatory (str, required): "Yes" if collection of this form is
            required, "No" otherwise.
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, indicates this form should be skipped.
    """

    FormOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class StudyEventDef(OE.ODMElement):
    """Defines a study event (visit or encounter) within a MetaDataVersion.

    A StudyEventDef describes a scheduled or unscheduled visit at which
    one or more CRF forms are collected. It contains FormRef elements
    listing which forms are collected at this event.

    Supports iteration over its FormRef elements.

    Attributes:
        OID (str, required): Unique identifier for this study event.
        Name (str, required): Human-readable name of the study event
            (e.g., "Screening", "Week 4").
        Repeating (str, required): "Yes" if the event can occur multiple
            times, "No" otherwise.
        Type (str, required): Event type (e.g., "Scheduled",
            "Unscheduled", "Common").
        Category (str): Optional category grouping for the event.
        Description: Optional Description element with TranslatedText.
        FormRef (list): List of FormRef elements indicating which forms
            are collected at this event.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Type = T.ValueSetString(required=True)
    Category = T.String(required=False)
    Description = T.ODMObject(element_class=Description)
    FormRef = T.ODMListObject(element_class=FormRef)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        """ returns the number of FormRefs in an StudyEventDef object as the length """
        return len(self.FormRef)

    def __getitem__(self, position):
        """ creates an iterator from an StudyEventDef object that returns the FormRef in position """
        return self.FormRef[position]

    def __iter__(self):
        return iter(self.FormRef)


class ItemGroupRef(OE.ODMElement):
    """A reference to an ItemGroupDef within a FormDef.

    Defines which item groups (datasets) are included on a CRF form
    and in what order.

    Attributes:
        ItemGroupOID (str, required): OID of the referenced ItemGroupDef.
        OrderNumber (int): Optional display order of the item group
            within the form.
        Mandatory (str, required): "Yes" if collection of this item group
            is required, "No" otherwise.
        CollectionExceptionConditionOID (str): OID of a ConditionDef that,
            when true, indicates this item group should be skipped.
    """

    ItemGroupOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class ArchiveLayout(OE.ODMElement):
    """Defines a PDF layout for archiving a form.

    Associates a PDF file with a FormDef for archival purposes.

    Attributes:
        OID (str, required): Unique identifier for this archive layout.
        PdfFileName (str, required): The filename of the PDF file.
        PresentationOID (str): Optional OID of a Presentation element
            that defines the rendering of the PDF.
    """

    OID = T.OID(required=True)
    PdfFileName = T.FileName(required=True)
    PresentationOID = T.OIDRef(required=False)


class FormDef(OE.ODMElement):
    """Defines a CRF form within a MetaDataVersion.

    A FormDef describes the structure of a case report form. It contains
    ItemGroupRef elements that reference the item groups (datasets) collected
    on this form.

    Supports iteration over its ItemGroupRef elements.

    Attributes:
        OID (str, required): Unique identifier for this form.
        Name (str, required): Human-readable name of the form.
        Repeating (str, required): "Yes" if the form can be collected
            multiple times at a single event, "No" otherwise.
        Description: Optional Description element with TranslatedText.
        ItemGroupRef (list): List of ItemGroupRef elements indicating
            which item groups are on this form.
        ArchiveLayout (list): Optional list of ArchiveLayout elements
            for PDF archival.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    ArchiveLayout = T.ODMListObject(element_class=ArchiveLayout)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        return len(self.ItemGroupRef)

    def __getitem__(self, position):
        return self.ItemGroupRef[position]

    def __iter__(self):
        return iter(self.ItemGroupRef)


class ItemRef(OE.ODMElement):
    """A reference to an ItemDef within an ItemGroupDef.

    Defines which individual data items are included in a dataset (item group)
    and their collection properties.

    Attributes:
        ItemOID (str, required): OID of the referenced ItemDef.
        OrderNumber (int): Optional display order of the item within the
            item group.
        Mandatory (str, required): "Yes" if collection of this item is
            required, "No" otherwise.
        KeySequence (int): Optional key sequence number if this item is
            part of the dataset key.
        MethodOID (str): Optional OID of a MethodDef defining how this
            item's value is computed.
        Role (str): Optional role of this item (e.g., "Topic").
        RoleCodeListOID (str): Optional OID of the CodeList defining
            valid roles.
        CollectionExceptionConditionOID (str): Optional OID of a
            ConditionDef that, when true, indicates this item should
            be skipped.
    """

    ItemOID = T.String(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    KeySequence = T.Integer(required=False)
    MethodOID = T.String(required=False)
    Role = T.String()
    RoleCodeListOID = T.String()
    CollectionExceptionConditionOID = T.String()


class ItemGroupDef(OE.ODMElement):
    """Defines an item group (dataset or domain) within a MetaDataVersion.

    An ItemGroupDef describes the structure of a tabular dataset. In SDTM
    and ADaM submissions, each ItemGroupDef typically corresponds to one
    dataset (e.g., DM, AE, LB). It contains ItemRef elements that reference
    the individual variable definitions.

    Supports iteration over its ItemRef elements.

    Attributes:
        OID (str, required): Unique identifier for this item group.
        Name (str, required): Human-readable name (often the domain name,
            e.g., "DM", "AE").
        Repeating (str, required): "Yes" if the dataset can have multiple
            records per subject, "No" for single-record datasets.
        IsReferenceData (str): "Yes" if this group contains reference data
            (e.g., coding dictionaries) rather than subject data.
        SASDatasetName (str): Optional SAS dataset name (max 8 characters).
        Domain (str): Optional CDISC domain abbreviation (e.g., "DM").
        Origin (str): Optional description of where data originates.
        Purpose (str): Optional description of the dataset's purpose.
        Comment (str): Optional comment text.
        Description: Optional Description element with TranslatedText.
        ItemRef (list): List of ItemRef elements referencing the variable
            definitions included in this dataset.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    IsReferenceData = T.ValueSetString(required=False)
    SASDatasetName = T.SASName()
    Domain = T.String()
    Origin = T.String()
    Purpose = T.String()
    Comment = T.String()
    Description = T.ODMObject(element_class=Description)
    ItemRef = T.ODMListObject(element_class=ItemRef)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class Question(OE.ODMElement):
    """The question text presented to a data entry operator for an item.

    Contains one or more TranslatedText elements so the question can be
    displayed in multiple languages.

    Attributes:
        TranslatedText (list, required): One or more translated question
            texts.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class ExternalQuestion(OE.ODMElement):
    """A reference to a question defined in an external dictionary.

    Identifies an item's question by its code in an external coding system
    such as a questionnaire library.

    Attributes:
        Dictionary (str): The name of the external dictionary or library.
        Version (str): The version of the external dictionary.
        Code (str): The code identifying the question within the dictionary.
    """

    Dictionary = T.String(required=False)
    Version = T.String(required=False)
    Code = T.String(required=False)


class MeasurementUnitRef(OE.ODMElement):
    """A reference to a MeasurementUnit defined in BasicDefinitions.

    Used within ItemDef and ItemData to associate a unit of measurement
    with a collected value.

    Attributes:
        MeasurementUnitOID (str, required): OID of the referenced
            MeasurementUnit.
    """

    MeasurementUnitOID = T.String(required=True)


class CheckValue(OE.ODMElement):
    """A single value used in a range check comparison.

    Provides the threshold or boundary value for a RangeCheck comparator
    (e.g., the "18" in "age >= 18").

    Attributes:
        _content (str, required): The check value as a string.
    """

    _content = T.String(required=True)


class FormalExpression(OE.ODMElement):
    """A formal computational expression in a specified language or context.

    Used within MethodDef and ConditionDef to express algorithms and
    conditions in a machine-readable form (e.g., SAS, R, or custom syntax).

    Attributes:
        Context (str, required): The language or context of the expression
            (e.g., "SAS", "R", "xpath").
        _content (str, required): The expression text.
    """

    Context = T.String(required=True)
    _content = T.String(required=True)


class ErrorMessage(OE.ODMElement):
    """An error message displayed when a RangeCheck fails.

    Contains one or more TranslatedText elements so the error message can
    be shown in multiple languages.

    Attributes:
        TranslatedText (list, required): One or more translated error
            message texts.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class RangeCheck(OE.ODMElement):
    """A validity check defining acceptable value ranges for an item.

    Specifies constraints on item values using comparators and check values
    or formal expressions. Can generate soft (warning) or hard (error)
    violations.

    Attributes:
        Comparator (str): The comparison operator (e.g., "LT", "LE",
            "GT", "GE", "EQ", "NE", "IN", "NOTIN").
        SoftHard (str, required): "Soft" for a warning, "Hard" for an
            error when the check fails.
        CheckValue (list): List of CheckValue elements providing the
            boundary values.
        FormalExpression (list): List of FormalExpression elements for
            complex range expressions.
        MeasurementUnitRef: Optional reference to a MeasurementUnit
            for the check values.
        ErrorMessage: Optional message to display when the check fails.
    """

    Comparator = T.ValueSetString(required=False)
    SoftHard = T.ValueSetString(required=True)
    CheckValue = T.ODMListObject(element_class=CheckValue)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    MeasurementUnitRef = T.ODMObject(element_class=MeasurementUnitRef)
    ErrorMessage = T.ODMObject(element_class=ErrorMessage)


class CodeListRef(OE.ODMElement):
    """A reference to a CodeList within an ItemDef.

    Links an ItemDef to the CodeList that defines the permitted coded
    values for that item.

    Attributes:
        CodeListOID (str, required): OID of the referenced CodeList.
    """

    CodeListOID = T.OIDRef(required=True)


class ItemDef(OE.ODMElement):
    """Defines an individual data item (variable) within a MetaDataVersion.

    An ItemDef describes a single CRF question or dataset variable,
    including its data type, length, valid value range, and coded value
    list. In SDTM/ADaM contexts, each ItemDef corresponds to one dataset
    variable (column).

    Attributes:
        OID (str, required): Unique identifier for this item.
        Name (str, required): The variable name (e.g., "AGE", "SEX").
        DataType (str, required): The data type (e.g., "text", "integer",
            "float", "date", "datetime", "time", "boolean").
        Length (int): Maximum length of the value (for text types).
        SignificantDigits (int): Number of significant digits (for numeric
            types).
        SASFieldName (str): Optional SAS variable name (max 8 characters).
        SDSVarName (str): Optional CDISC Submission Dataset variable name.
        Origin (str): Optional description of where the value originates.
        Comment (str): Optional comment text.
        Description: Optional Description element with TranslatedText.
        Question: Optional question text presented to data entry operators.
        ExternalQuestion: Optional reference to a question in an external
            dictionary.
        MeasurementUnitRef (list): Optional list of units of measure.
        RangeCheck (list): Optional list of validity range checks.
        CodeListRef: Optional reference to the CodeList of permitted values.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    Length = T.PositiveInteger()
    SignificantDigits = T.NonNegativeInteger()
    SASFieldName = T.SASName()
    SDSVarName = T.SASName()
    Origin = T.String()
    Comment = T.String()
    Description = T.ODMObject(element_class=Description)
    Question = T.ODMObject(element_class=Question)
    ExternalQuestion = T.ODMObject(element_class=ExternalQuestion)
    MeasurementUnitRef = T.ODMListObject(element_class=MeasurementUnitRef)
    RangeCheck = T.ODMListObject(element_class=RangeCheck)
    CodeListRef = T.ODMObject(element_class=CodeListRef)
    Alias = T.ODMListObject(element_class=Alias)


class Decode(OE.ODMElement):
    """The human-readable label for a coded value in a CodeListItem.

    Contains one or more TranslatedText elements so the label can be
    displayed in multiple languages.

    Attributes:
        TranslatedText (list, required): One or more translated decode
            labels for the coded value.
    """

    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListItem(OE.ODMElement):
    """A single coded value with its human-readable label in a CodeList.

    Represents one enumerated value in a CodeList that has associated
    decode text. Used for items where the submitted value differs from
    or is supplemented by a descriptive label.

    Attributes:
        CodedValue (str, required): The actual coded value submitted in
            the dataset.
        Rank (float): Optional numeric rank for ordering.
        OrderNumber (int): Optional display order within the CodeList.
        Decode: The human-readable label for this coded value.
        Alias (list): Optional list of Alias elements mapping this value
            to external terminologies (e.g., NCI thesaurus codes).
    """

    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    OrderNumber = T.Integer(required=False)
    Decode = T.ODMObject(element_class=Decode)
    Alias = T.ODMListObject(element_class=Alias)


class EnumeratedItem(OE.ODMElement):
    """A single enumerated value in a CodeList without a separate decode label.

    Represents one permitted value in a CodeList where the coded value
    itself is self-describing and no separate decode text is needed.

    Attributes:
        CodedValue (str, required): The enumerated value.
        Rank (float): Optional numeric rank for ordering.
        OrderNumber (int): Optional display order within the CodeList.
        Alias (list): Optional list of Alias elements mapping this value
            to external terminologies.
    """

    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    OrderNumber = T.Integer(required=False)
    Alias = T.ODMListObject(element_class=Alias)


class ExternalCodeList(OE.ODMElement):
    """A reference to a code list defined in an external dictionary.

    Used when permitted values for an item are defined by an external
    coding system (e.g., MedDRA, WHO Drug Dictionary) rather than inline
    in the ODM document.

    Attributes:
        Dictionary (str): The name of the external dictionary or
            coding system.
        Version (str): The version of the external dictionary.
        ref (str): An optional reference identifier within the dictionary.
        href (str): An optional URL or path to the external code list.
    """

    Dictionary = T.String(required=False)
    Version = T.String(required=False)
    ref = T.String(required=False)
    href = T.String(required=False)


class CodeList(OE.ODMElement):
    """Defines a list of permitted coded values for an item.

    A CodeList contains either CodeListItem elements (with decode labels)
    or EnumeratedItem elements (value only), or a reference to an external
    code list. CodeLists are referenced by ItemDef elements via CodeListRef.

    Attributes:
        OID (str, required): Unique identifier for this code list.
        Name (str, required): Human-readable name of the code list.
        DataType (str, required): The data type of coded values
            (e.g., "text", "integer", "float").
        SASFormatName (str): Optional SAS format name associated with
            this code list.
        Description: Optional Description element with TranslatedText.
        CodeListItem (list): List of coded value items with decode labels.
        EnumeratedItem (list): List of enumerated values without separate
            decode labels.
        ExternalCodeList: Optional reference to an external code list.
        Alias (list): Optional list of Alias elements for external mappings
            (e.g., NCI code list OIDs).
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    SASFormatName = T.SASFormat()
    Description = T.ODMObject(element_class=Description)
    CodeListItem = T.ODMListObject(element_class=CodeListItem)
    EnumeratedItem = T.ODMListObject(element_class=EnumeratedItem)
    ExternalCodeList = T.ODMObject(element_class=ExternalCodeList)
    Alias = T.ODMListObject(element_class=Alias)


class Presentation(OE.ODMElement):
    """A presentation definition for a form layout or style sheet.

    Stores presentation or formatting content (e.g., XSL, HTML) that
    controls how a form is displayed or rendered for archival purposes.

    Attributes:
        OID (str, required): Unique identifier for this presentation.
        lang (str): Optional language code for the presentation content.
        _content (str): The presentation content (e.g., stylesheet text).
    """

    OID = T.OID(required=True)
    lang = T.String(required=False)
    _content = T.String()


class ConditionDef(OE.ODMElement):
    """Defines a logical condition used for skip logic and collection exceptions.

    A ConditionDef encodes a logical expression that can be evaluated at
    runtime to determine whether a StudyEventRef, FormRef, ItemGroupRef,
    or ItemRef should be skipped (not collected).

    Attributes:
        OID (str, required): Unique identifier for this condition.
        Name (str, required): Human-readable name of the condition.
        Description: Optional Description element with TranslatedText.
        FormalExpression (list): List of formal expressions encoding
            the condition logic in one or more languages.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class MethodDef(OE.ODMElement):
    """Defines a computational method or derivation algorithm for an item.

    A MethodDef encodes the algorithm by which a derived or computed item
    value is calculated. It is referenced by ItemRef elements via the
    MethodOID attribute.

    Attributes:
        OID (str, required): Unique identifier for this method.
        Name (str, required): Human-readable name of the method.
        Type (str, required): The method type (e.g., "Computation",
            "Imputation", "Transpose", "Other").
        Description (Description, required): Description element with
            TranslatedText explaining the method.
        FormalExpression (list): List of formal expressions encoding
            the algorithm in one or more languages.
        Alias (list): Optional list of Alias elements for external mappings.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class MetaDataVersion(OE.ODMElement):
    """A complete set of metadata for a clinical study at a point in time.

    MetaDataVersion is the central container for all study metadata,
    including the Protocol, study event definitions, form definitions,
    item group definitions, item definitions, code lists, methods, and
    conditions. A Study can have multiple MetaDataVersions representing
    amendments to the protocol.

    Attributes:
        OID (str, required): Unique identifier for this metadata version.
        Name (str, required): Human-readable name (e.g., "v1.0", "Amendment 1").
        Description (str): Optional textual description of this version.
        Include: Optional Include element referencing a prior
            MetaDataVersion whose definitions are inherited.
        Protocol: The Protocol element defining the study event sequence.
        StudyEventDef (list): List of StudyEventDef elements.
        FormDef (list): List of FormDef elements.
        ItemGroupDef (list): List of ItemGroupDef elements.
        ItemDef (list): List of ItemDef elements.
        CodeList (list): List of CodeList elements.
        Presentation (list): List of Presentation elements.
        ConditionDef (list): List of ConditionDef elements for skip logic.
        MethodDef (list): List of MethodDef elements for derivations.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.String(required=False)
    Include = T.ODMObject(element_class=Include)
    Protocol = T.ODMObject(element_class=Protocol)
    StudyEventDef = T.ODMListObject(element_class=StudyEventDef)
    FormDef = T.ODMListObject(element_class=FormDef)
    ItemGroupDef = T.ODMListObject(element_class=ItemGroupDef)
    ItemDef = T.ODMListObject(element_class=ItemDef)
    CodeList = T.ODMListObject(element_class=CodeList)
    Presentation = T.ODMListObject(element_class=Presentation)
    ConditionDef = T.ODMListObject(element_class=ConditionDef)
    MethodDef = T.ODMListObject(element_class=MethodDef)


class LoginName(OE.ODMElement):
    """The login username for a User.

    Attributes:
        _content (str, required): The login name text.
    """

    _content = T.String(required=True)


class DisplayName(OE.ODMElement):
    """A short display name for a User.

    Attributes:
        _content (str, required): The display name text.
    """

    _content = T.String(required=True)


class FullName(OE.ODMElement):
    """The full legal name of a User.

    Attributes:
        _content (str, required): The full name text.
    """

    _content = T.String(required=True)


class FirstName(OE.ODMElement):
    """The first (given) name of a User.

    Attributes:
        _content (str, required): The first name text.
    """

    _content = T.String(required=True)


class LastName(OE.ODMElement):
    """The last (family) name of a User.

    Attributes:
        _content (str, required): The last name text.
    """

    _content = T.String(required=True)


class Organization(OE.ODMElement):
    """The organization or institution a User is affiliated with.

    Attributes:
        _content (str, required): The organization name text.
    """

    _content = T.String(required=True)


class StreetName(OE.ODMElement):
    """A street address line in a User's address.

    Attributes:
        _content (str, required): The street address line text.
    """

    _content = T.String(required=True)


class City(OE.ODMElement):
    """The city component of a User's address.

    Attributes:
        _content (str, required): The city name text.
    """

    _content = T.String(required=True)


class StateProv(OE.ODMElement):
    """The state or province component of a User's address.

    Attributes:
        _content (str, required): The state or province name text.
    """

    _content = T.String(required=True)


class Country(OE.ODMElement):
    """The country component of a User's address.

    Stored as an ISO 3166-1 alpha-2 country code.

    Attributes:
        _content (str, required): The two-letter ISO country code
            (e.g., "US", "DE").
    """

    _content = T.ValueSetString(required=True)


class PostalCode(OE.ODMElement):
    """The postal or ZIP code component of a User's address.

    Attributes:
        _content (str, required): The postal code text.
    """

    _content = T.String(required=True)


class OtherText(OE.ODMElement):
    """Additional unstructured address text for a User's address.

    Used for address information that does not fit into the other
    structured address fields.

    Attributes:
        _content (str, required): The additional address text.
    """

    _content = T.String(required=True)


class Address(OE.ODMElement):
    """The postal address of a User.

    Groups the structured address components for a user record.

    Attributes:
        StreetName (list): List of street address lines.
        City: The city.
        StateProv: The state or province.
        Country: The country (ISO 3166-1 alpha-2 code).
        PostalCode: The postal or ZIP code.
        OtherText: Any additional unstructured address information.
    """

    StreetName = T.ODMListObject(element_class=StreetName)
    City = T.ODMObject(element_class=City)
    StateProv = T.ODMObject(element_class=StateProv)
    Country = T.ODMObject(element_class=Country)
    PostalCode = T.ODMObject(element_class=PostalCode)
    OtherText = T.ODMObject(element_class=OtherText)


class Email(OE.ODMElement):
    """An email address for a User.

    Attributes:
        _content (str, required): The email address, validated as a
            properly formatted email string.
    """

    _content = T.Email(required=True)


class Picture(OE.ODMElement):
    """A reference to a picture file for a User.

    Attributes:
        PictureFileName (str, required): The filename of the picture file.
        ImageType (str): Optional image type or format (e.g., "JPEG", "PNG").
    """

    PictureFileName = T.FileName(required=True)
    ImageType = T.Name()


class Pager(OE.ODMElement):
    """A pager contact number for a User.

    Attributes:
        _content (str, required): The pager number text.
    """

    _content = T.String(required=True)


class Fax(OE.ODMElement):
    """A fax number for a User.

    Attributes:
        _content (str, required): The fax number text.
    """

    _content = T.String(required=True)


class Phone(OE.ODMElement):
    """A phone number for a User.

    Attributes:
        _content (str, required): The phone number text.
    """

    _content = T.String(required=True)


class LocationRef(OE.ODMElement):
    """A reference to a Location defined in AdminData.

    Used to associate a User or AuditRecord with the site or location
    where they operate.

    Attributes:
        LocationOID (str, required): OID of the referenced Location.
    """

    LocationOID = T.OIDRef(required=True)


class Certificate(OE.ODMElement):
    """A digital certificate associated with a User for signature purposes.

    Attributes:
        _content (str, required): The certificate data (typically
            base64-encoded certificate content).
    """

    _content = T.String(required=True)


class User(OE.ODMElement):
    """Defines a system user involved in the clinical trial.

    User records in AdminData identify personnel (investigators, data
    managers, monitors, etc.) who interact with the study data. User
    records are referenced in AuditRecord and Signature elements.

    Attributes:
        OID (str, required): Unique identifier for this user.
        UserType (str): The type of user (e.g., "Investigator",
            "Sponsor", "Laboratory", "Other").
        LoginName: The login username.
        DisplayName: A short display name.
        FullName: The full legal name.
        FirstName: The given name.
        LastName: The family name.
        Organization: The affiliated organization.
        Address (list): List of postal addresses.
        Email (list): List of email addresses.
        Pager: Optional pager number.
        Fax (list): List of fax numbers.
        Phone (list): List of phone numbers.
        LocationRef (list): List of location references indicating sites
            where the user operates.
        Certificate (list): List of digital certificates.
    """

    OID = T.OID(required=True)
    UserType = T.ValueSetString()
    LoginName = T.ODMObject(element_class=LoginName)
    DisplayName = T.ODMObject(element_class=DisplayName)
    FullName = T.ODMObject(element_class=FullName)
    FirstName = T.ODMObject(element_class=FirstName)
    LastName = T.ODMObject(element_class=LastName)
    Organization = T.ODMObject(element_class=Organization)
    Address = T.ODMListObject(element_class=Address)
    Email = T.ODMListObject(element_class=Email)
    Pager = T.ODMObject(element_class=Pager)
    Fax = T.ODMListObject(element_class=Fax)
    Phone = T.ODMListObject(element_class=Phone)
    LocationRef = T.ODMListObject(element_class=LocationRef)
    Certificate = T.ODMListObject(element_class=Certificate)


class MetaDataVersionRef(OE.ODMElement):
    """A reference to a specific MetaDataVersion with an effective date.

    Used within a Location to record which MetaDataVersion applies at
    that location and from what date.

    Attributes:
        StudyOID (str, required): OID of the study containing the
            referenced MetaDataVersion.
        MetaDataVersionOID (str, required): OID of the referenced
            MetaDataVersion.
        EffectiveDate (str, required): The date from which this
            MetaDataVersion is effective at the location (ISO 8601 date).
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    EffectiveDate = T.DateString(required=True)


class Location(OE.ODMElement):
    """Defines a site or location participating in the clinical trial.

    Location records in AdminData identify investigative sites and other
    locations involved in the study. They are referenced by LocationRef
    elements in User records and AuditRecord elements.

    Attributes:
        OID (str, required): Unique identifier for this location.
        Name (str, required): The name of the location or site.
        LocationType (str): The type of location (e.g., "Sponsor",
            "Site", "CRO", "Lab", "Other").
        MetaDataVersionRef (list, required): List of MetaDataVersionRef
            elements specifying which metadata versions apply at this
            location and from what effective date.
    """

    OID = T.OID(required=True)
    Name = T.Name(required=True)
    LocationType = T.ValueSetString()
    MetaDataVersionRef = T.ODMListObject(required=True, element_class=MetaDataVersionRef)


class Meaning(OE.ODMElement):
    """The meaning or purpose of a signature in human-readable text.

    Used within SignatureDef to describe what a signature represents
    (e.g., "Author", "Reviewer", "Approver").

    Attributes:
        _content (str, required): The meaning text.
    """

    _content = T.String(required=True)


class LegalReason(OE.ODMElement):
    """The legal reason or basis for a signature.

    Used within SignatureDef to record the regulatory or legal
    justification for requiring a signature.

    Attributes:
        _content (str, required): The legal reason text.
    """

    _content = T.String(required=True)


class SignatureDef(OE.ODMElement):
    """Defines a type of electronic signature used in the study.

    SignatureDef records describe the different roles or purposes for
    which electronic signatures are applied to data. Each Signature
    element in clinical data references a SignatureDef.

    Attributes:
        OID (str, required): Unique identifier for this signature definition.
        Methodology (str): The signature methodology (e.g., "Electronic",
            "Digital").
        Meaning (Meaning, required): Human-readable description of what
            the signature represents.
        LegalReason (LegalReason, required): The legal basis for the
            signature.
    """

    OID = T.OID(required=True)
    Methodology = T.ValueSetString()
    Meaning = T.ODMObject(required=True, element_class=Meaning)
    LegalReason = T.ODMObject(required=True, element_class=LegalReason)


class AdminData(OE.ODMElement):
    """Administrative data associated with a study or the entire ODM document.

    AdminData contains user records, site/location records, and signature
    definitions used to support audit trails and electronic signatures
    throughout the clinical data.

    Attributes:
        StudyOID (str): Optional OID of the study this admin data belongs
            to; if omitted, the data applies to all studies in the document.
        User (list): List of User records.
        Location (list): List of Location (site) records.
        SignatureDef (list): List of SignatureDef records.
    """

    StudyOID = T.OIDRef()
    User = T.ODMListObject(element_class=User)
    Location = T.ODMListObject(element_class=Location)
    SignatureDef = T.ODMListObject(element_class=SignatureDef)


class Study(OE.ODMElement):
    """Represents a single clinical study within an ODM document.

    A Study element contains the global variables that identify the study
    and one or more MetaDataVersion elements that define the study's
    data collection structure.

    Attributes:
        OID (str, required): Unique identifier for this study.
        GlobalVariables (GlobalVariables, required): The required study
            identification variables (name, description, protocol name).
        BasicDefinitions: Optional container for shared definitions such
            as measurement units.
        MetaDataVersion (list): List of MetaDataVersion elements, each
            representing the complete study metadata at a point in time.
    """

    OID = T.String(required=True)
    GlobalVariables = T.ODMObject(required=True, element_class=GlobalVariables)
    BasicDefinitions = T.ODMObject(element_class=BasicDefinitions)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class UserRef(OE.ODMElement):
    """A reference to a User defined in AdminData.

    Used within AuditRecord and Signature elements to identify the
    user who performed an action or applied a signature.

    Attributes:
        UserOID (str, required): OID of the referenced User.
    """

    UserOID = T.OIDRef(required=True)


class DateTimeStamp(OE.ODMElement):
    """A date and time stamp for an audit record or signature.

    Attributes:
        _content (str, required): The ISO 8601 date-time string recording
            when the action occurred.
    """

    _content = T.DateTimeString(required=True)


class ReasonForChange(OE.ODMElement):
    """A human-readable explanation for why data was changed.

    Recorded in AuditRecord elements when data is modified after initial
    entry, as required by 21 CFR Part 11 and similar regulations.

    Attributes:
        _content (str, required): The reason for change text.
    """

    _content = T.String(required=True)


class SourceID(OE.ODMElement):
    """An identifier linking an audit record to its source system record.

    Provides traceability from the ODM representation back to the originating
    record in the source data management system.

    Attributes:
        _content (str, required): The source system record identifier.
    """

    _content = T.String(required=True)


class AuditRecord(OE.ODMElement):
    """An audit trail record for a data creation or modification event.

    AuditRecord captures who made a change, where, when, and why, as
    required for regulatory compliance (21 CFR Part 11, ICH E6). It can
    appear on ItemData, ItemGroupData, FormData, StudyEventData, and
    SubjectData elements.

    Attributes:
        EditPoint (str): The stage of data processing when the edit
            occurred (e.g., "DataManagement", "DBAudit", "RegulatoryReview").
        UsedImputationMethod (str): "Yes" if a missing value imputation
            method was used.
        ID (str): Optional unique identifier for this audit record.
        UserRef (UserRef, required): Reference to the user who made
            the change.
        LocationRef (LocationRef, required): Reference to the site where
            the change was made.
        DateTimeStamp (DateTimeStamp, required): Date and time when the
            change was made.
        ReasonForChange: Optional explanation for why the data was changed.
        SourceID: Optional link to the source system record.
    """

    EditPoint = T.ValueSetString(required=False)
    UsedImputationMethod = T.ValueSetString(required=False)
    ID = T.ID(required=False)
    UserRef = T.ODMObject(required=True, element_class=UserRef)
    LocationRef = T.ODMObject(required=True, element_class=LocationRef)
    DateTimeStamp = T.ODMObject(required=True, element_class=DateTimeStamp)
    ReasonForChange = T.ODMObject(required=False, element_class=ReasonForChange)
    SourceID = T.ODMObject(required=False, element_class=SourceID)


class SignatureRef(OE.ODMElement):
    """A reference to a SignatureDef defined in AdminData.

    Links a Signature instance to its corresponding SignatureDef that
    describes the meaning and methodology of the signature.

    Attributes:
        SignatureOID (str, required): OID of the referenced SignatureDef.
    """

    SignatureOID = T.OIDRef(required=True)


class Signature(OE.ODMElement):
    """An electronic or digital signature applied to clinical data.

    Signature elements record that a specific user, at a specific location
    and time, applied a signature of a defined type to a piece of data.
    Signatures can appear on ItemData, ItemGroupData, FormData,
    StudyEventData, and SubjectData elements.

    Attributes:
        ID (str, required): Unique identifier for this signature instance.
        UserRef (UserRef, required): Reference to the user who signed.
        LocationRef (LocationRef, required): Reference to the location
            where the signature was applied.
        SignatureRef (SignatureRef, required): Reference to the SignatureDef
            defining the type and meaning of this signature.
        DateTimeStamp (DateTimeStamp, required): Date and time when the
            signature was applied.
    """

    ID = T.ID(required=True)
    UserRef = T.ODMObject(required=True, element_class=UserRef)
    LocationRef = T.ODMObject(required=True, element_class=LocationRef)
    SignatureRef = T.ODMObject(required=True, element_class=SignatureRef)
    DateTimeStamp = T.ODMObject(required=True, element_class=DateTimeStamp)


class InvestigatorRef(OE.ODMElement):
    """A reference to the investigator (User) responsible for a subject.

    Used within SubjectData to identify the principal investigator
    associated with the subject's data.

    Attributes:
        UserOID (str, required): OID of the referenced User who is
            the investigator.
    """

    UserOID = T.OIDRef(required=True)


class SiteRef(OE.ODMElement):
    """A reference to the site (Location) where a subject is enrolled.

    Used within SubjectData to identify the investigative site at which
    the subject participates in the study.

    Attributes:
        LocationOID (str, required): OID of the referenced Location
            that is the enrollment site.
    """

    LocationOID = T.OIDRef(required=True)


class FlagValue(OE.ODMElement):
    """The value of a data review flag from a defined code list.

    Contains the actual flag value (e.g., "Open", "Closed", "Resolved")
    drawn from the code list referenced by CodeListOID.

    Attributes:
        CodeListOID (str, required): OID of the CodeList that defines
            the permitted flag values.
        _content (str, required): The flag value, which must be a valid
            coded value from the referenced CodeList.
    """

    CodeListOID = T.OIDRef(required=True)
    _content = T.String(required=True)


class FlagType(OE.ODMElement):
    """The type or category of a data review flag.

    Identifies the kind of flag (e.g., "Query", "Comment", "Review")
    using a coded value from the referenced code list.

    Attributes:
        CodeListOID (str, required): OID of the CodeList that defines
            the permitted flag type values.
        _content (str, required): The flag type, which must be a valid
            coded value from the referenced CodeList.
    """

    CodeListOID = T.OIDRef(required=True)
    _content = T.String(required=True)


class Flag(OE.ODMElement):
    """A data review or quality flag attached to a data element.

    Flags are used in clinical data review workflows to mark items for
    attention (e.g., data queries, review status indicators).

    Attributes:
        FlagValue (FlagValue, required): The current value of the flag.
        FlagType: Optional type or category of the flag.
    """

    FlagValue = T.ODMObject(required=True, element_class=FlagValue)
    FlagType = T.ODMObject(element_class=FlagType)


class Comment(OE.ODMElement):
    """A textual comment attached to an Annotation.

    Records a free-text comment associated with an Annotation on
    clinical data, optionally tagged with whether it originates from
    the sponsor or the site.

    Attributes:
        SponsorOrSite (str): Indicates the origin of the comment;
            "Sponsor" or "Site".
        _content (str, required): The comment text.
    """

    SponsorOrSite = T.ValueSetString()
    _content = T.String(required=True)


class Annotation(OE.ODMElement):
    """An annotation attached to a clinical data element.

    Annotations associate review comments and data quality flags with
    specific data elements. They can appear on ItemData, ItemGroupData,
    FormData, StudyEventData, SubjectData, and at the ClinicalData level.

    Attributes:
        SeqNum (int, required): Sequence number uniquely identifying this
            annotation within its parent element.
        TransactionType (str): The transaction type for this annotation
            in an incremental transfer (e.g., "Insert", "Update",
            "Remove", "Upsert", "Context").
        ID (str): Optional unique identifier for this annotation.
        Comment: Optional free-text comment.
        Flag (list): List of Flag elements with review status indicators.
    """

    SeqNum = T.Integer(required=True)
    TransactionType = T.ValueSetString(required=False)
    ID = T.ID(required=False)
    Comment = T.ODMObject(required=False, element_class=Comment)
    Flag = T.ODMListObject(element_class=Flag)


class ItemData(OE.ODMElement):
    """The collected value for a single data item (variable) for a subject.

    ItemData stores the actual data value for one variable within an
    ItemGroupData record. It references the ItemDef that defines the
    variable's metadata.

    Attributes:
        ItemOID (str, required): OID of the ItemDef this value belongs to.
        TransactionType (str): The transaction type for incremental transfers
            (e.g., "Insert", "Update", "Remove", "Upsert", "Context").
        Value (str): The collected data value as a string. Null values
            are represented by setting IsNull to "Yes".
        IsNull (str): "Yes" if the value is explicitly null/missing.
        AuditRecord: Optional audit trail for this data value.
        Signature: Optional electronic signature for this data value.
        MeasurementUnitRef: Optional reference to the unit of measure
            for this value.
        Annotation (list): Optional list of review annotations.
    """

    ItemOID = T.OIDRef(required=True)
    TransactionType = T.ValueSetString(required=False)
    Value = T.String(required=False)
    IsNull = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    MeasurementUnitRef = T.ODMObject(required=False, element_class=MeasurementUnitRef)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)


class ItemGroupData(OE.ODMElement):
    """A single record within a dataset (item group) for a subject.

    ItemGroupData contains the ItemData values for one row in a dataset.
    For repeating item groups (e.g., lab results), multiple ItemGroupData
    elements appear within a FormData, distinguished by ItemGroupRepeatKey.

    Supports iteration over its ItemData elements.

    Attributes:
        ItemGroupOID (str, required): OID of the ItemGroupDef this record
            belongs to.
        ItemGroupRepeatKey (str): For repeating item groups, the key
            identifying this particular record.
        TransactionType (str): The transaction type for incremental
            transfers.
        AuditRecord: Optional audit trail for this record.
        Signature: Optional electronic signature for this record.
        ArchiveLayout: Optional archive layout reference.
        Annotation (list): Optional list of review annotations.
        ItemData (list): List of ItemData elements with the actual
            variable values.
    """

    ItemGroupOID = T.OIDRef(required=True)
    ItemGroupRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    ArchiveLayout = T.ODMObject(required=False, element_class=ArchiveLayout)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    ItemData = T.ODMListObject(required=False, element_class=ItemData)

    def __len__(self):
        return len(self.ItemData)

    def __getitem__(self, position):
        return self.ItemData[position]

    def __iter__(self):
        return iter(self.ItemData)


class FormData(OE.ODMElement):
    """Collected data for a single form instance at a study event.

    FormData groups all item group data collected on one CRF form at
    a study event visit. For repeating forms, multiple FormData elements
    may appear within a StudyEventData, distinguished by FormRepeatKey.

    Supports iteration over its ItemGroupData elements.

    Attributes:
        FormOID (str, required): OID of the FormDef this data belongs to.
        FormRepeatKey (str): For repeating forms, the key identifying
            this particular form instance.
        TransactionType (str): The transaction type for incremental
            transfers.
        AuditRecord: Optional audit trail for this form instance.
        Signature: Optional electronic signature for this form instance.
        ArchiveLayout: Optional archive layout reference.
        Annotation (list): Optional list of review annotations.
        ItemGroupData (list): List of ItemGroupData elements containing
            the dataset records collected on this form.
    """

    FormOID = T.OIDRef(required=True)
    FormRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    ArchiveLayout = T.ODMObject(required=False, element_class=ArchiveLayout)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    ItemGroupData = T.ODMListObject(required=False, element_class=ItemGroupData)

    def __len__(self):
        return len(self.ItemGroupData)

    def __getitem__(self, position):
        return self.ItemGroupData[position]

    def __iter__(self):
        return iter(self.ItemGroupData)


class StudyEventData(OE.ODMElement):
    """Collected data for a single study event (visit) occurrence for a subject.

    StudyEventData groups all form data collected at one study event visit.
    For repeating events, multiple StudyEventData elements may appear
    within a SubjectData, distinguished by StudyEventRepeatKey.

    Supports iteration over its FormData elements.

    Attributes:
        StudyEventOID (str, required): OID of the StudyEventDef this
            data belongs to.
        StudyEventRepeatKey (str): For repeating events, the key
            identifying this particular event occurrence.
        TransactionType (str): The transaction type for incremental
            transfers.
        AuditRecord: Optional audit trail for this event occurrence.
        Signature: Optional electronic signature for this event occurrence.
        Annotation (list): Optional list of review annotations.
        FormData (list): List of FormData elements containing the CRF
            form data collected at this event.
    """

    StudyEventOID = T.OIDRef(required=True)
    StudyEventRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    FormData = T.ODMListObject(required=False, element_class=FormData)

    def __len__(self):
        return len(self.FormData)

    def __getitem__(self, position):
        return self.FormData[position]

    def __iter__(self):
        return iter(self.FormData)


class SubjectData(OE.ODMElement):
    """All clinical data collected for a single study subject.

    SubjectData is the top-level container for one subject's data within
    a ClinicalData element. It organizes the subject's data hierarchically
    by study event, form, item group, and item.

    Supports iteration over its StudyEventData elements.

    Attributes:
        SubjectKey (str, required): The unique subject identifier within
            the study (e.g., subject number or randomization number).
        TransactionType (str): The transaction type for incremental
            transfers.
        AuditRecord: Optional audit trail for the subject record.
        Signature: Optional electronic signature for the subject record.
        InvestigatorRef: Optional reference to the investigator responsible
            for this subject.
        SiteRef: Optional reference to the site where the subject
            is enrolled.
        Annotation (list): Optional list of review annotations.
        StudyEventData (list): List of StudyEventData elements containing
            all data collected for this subject across study events.
    """

    SubjectKey = T.String(required=True)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    InvestigatorRef = T.ODMObject(required=False, element_class=InvestigatorRef)
    SiteRef = T.ODMObject(required=False, element_class=SiteRef)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    StudyEventData = T.ODMListObject(required=False, element_class=StudyEventData)

    def __len__(self):
        return len(self.StudyEventData)

    def __getitem__(self, position):
        return self.StudyEventData[position]

    def __iter__(self):
        return iter(self.StudyEventData)


class AuditRecords(OE.ODMElement):
    """A container for standalone AuditRecord elements at the ClinicalData level.

    Holds audit records that are not directly attached to a specific data
    element but apply at the clinical data level.

    Attributes:
        AuditRecord (list): List of AuditRecord elements.
    """

    AuditRecord = T.ODMListObject(required=False, element_class=AuditRecord)


class Signatures(OE.ODMElement):
    """A container for standalone Signature elements at the ClinicalData level.

    Holds electronic signatures that apply at the clinical data level
    rather than being attached to a specific data element.

    Attributes:
        Signature (list): List of Signature elements.
    """

    Signature = T.ODMListObject(required=False, element_class=Signature)


class Annotations(OE.ODMElement):
    """A container for standalone Annotation elements at the ClinicalData level.

    Holds review annotations that apply at the clinical data level
    rather than being attached to a specific data element.

    Attributes:
        Annotation (list): List of Annotation elements.
    """

    Annotation = T.ODMListObject(required=False, element_class=Annotation)


class ClinicalData(OE.ODMElement):
    """All subject-level clinical data for one study in an ODM document.

    ClinicalData is the primary container for collected study data. It
    references the study and metadata version that define the data
    structure, and contains one SubjectData element per study subject.

    Supports iteration over its SubjectData elements.

    Attributes:
        StudyOID (str, required): OID of the Study this data belongs to.
        MetaDataVersionOID (str, required): OID of the MetaDataVersion
            that defines the data structure for this clinical data.
        SubjectData (list): List of SubjectData elements, one per subject.
        AuditRecords (list): Optional list of AuditRecords containers.
        Signatures (list): Optional list of Signatures containers.
        Annotations (list): Optional list of Annotations containers.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    SubjectData = T.ODMListObject(element_class=SubjectData)
    AuditRecords = T.ODMListObject(element_class=AuditRecords)
    Signatures = T.ODMListObject(element_class=Signatures)
    Annotations = T.ODMListObject(element_class=Annotations)

    def __len__(self):
        return len(self.SubjectData)

    def __getitem__(self, position):
        return self.SubjectData[position]

    def __iter__(self):
        return iter(self.SubjectData)


class ReferenceData(OE.ODMElement):
    """Reference data (e.g., coding dictionaries) associated with a study.

    ReferenceData holds non-subject data that supports the study, such
    as coding dictionaries or lookup tables. It follows the same structure
    as ClinicalData but contains ItemGroupData directly rather than
    subject-organized data.

    Attributes:
        StudyOID (str, required): OID of the Study this reference data
            belongs to.
        MetaDataVersionOID (str, required): OID of the MetaDataVersion
            that defines the data structure.
        ItemGroupData (list): List of ItemGroupData elements containing
            the reference records.
        AuditRecords (list): Optional list of AuditRecords containers.
        Signatures (list): Optional list of Signatures containers.
        Annotations (list): Optional list of Annotations containers.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)
    AuditRecords = T.ODMListObject(element_class=AuditRecords)
    Signatures = T.ODMListObject(element_class=Signatures)
    Annotations = T.ODMListObject(element_class=Annotations)


class KeySet(OE.ODMElement):
    """A set of keys that uniquely identifies a specific data element.

    KeySet is used within Association elements to precisely locate a
    data element within the ODM clinical data hierarchy, from the study
    level down to the individual item level.

    Attributes:
        StudyOID (str, required): OID of the study containing the data.
        SubjectKey (str): The subject identifier.
        StudyEventOID (str): OID of the study event.
        StudyEventRepeatKey (str): Repeat key for repeating study events.
        FormOID (str): OID of the form.
        FormRepeatKey (str): Repeat key for repeating forms.
        ItemGroupOID (str): OID of the item group.
        ItemGroupRepeatKey (str): Repeat key for repeating item groups.
        ItemOID (str): OID of the specific item.
    """

    StudyOID = T.OIDRef(required=True)
    SubjectKey = T.String()
    StudyEventOID = T.OIDRef()
    StudyEventRepeatKey = T.String()
    FormOID = T.OIDRef()
    FormRepeatKey = T.String()
    ItemGroupOID = T.OIDRef()
    ItemGroupRepeatKey = T.String()
    ItemOID = T.OIDRef()


class Association(OE.ODMElement):
    """An association linking an annotation to specific data elements.

    Association elements allow annotations to be associated with
    data elements that may span across subjects or study events by
    using KeySet elements to identify each relevant data point.

    Attributes:
        StudyOID (str, required): OID of the study containing the
            associated data.
        MetaDataVersionOID (str, required): OID of the MetaDataVersion
            defining the data structure.
        KeySet (list, required): List of KeySet elements identifying
            the specific data elements being annotated.
        Annotation (Annotation, required): The annotation being
            associated with the identified data elements.
    """

    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    KeySet = T.ODMListObject(required=True, element_class=KeySet)
    Annotation = T.ODMObject(required=True, element_class=Annotation)


class ODM(OE.ODMElement):
    """The root element of an ODM document.

    ODM is the top-level container for all content in an ODM file. It
    carries document-level metadata (file type, creation date, originator)
    and contains Study, AdminData, ReferenceData, ClinicalData, and
    Association elements.

    Attributes:
        Description (str): Optional human-readable description of the
            ODM document.
        FileType (str, required): The type of ODM file; "Snapshot" for
            complete point-in-time data, "Transactional" for incremental
            updates.
        Granularity (str): Optional granularity of the file content
            (e.g., "All", "Metadata", "AdminData", "ReferenceData",
            "ClinicalData", "SingleSite", "SingleSubject").
        Archival (str): Optional flag indicating whether this is an
            archival version ("Yes" or "No").
        FileOID (str, required): Unique identifier for this ODM file
            instance.
        CreationDateTime (str, required): ISO 8601 date-time string
            indicating when the file was created.
        PriorFileOID (str): OID of the preceding file in a series of
            transactional files.
        AsOfDateTime (str): ISO 8601 date-time for the point in time
            that a Snapshot file represents.
        ODMVersion (str): The version of the ODM standard used
            (e.g., "1.3.2").
        Originator (str): The organization or system that created
            the file.
        SourceSystem (str): The name of the source system that
            generated the file.
        SourceSystemVersion (str): The version of the source system.
        schemaLocation (str): The XML schema location hint, stored
            in the xs:schemaLocation attribute.
        ID (str): Optional unique identifier for this ODM element.
        Study (list): List of Study elements containing study metadata.
        AdminData (list): List of AdminData elements containing user
            and site records.
        ReferenceData (list): List of ReferenceData elements containing
            reference datasets.
        ClinicalData (list): List of ClinicalData elements containing
            subject data.
        Association (list): List of Association elements linking
            annotations to data elements.
    """

    Description = T.String(required=False)
    FileType = T.ValueSetString(required=True)
    Granularity = T.ValueSetString(required=False)
    Archival = T.ValueSetString(required=False)
    FileOID = T.OID(required=True)
    CreationDateTime = T.DateTimeString(required=True)
    PriorFileOID = T.OIDRef(required=False)
    AsOfDateTime = T.DateTimeString(required=False)
    ODMVersion = T.ValueSetString(required=False)
    Originator = T.String(required=False)
    SourceSystem = T.String(required=False)
    SourceSystemVersion = T.String(required=False)
    schemaLocation = T.String(required=False, namespace="xs")
    ID = T.ID()
    Study = T.ODMListObject(element_class=Study)
    AdminData = T.ODMListObject(element_class=AdminData)
    ReferenceData = T.ODMListObject(element_class=ReferenceData)
    ClinicalData = T.ODMListObject(element_class=ClinicalData)
    Association = T.ODMListObject(element_class=Association)
