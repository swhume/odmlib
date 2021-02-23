import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")


class TranslatedText(ODM.TranslatedText):
    lang = ODM.TranslatedText.lang
    _content = ODM.TranslatedText._content


class Alias(ODM.Alias):
    Context = ODM.Alias.Context
    Name = ODM.Alias.Name


class StudyDescription(ODM.StudyDescription):
    _content = ODM.StudyDescription._content


class ProtocolName(ODM.ProtocolName):
    _content = ODM.ProtocolName._content


class StudyName(ODM.StudyName):
    _content = ODM.StudyName._content


class GlobalVariables(ODM.GlobalVariables):
    StudyName = ODM.GlobalVariables.StudyName
    StudyDescription = ODM.GlobalVariables.StudyDescription
    ProtocolName = ODM.GlobalVariables.ProtocolName


class Description(ODM.Description):
    TranslatedText = ODM.Description.TranslatedText


class WhereClauseRef(OE.ODMElement):
    namespace = "def"
    WhereClauseOID = T.OIDRef(required=True)


class ItemRef(ODM.ItemRef):
    ItemOID = ODM.ItemRef.ItemOID
    OrderNumber = ODM.ItemRef.OrderNumber
    Mandatory = ODM.ItemRef.Mandatory
    KeySequence = ODM.ItemRef.KeySequence
    MethodOID = ODM.ItemRef.MethodOID
    Role = ODM.ItemRef.Role
    RoleCodeListOID = ODM.ItemRef.RoleCodeListOID
    WhereClauseRef = T.ODMListObject(required=True, element_class=WhereClauseRef, namespace="def")


class title(OE.ODMElement):
    namespace = "def"
    _content = T.String(required=True)


class leaf(OE.ODMElement):
    namespace = "def"
    ID = T.ID(required=True)
    href = T.String(required=True, namespace="xlink")
    title = T.ODMObject(required=True, element_class=title, namespace="def")


class ItemGroupDef(ODM.ItemGroupDef):
    OID = ODM.ItemGroupDef.OID
    Name = ODM.ItemGroupDef.Name
    Repeating = ODM.ItemGroupDef.Repeating
    IsReferenceData = ODM.ItemGroupDef.IsReferenceData
    SASDatasetName = ODM.ItemGroupDef.SASDatasetName
    Domain = ODM.ItemGroupDef.Domain
    Purpose = ODM.ItemGroupDef.Purpose
    Structure = T.String(required=True, namespace="def")
    Class = T.ValueSetString(required=True, namespace="def")
    ArchiveLocationID = T.String(required=True, namespace="def")
    CommentOID = T.OIDRef(namespace="def")
    Description = ODM.ItemGroupDef.Description
    ItemRef = ODM.ItemGroupDef.ItemRef
    Alias = ODM.ItemGroupDef.Alias
    leaf = T.ODMObject(required=True, element_class=leaf, namespace="def")

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CheckValue(ODM.CheckValue):
    _content = ODM.CheckValue._content


class FormalExpression(ODM.FormalExpression):
    Context = ODM.FormalExpression.Context
    _content = ODM.FormalExpression._content


class RangeCheck(ODM.RangeCheck):
    Comparator = ODM.RangeCheck.Comparator
    SoftHard = ODM.RangeCheck.SoftHard
    ItemOID = T.OIDRef(required=True, namespace="def")
    CheckValue = T.ODMListObject(element_class=CheckValue)


class CodeListRef(ODM.CodeListRef):
    CodeListOID = ODM.CodeListRef.CodeListOID


class ValueListRef(OE.ODMElement):
    namespace = "def"
    ValueListOID = T.OIDRef(required=True)


class PDFPageRef(OE.ODMElement):
    namespace = "def"
    Type = T.ValueSetString(required=True)
    PageRefs = T.String()
    FirstPage = T.PositiveInteger()
    LastPage = T.PositiveInteger()


class DocumentRef(OE.ODMElement):
    namespace = "def"
    leafID = T.String(required=True)
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef, namespace="def")


class Origin(OE.ODMElement):
    namespace = "def"
    Type = T.ValueSetString(required=True)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")
    Description = T.ODMObject(element_class=Description)


class ItemDef(ODM.ItemDef):
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
    Origin = T.ODMObject(element_class=Origin, namespace="def")
    ValueListRef = T.ODMObject(element_class=ValueListRef, namespace="def")
    Alias = T.ODMListObject(element_class=Alias)


