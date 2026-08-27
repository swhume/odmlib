"""ARM (Analysis Results Metadata) 1.0 model classes.

Extends Define-XML 2.1 with elements for describing analysis results,
result displays, programming code, and analysis datasets.  ARM is used
in ADaM Define-XML documents to capture analysis metadata.

The ARM namespace is ``http://www.cdisc.org/ns/arm/v1.0``.

All non-ARM-specific classes are re-exported from
:mod:`odmlib.define_2_1.model` so that a single model import provides
every element needed for a complete ARM-extended Define-XML document.
"""
import odmlib.define_2_1.model as DEF
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS

# arm is an extension namespace embedded in Define-XML documents whose default
# namespace must remain ODM — it must never be registered as the default
NS.NamespaceRegistry(prefix="arm", uri="http://www.cdisc.org/ns/arm/v1.0")


# ---------------------------------------------------------------------------
# Re-exported Define-XML 2.1 base classes
# ---------------------------------------------------------------------------

class TranslatedText(DEF.TranslatedText):
    """ARM TranslatedText element (identical to Define-XML 2.1)."""
    lang = DEF.TranslatedText.lang
    _content = DEF.TranslatedText._content


class Description(DEF.Description):
    """ARM Description element (identical to Define-XML 2.1)."""
    TranslatedText = DEF.Description.TranslatedText


class Alias(DEF.Alias):
    """ARM Alias element (identical to Define-XML 2.1)."""
    Context = DEF.Alias.Context
    Name = DEF.Alias.Name


class StudyDescription(DEF.StudyDescription):
    """ARM StudyDescription element (identical to Define-XML 2.1)."""
    _content = DEF.StudyDescription._content


class ProtocolName(DEF.ProtocolName):
    """ARM ProtocolName element (identical to Define-XML 2.1)."""
    _content = DEF.ProtocolName._content


class StudyName(DEF.StudyName):
    """ARM StudyName element (identical to Define-XML 2.1)."""
    _content = DEF.StudyName._content


class GlobalVariables(DEF.GlobalVariables):
    """ARM GlobalVariables element (identical to Define-XML 2.1)."""
    StudyName = DEF.GlobalVariables.StudyName
    StudyDescription = DEF.GlobalVariables.StudyDescription
    ProtocolName = DEF.GlobalVariables.ProtocolName


class WhereClauseRef(DEF.WhereClauseRef):
    """ARM WhereClauseRef element (def namespace)."""
    namespace = "def"
    WhereClauseOID = DEF.WhereClauseRef.WhereClauseOID


class PDFPageRef(DEF.PDFPageRef):
    """ARM PDFPageRef element (def namespace)."""
    namespace = "def"
    Type = DEF.PDFPageRef.Type
    PageRefs = DEF.PDFPageRef.PageRefs
    FirstPage = DEF.PDFPageRef.FirstPage
    LastPage = DEF.PDFPageRef.LastPage
    Title = DEF.PDFPageRef.Title


class DocumentRef(DEF.DocumentRef):
    """ARM DocumentRef element (def namespace)."""
    namespace = "def"
    leafID = DEF.DocumentRef.leafID
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef, namespace="def")


class title(DEF.title):
    """ARM title element (def namespace)."""
    namespace = "def"
    _content = DEF.title._content


class leaf(DEF.leaf):
    """ARM leaf element (def namespace)."""
    namespace = "def"
    ID = DEF.leaf.ID
    href = DEF.leaf.href
    title = DEF.leaf.title


class SubClass(DEF.SubClass):
    """ARM SubClass element (def namespace)."""
    namespace = "def"
    Name = DEF.SubClass.Name
    ParentClass = DEF.SubClass.ParentClass


class Class(DEF.Class):
    """ARM Class element (def namespace)."""
    namespace = "def"
    Name = DEF.Class.Name
    SubClass = DEF.Class.SubClass


class ItemRef(DEF.ItemRef):
    """ARM ItemRef element (identical to Define-XML 2.1)."""
    ItemOID = DEF.ItemRef.ItemOID
    OrderNumber = DEF.ItemRef.OrderNumber
    Mandatory = DEF.ItemRef.Mandatory
    KeySequence = DEF.ItemRef.KeySequence
    MethodOID = DEF.ItemRef.MethodOID
    Role = DEF.ItemRef.Role
    RoleCodeListOID = DEF.ItemRef.RoleCodeListOID
    IsNonStandard = DEF.ItemRef.IsNonStandard
    HasNoData = DEF.ItemRef.HasNoData
    WhereClauseRef = DEF.ItemRef.WhereClauseRef


class ItemGroupDef(DEF.ItemGroupDef):
    """ARM ItemGroupDef element (identical to Define-XML 2.1)."""
    OID = DEF.ItemGroupDef.OID
    Name = DEF.ItemGroupDef.Name
    Repeating = DEF.ItemGroupDef.Repeating
    IsReferenceData = DEF.ItemGroupDef.IsReferenceData
    SASDatasetName = DEF.ItemGroupDef.SASDatasetName
    Domain = DEF.ItemGroupDef.Domain
    Purpose = DEF.ItemGroupDef.Purpose
    Structure = DEF.ItemGroupDef.Structure
    ArchiveLocationID = DEF.ItemGroupDef.ArchiveLocationID
    CommentOID = DEF.ItemGroupDef.CommentOID
    IsNonStandard = DEF.ItemGroupDef.IsNonStandard
    StandardOID = DEF.ItemGroupDef.StandardOID
    HasNoData = DEF.ItemGroupDef.HasNoData
    Description = DEF.ItemGroupDef.Description
    ItemRef = DEF.ItemGroupDef.ItemRef
    Alias = DEF.ItemGroupDef.Alias
    Class = DEF.ItemGroupDef.Class
    leaf = DEF.ItemGroupDef.leaf

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CheckValue(DEF.CheckValue):
    """ARM CheckValue element (identical to Define-XML 2.1)."""
    _content = T.String(required=False)


class FormalExpression(DEF.FormalExpression):
    """ARM FormalExpression element (identical to Define-XML 2.1)."""
    Context = DEF.FormalExpression.Context
    _content = DEF.FormalExpression._content


class RangeCheck(DEF.RangeCheck):
    """ARM RangeCheck element (identical to Define-XML 2.1)."""
    Comparator = DEF.RangeCheck.Comparator
    SoftHard = DEF.RangeCheck.SoftHard
    ItemOID = DEF.RangeCheck.ItemOID
    CheckValue = DEF.RangeCheck.CheckValue


class CodeListRef(DEF.CodeListRef):
    """ARM CodeListRef element (identical to Define-XML 2.1)."""
    CodeListOID = DEF.CodeListRef.CodeListOID


class ValueListRef(DEF.ValueListRef):
    """ARM ValueListRef element (def namespace)."""
    namespace = "def"
    ValueListOID = DEF.ValueListRef.ValueListOID


class Origin(DEF.Origin):
    """ARM Origin element (def namespace)."""
    namespace = "def"
    Type = DEF.Origin.Type
    Source = DEF.Origin.Source
    Description = DEF.Origin.Description
    DocumentRef = DEF.Origin.DocumentRef


class ItemDef(DEF.ItemDef):
    """ARM ItemDef element (identical to Define-XML 2.1)."""
    OID = DEF.ItemDef.OID
    Name = DEF.ItemDef.Name
    DataType = DEF.ItemDef.DataType
    Length = DEF.ItemDef.Length
    SignificantDigits = DEF.ItemDef.SignificantDigits
    SASFieldName = DEF.ItemDef.SASFieldName
    DisplayFormat = DEF.ItemDef.DisplayFormat
    CommentOID = DEF.ItemDef.CommentOID
    Description = DEF.ItemDef.Description
    CodeListRef = DEF.ItemDef.CodeListRef
    Origin = DEF.ItemDef.Origin
    ValueListRef = DEF.ItemDef.ValueListRef
    Alias = DEF.ItemDef.Alias


class Decode(DEF.Decode):
    """ARM Decode element (identical to Define-XML 2.1)."""
    TranslatedText = DEF.Decode.TranslatedText


class CodeListItem(DEF.CodeListItem):
    """ARM CodeListItem element (identical to Define-XML 2.1)."""
    CodedValue = DEF.CodeListItem.CodedValue
    Rank = DEF.CodeListItem.Rank
    OrderNumber = DEF.CodeListItem.OrderNumber
    ExtendedValue = DEF.CodeListItem.ExtendedValue
    Description = DEF.CodeListItem.Description
    Decode = DEF.CodeListItem.Decode
    Alias = DEF.CodeListItem.Alias