class Decode(ODM.Decode):
    TranslatedText = ODM.Decode.TranslatedText


class CodeListItem(ODM.CodeListItem):
    CodedValue = ODM.CodeListItem.CodedValue
    Rank = ODM.CodeListItem.Rank
    OrderNumber = ODM.CodeListItem.OrderNumber
    ExtendedValue = T.ValueSetString(namespace="def")
    Decode = ODM.CodeListItem.Decode
    Alias = ODM.CodeListItem.Alias


class EnumeratedItem(ODM.EnumeratedItem):
    CodedValue = ODM.EnumeratedItem.CodedValue
    Rank = ODM.EnumeratedItem.Rank
    OrderNumber = ODM.EnumeratedItem.OrderNumber
    ExtendedValue = T.String(namespace="def")
    Alias = ODM.EnumeratedItem.Alias


class ExternalCodeList(ODM.ExternalCodeList):
    Dictionary = ODM.ExternalCodeList.Dictionary
    Version = ODM.ExternalCodeList.Version
    ref = ODM.ExternalCodeList.ref
    href = ODM.ExternalCodeList.href


class CodeList(ODM.CodeList):
    OID = ODM.CodeList.OID
    Name = ODM.CodeList.Name
    DataType = ODM.CodeList.DataType
    SASFormatName = ODM.CodeList.SASFormatName
    Description = ODM.CodeList.Description
    CodeListItem = ODM.CodeList.CodeListItem
    EnumeratedItem = ODM.CodeList.EnumeratedItem
    ExternalCodeList = ODM.CodeList.ExternalCodeList
    Alias = ODM.CodeList.Alias


class MethodDef(ODM.MethodDef):
    OID = ODM.MethodDef.OID
    Name = ODM.MethodDef.Name
    Type = ODM.MethodDef.Type
    Description = ODM.MethodDef.Description
    FormalExpression = ODM.MethodDef.FormalExpression
    Alias = ODM.MethodDef.Alias
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class AnnotatedCRF(OE.ODMElement):
    namespace = "def"
    DocumentRef = T.ODMObject(required=True, element_class=DocumentRef, namespace="def")


class SupplementalDoc(OE.ODMElement):
    namespace = "def"
    DocumentRef = T.ODMListObject(required=True, element_class=DocumentRef, namespace="def")


class WhereClauseDef(OE.ODMElement):
    namespace = "def"
    OID = T.OID(required=True)
    CommentOID = T.OIDRef(namespace="def")
    RangeCheck = T.ODMListObject(required=True, element_class=RangeCheck)


class ValueListDef(OE.ODMElement):
    namespace = "def"
    OID = T.OID(required=True)
    ItemRef = T.ODMListObject(element_class=ItemRef, required=True)

    def __len__(self):
        return len(self.ItemRef)

    def __getitem__(self, position):
        return self.ItemRef[position]

    def __iter__(self):
        return iter(self.ItemRef)


class CommentDef(OE.ODMElement):
    namespace = "def"
    OID = T.OID(required=True)
    Description = T.ODMObject(element_class=Description)
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")


class MetaDataVersion(ODM.MetaDataVersion):
    OID = ODM.MetaDataVersion.OID
    Name = ODM.MetaDataVersion.Name
    Description = ODM.MetaDataVersion.Description
    DefineVersion = T.ValueSetString(required=True, namespace="def")
    StandardName = T.String(required=True, namespace="def")
    StandardVersion = T.String(required=True, namespace="def")
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
    OID = ODM.Study.OID
    GlobalVariables = ODM.Study.GlobalVariables
    MetaDataVersion = T.ODMObject(element_class=MetaDataVersion)


class ODM(ODM.ODM):
    FileType = ODM.ODM.FileType
    FileOID = ODM.ODM.FileOID
    CreationDateTime = ODM.ODM.CreationDateTime
    AsOfDateTime = ODM.ODM.AsOfDateTime
    ODMVersion = ODM.ODM.ODMVersion
    Originator = ODM.ODM.Originator
    SourceSystem = ODM.ODM.SourceSystem
    SourceSystemVersion = ODM.ODM.SourceSystemVersion
    schemaLocation = ODM.ODM.schemaLocation
    ID = ODM.ODM.ID
    Study = ODM.ODM.Study