class EnumeratedItem(DEF.EnumeratedItem):
    """ARM EnumeratedItem element (identical to Define-XML 2.1)."""
    CodedValue = DEF.EnumeratedItem.CodedValue
    Rank = DEF.EnumeratedItem.Rank
    OrderNumber = DEF.EnumeratedItem.OrderNumber
    ExtendedValue = DEF.EnumeratedItem.ExtendedValue
    Description = DEF.EnumeratedItem.Description
    Alias = DEF.EnumeratedItem.Alias


class ExternalCodeList(DEF.ExternalCodeList):
    """ARM ExternalCodeList element (identical to Define-XML 2.1)."""
    Dictionary = DEF.ExternalCodeList.Dictionary
    Version = DEF.ExternalCodeList.Version
    ref = DEF.ExternalCodeList.ref
    href = DEF.ExternalCodeList.href


class CodeList(DEF.CodeList):
    """ARM CodeList element (identical to Define-XML 2.1)."""
    OID = DEF.CodeList.OID
    Name = DEF.CodeList.Name
    DataType = DEF.CodeList.DataType
    IsNonStandard = DEF.CodeList.IsNonStandard
    StandardOID = DEF.CodeList.StandardOID
    SASFormatName = DEF.CodeList.SASFormatName
    CommentOID = DEF.CodeList.CommentOID
    Description = DEF.CodeList.Description
    CodeListItem = DEF.CodeList.CodeListItem
    EnumeratedItem = DEF.CodeList.EnumeratedItem
    ExternalCodeList = DEF.CodeList.ExternalCodeList
    Alias = DEF.CodeList.Alias


class MethodDef(DEF.MethodDef):
    """ARM MethodDef element (identical to Define-XML 2.1)."""
    OID = DEF.MethodDef.OID
    Name = DEF.MethodDef.Name
    Type = DEF.MethodDef.Type
    Description = DEF.MethodDef.Description
    FormalExpression = DEF.MethodDef.FormalExpression
    DocumentRef = DEF.MethodDef.DocumentRef


class AnnotatedCRF(DEF.AnnotatedCRF):
    """ARM AnnotatedCRF element (def namespace)."""
    namespace = "def"
    DocumentRef = DEF.AnnotatedCRF.DocumentRef


class SupplementalDoc(DEF.SupplementalDoc):
    """ARM SupplementalDoc element (def namespace)."""
    namespace = "def"
    DocumentRef = DEF.SupplementalDoc.DocumentRef


class WhereClauseDef(DEF.WhereClauseDef):
    """ARM WhereClauseDef element (def namespace)."""
    namespace = "def"
    OID = DEF.WhereClauseDef.OID
    CommentOID = DEF.WhereClauseDef.CommentOID
    RangeCheck = DEF.WhereClauseDef.RangeCheck


class ValueListDef(DEF.ValueListDef):
    """ARM ValueListDef element (def namespace)."""
    namespace = "def"
    OID = DEF.ValueListDef.OID
    Description = DEF.ValueListDef.Description
    ItemRef = DEF.ValueListDef.ItemRef

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CommentDef(DEF.CommentDef):
    """ARM CommentDef element (def namespace)."""
    namespace = "def"
    OID = DEF.CommentDef.OID
    Description = DEF.CommentDef.Description
    DocumentRef = DEF.CommentDef.DocumentRef


class Standard(DEF.Standard):
    """ARM Standard element (def namespace)."""
    namespace = "def"
    OID = DEF.Standard.OID
    Name = DEF.Standard.Name
    Type = DEF.Standard.Type
    PublishingSet = DEF.Standard.PublishingSet
    Version = DEF.Standard.Version
    Status = DEF.Standard.Status
    CommentOID = DEF.Standard.CommentOID


class Standards(DEF.Standards):
    """ARM Standards element (def namespace)."""
    namespace = "def"
    Standard = DEF.Standards.Standard

    def __len__(self):
        return len(self.Standard)

    def __getitem__(self, position):
        return self.Standard[position]

    def __iter__(self):
        return iter(self.Standard)


# ---------------------------------------------------------------------------
# ARM-specific classes (Analysis Results Metadata)
# ---------------------------------------------------------------------------

class Documentation(OE.ODMElement):
    """ARM Documentation element containing descriptive text and references.

    Provides documentation for an analysis result, including a description
    and references to external documents (e.g., SAP sections).

    Attributes:
        Description: Textual description of the documentation.
        DocumentRef: References to external documents.
    """
    namespace = "arm"
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class Code(OE.ODMElement):
    """ARM Code element containing programming code text.

    Holds the actual source code text for an analysis (e.g., SAS code).

    Attributes:
        _content (str): The programming code text content.
    """
    namespace = "arm"
    _content = T.String(required=False)


class ProgrammingCode(OE.ODMElement):
    """ARM ProgrammingCode element describing analysis code.

    Contains the programming context (e.g., "SAS version 9.2"),
    the code itself, and optional references to code documentation.

    Attributes:
        Context (str): Programming language/environment context.
        Code: The programming code content.
        DocumentRef: References to external code documentation.
    """
    namespace = "arm"
    Context = T.String
    Code = T.ODMObject(element_class=Code, namespace="arm")
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class AnalysisVariable(OE.ODMElement):
    """ARM AnalysisVariable element referencing a variable used in analysis.

    Attributes:
        ItemOID (str, required): OID reference to the ItemDef for this variable.
    """
    namespace = "arm"
    ItemOID = T.OIDRef(required=True)


class AnalysisDataset(OE.ODMElement):
    """ARM AnalysisDataset element describing a dataset used in analysis.

    References an ItemGroupDef and optionally filters rows via a
    WhereClauseRef.  Contains the list of analysis variables used
    from this dataset.

    Attributes:
        ItemGroupOID (str, required): OID reference to the ItemGroupDef.
        WhereClauseRef: Optional row filter clause.
        AnalysisVariable: List of variables from this dataset used in the analysis.
    """
    namespace = "arm"
    ItemGroupOID = T.OIDRef(required=True)
    WhereClauseRef = T.ODMObject(element_class=WhereClauseRef, namespace="def")
    AnalysisVariable = T.ODMListObject(element_class=AnalysisVariable, namespace="arm")


class AnalysisDatasets(OE.ODMElement):
    """ARM AnalysisDatasets container for analysis dataset references.

    Attributes:
        CommentOID (str): Optional OID reference to a CommentDef.
        AnalysisDataset: List of analysis datasets.
    """
    namespace = "arm"
    CommentOID = T.OIDRef(namespace="def")
    AnalysisDataset = T.ODMListObject(element_class=AnalysisDataset, namespace="arm")

    def __len__(self):
        return len(self.AnalysisDataset)

    def __getitem__(self, position):
        return self.AnalysisDataset[position]

    def __iter__(self):
        return iter(self.AnalysisDataset)


class AnalysisResult(OE.ODMElement):
    """ARM AnalysisResult element describing a single analysis result.

    Captures the reason and purpose for the analysis, along with
    documentation, programming code, and the datasets involved.

    Attributes:
        OID (str, required): Unique identifier for this analysis result.
        ParameterOID (str): OID reference to the parameter variable.
        AnalysisReason (str, required): Reason for the analysis
            (e.g., "SPECIFIED IN SAP", "DATA DRIVEN").
        AnalysisPurpose (str, required): Purpose of the analysis
            (e.g., "PRIMARY OUTCOME MEASURE").
        Description: Textual description of the analysis.
        AnalysisDatasets: Datasets used in this analysis.
        Documentation: Supporting documentation and references.
        ProgrammingCode: Code used to produce this result.
    """
    namespace = "arm"
    OID = T.OID(required=True)
    ParameterOID = T.OIDRef(required=False)
    AnalysisReason = T.ExtendedValidValues(required=True, valid_values=["SPECIFIED IN PROTOCOL", "SPECIFIED IN SAP",
                                                                        "DATA DRIVEN", "REQUESTED BY REGULATORY AGENCY"])
    AnalysisPurpose = T.ExtendedValidValues(required=True, valid_values=["PRIMARY OUTCOME MEASURE", "SECONDARY OUTCOME MEASURE",
                                                                         "EXPLORATORY OUTCOME MEASURE"])
    # Declaration order is serialization order, and the ARM XSD requires the
    # sequence Description, AnalysisDatasets, Documentation, ProgrammingCode.
    # AnalysisDatasets must stay ahead of Documentation/ProgrammingCode or the
    # written document fails schema validation.
    Description = T.ODMObject(element_class=Description)
    AnalysisDatasets = T.ODMObject(element_class=AnalysisDatasets, namespace="arm")
    Documentation = T.ODMObject(element_class=Documentation, namespace="arm")
    ProgrammingCode = T.ODMObject(element_class=ProgrammingCode, namespace="arm")


class ResultDisplay(OE.ODMElement):
    """ARM ResultDisplay element representing a display of analysis results.

    Groups one or more AnalysisResult elements that share a common
    display (e.g., a table or figure in a clinical study report).

    Attributes:
        OID (str, required): Unique identifier for this result display.
        Name (str, required): Human-readable name of the display.
        Description: Textual description of the display.
        DocumentRef: References to the display location in external documents.
        AnalysisResult: List of analysis results shown in this display.
    """
    namespace = "arm"
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")
    AnalysisResult = T.ODMListObject(element_class=AnalysisResult, required=True, namespace="arm")

    def __len__(self):
        return len(self.AnalysisResult)

    def __getitem__(self, position):
        return self.AnalysisResult[position]

    def __iter__(self):
        return iter(self.AnalysisResult)


class AnalysisResultDisplays(OE.ODMElement):
    """ARM AnalysisResultDisplays container at the MetaDataVersion level.

    Top-level ARM element that holds all ResultDisplay elements for
    an ADaM Define-XML document.

    Attributes:
        ResultDisplay: List of result displays.
    """
    namespace = "arm"
    ResultDisplay = T.ODMListObject(element_class=ResultDisplay, required=True, namespace="arm")

    def __len__(self):
        return len(self.ResultDisplay)

    def __getitem__(self, position):
        return self.ResultDisplay[position]

    def __iter__(self):
        return iter(self.ResultDisplay)


# ---------------------------------------------------------------------------
# Root structure classes (MetaDataVersion, Study, ODM)
# ---------------------------------------------------------------------------

class MetaDataVersion(DEF.MetaDataVersion):
    """ARM-extended MetaDataVersion adding AnalysisResultDisplays.

    Extends the Define-XML 2.1 MetaDataVersion with the ARM
    AnalysisResultDisplays element.
    """
    OID = DEF.MetaDataVersion.OID
    Name = DEF.MetaDataVersion.Name
    Description = DEF.MetaDataVersion.Description
    DefineVersion = DEF.MetaDataVersion.DefineVersion
    CommentOID = DEF.MetaDataVersion.CommentOID
    Standards = DEF.MetaDataVersion.Standards
    AnnotatedCRF = DEF.MetaDataVersion.AnnotatedCRF
    SupplementalDoc = DEF.MetaDataVersion.SupplementalDoc
    ValueListDef = DEF.MetaDataVersion.ValueListDef
    WhereClauseDef = DEF.MetaDataVersion.WhereClauseDef
    ItemGroupDef = DEF.MetaDataVersion.ItemGroupDef
    ItemDef = DEF.MetaDataVersion.ItemDef
    CodeList = DEF.MetaDataVersion.CodeList
    MethodDef = DEF.MetaDataVersion.MethodDef
    CommentDef = DEF.MetaDataVersion.CommentDef
    leaf = DEF.MetaDataVersion.leaf
    AnalysisResultDisplays = T.ODMObject(element_class=AnalysisResultDisplays, namespace="arm")


class Study(DEF.Study):
    """ARM-extended Study element."""
    OID = DEF.Study.OID
    GlobalVariables = DEF.Study.GlobalVariables
    MetaDataVersion = T.ODMObject(required=True, element_class=MetaDataVersion)


class ODM(DEF.ODM):
    """ARM-extended ODM root element."""
    FileType = DEF.ODM.FileType
    FileOID = DEF.ODM.FileOID
    CreationDateTime = DEF.ODM.CreationDateTime
    AsOfDateTime = DEF.ODM.AsOfDateTime
    ODMVersion = DEF.ODM.ODMVersion
    Originator = DEF.ODM.Originator
    SourceSystem = DEF.ODM.SourceSystem
    SourceSystemVersion = DEF.ODM.SourceSystemVersion
    schemaLocation = DEF.ODM.schemaLocation
    Context = DEF.ODM.Context
    ID = DEF.ODM.ID
    Study = T.ODMObject(required=True, element_class=Study)
