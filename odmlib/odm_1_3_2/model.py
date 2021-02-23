import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS


NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    lang = T.String(namespace="xml")
    _content = T.String(required=True)


class Alias(OE.ODMElement):
    Context = T.String(required=True)
    Name = T.String(required=True)


class StudyDescription(OE.ODMElement):
    _content = T.String(required=True)


class ProtocolName(OE.ODMElement):
    _content = T.String(required=True)


class StudyName(OE.ODMElement):
    _content = T.String(required=True)


class GlobalVariables(OE.ODMElement):
    StudyName = T.ODMObject(element_class=StudyName)
    StudyDescription = T.ODMObject(element_class=StudyDescription)
    ProtocolName = T.ODMObject(element_class=ProtocolName)


class Symbol(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class MeasurementUnit(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Symbol = T.ODMObject(required=True, element_class=Symbol)
    Alias = T.ODMListObject(element_class=Alias)


class BasicDefinitions(OE.ODMElement):
    MeasurementUnit = T.ODMListObject(element_class=MeasurementUnit)


class Include(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)


class Description(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class StudyEventRef(OE.ODMElement):
    StudyEventOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class Protocol(OE.ODMElement):
    Description = T.ODMObject(element_class=Description)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)
    Alias = T.ODMListObject(element_class=Alias)


class FormRef(OE.ODMElement):
    FormOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class StudyEventDef(OE.ODMElement):
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
    ItemGroupOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class ArchiveLayout(OE.ODMElement):
    OID = T.OID(required=True)
    PdfFileName = T.FileName(required=True)
    PresentationOID = T.OIDRef(required=False)


class FormDef(OE.ODMElement):
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
    ItemOID = T.String(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    KeySequence = T.Integer(required=False)
    MethodOID = T.String(required=False)
    Role = T.String()
    RoleCodeListOID = T.String()
    CollectionExceptionConditionOID = T.String()


class ItemGroupDef(OE.ODMElement):
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
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class ExternalQuestion(OE.ODMElement):
    Dictionary = T.String(required=False)
    Version = T.String(required=False)
    Code = T.String(required=False)


class MeasurementUnitRef(OE.ODMElement):
    MeasurementUnitOID = T.String(required=True)


class CheckValue(OE.ODMElement):
    _content = T.String(required=True)


class FormalExpression(OE.ODMElement):
    Context = T.String(required=True)
    _content = T.String(required=True)


class ErrorMessage(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class RangeCheck(OE.ODMElement):
    Comparator = T.ValueSetString(required=False)
    SoftHard = T.ValueSetString(required=True)
    CheckValue = T.ODMListObject(element_class=CheckValue)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    MeasurementUnitRef = T.ODMObject(element_class=MeasurementUnitRef)
    ErrorMessage = T.ODMObject(element_class=ErrorMessage)


class CodeListRef(OE.ODMElement):
    CodeListOID = T.OIDRef(required=True)


class ItemDef(OE.ODMElement):
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
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class CodeListItem(OE.ODMElement):
    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    OrderNumber = T.Integer(required=False)
    Decode = T.ODMObject(element_class=Decode)
    Alias = T.ODMListObject(element_class=Alias)


class EnumeratedItem(OE.ODMElement):
    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    OrderNumber = T.Integer(required=False)
    Alias = T.ODMListObject(element_class=Alias)


class ExternalCodeList(OE.ODMElement):
    Dictionary = T.String(required=False)
    Version = T.String(required=False)
    ref = T.String(required=False)
    href = T.String(required=False)


class CodeList(OE.ODMElement):
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
    OID = T.OID(required=True)
    lang = T.String(required=False)
    _content = T.String()


class ConditionDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class MethodDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class MetaDataVersion(OE.ODMElement):
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
    _content = T.String(required=True)


class DisplayName(OE.ODMElement):
    _content = T.String(required=True)


class FullName(OE.ODMElement):
    _content = T.String(required=True)


class FirstName(OE.ODMElement):
    _content = T.String(required=True)


class LastName(OE.ODMElement):
    _content = T.String(required=True)


class Organization(OE.ODMElement):
    _content = T.String(required=True)


class StreetName(OE.ODMElement):
    _content = T.String(required=True)


class City(OE.ODMElement):
    _content = T.String(required=True)


class StateProv(OE.ODMElement):
    _content = T.String(required=True)


class Country(OE.ODMElement):
    _content = T.ValueSetString(required=True)


class PostalCode(OE.ODMElement):
    _content = T.String(required=True)


class OtherText(OE.ODMElement):
    _content = T.String(required=True)


class Address(OE.ODMElement):
    StreetName = T.ODMListObject(element_class=StreetName)
    City = T.ODMObject(element_class=City)
    StateProv = T.ODMObject(element_class=StateProv)
    Country = T.ODMObject(element_class=Country)
    PostalCode = T.ODMObject(element_class=PostalCode)
    OtherText = T.ODMObject(element_class=OtherText)


class Email(OE.ODMElement):
    _content = T.Email(required=True)


class Picture(OE.ODMElement):
    PictureFileName = T.FileName(required=True)
    ImageType = T.Name()


class Pager(OE.ODMElement):
    _content = T.String(required=True)


class Fax(OE.ODMElement):
    _content = T.String(required=True)


class Phone(OE.ODMElement):
    _content = T.String(required=True)


class LocationRef(OE.ODMElement):
    LocationOID = T.OIDRef(required=True)


class Certificate(OE.ODMElement):
    _content = T.String(required=True)


class User(OE.ODMElement):
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
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    EffectiveDate = T.DateString(required=True)


class Location(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    LocationType = T.ValueSetString()
    MetaDataVersionRef = T.ODMListObject(required=True, element_class=MetaDataVersionRef)


class Meaning(OE.ODMElement):
    _content = T.String(required=True)


class LegalReason(OE.ODMElement):
    _content = T.String(required=True)


class SignatureDef(OE.ODMElement):
    OID = T.OID(required=True)
    Methodology = T.ValueSetString()
    Meaning = T.ODMObject(required=True, element_class=Meaning)
    LegalReason = T.ODMObject(required=True, element_class=LegalReason)


class AdminData(OE.ODMElement):
    StudyOID = T.OIDRef()
    User = T.ODMListObject(element_class=User)
    Location = T.ODMListObject(element_class=Location)
    SignatureDef = T.ODMListObject(element_class=SignatureDef)


class Study(OE.ODMElement):
    OID = T.String(required=True)
    GlobalVariables = T.ODMObject(required=True, element_class=GlobalVariables)
    BasicDefinitions = T.ODMObject(element_class=BasicDefinitions)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class UserRef(OE.ODMElement):
    UserOID = T.OIDRef(required=True)


class DateTimeStamp(OE.ODMElement):
    _content = T.DateTimeString(required=True)


class ReasonForChange(OE.ODMElement):
    _content = T.String(required=True)


class SourceID(OE.ODMElement):
    _content = T.String(required=True)


class AuditRecord(OE.ODMElement):
    EditPoint = T.ValueSetString(required=False)
    UsedImputationMethod = T.ValueSetString(required=False)
    ID = T.ID(required=False)
    UserRef = T.ODMObject(required=True, element_class=UserRef)
    LocationRef = T.ODMObject(required=True, element_class=LocationRef)
    DateTimeStamp = T.ODMObject(required=True, element_class=DateTimeStamp)
    ReasonForChange = T.ODMObject(required=False, element_class=ReasonForChange)
    SourceID = T.ODMObject(required=False, element_class=SourceID)


class SignatureRef(OE.ODMElement):
    SignatureOID = T.OIDRef(required=True)


class Signature(OE.ODMElement):
    ID = T.ID(required=True)
    UserRef = T.ODMObject(required=True, element_class=UserRef)
    LocationRef = T.ODMObject(required=True, element_class=LocationRef)
    SignatureRef = T.ODMObject(required=True, element_class=SignatureRef)
    DateTimeStamp = T.ODMObject(required=True, element_class=DateTimeStamp)


class InvestigatorRef(OE.ODMElement):
    UserOID = T.OIDRef(required=True)


class SiteRef(OE.ODMElement):
    LocationOID = T.OIDRef(required=True)


class FlagValue(OE.ODMElement):
    CodeListOID = T.OIDRef(required=True)
    _content = T.String(required=True)


class FlagType(OE.ODMElement):
    CodeListOID = T.OIDRef(required=True)
    _content = T.String(required=True)


class Flag(OE.ODMElement):
    FlagValue = T.ODMObject(required=True, element_class=FlagValue)
    FlagType = T.ODMObject(element_class=FlagType)


class Comment(OE.ODMElement):
    SponsorOrSite = T.ValueSetString()
    _content = T.String(required=True)


class Annotation(OE.ODMElement):
    SeqNum = T.Integer(required=True)
    TransactionType = T.ValueSetString(required=False)
    ID = T.ID(required=False)
    Comment = T.ODMObject(required=False, element_class=Comment)
    Flag = T.ODMListObject(element_class=Flag)


class ItemData(OE.ODMElement):
    ItemOID = T.OIDRef(required=True)
    TransactionType = T.ValueSetString(required=False)
    Value = T.String(required=False)
    IsNull = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    MeasurementUnitRef = T.ODMObject(required=False, element_class=MeasurementUnitRef)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)


class ItemGroupData(OE.ODMElement):
    ItemGroupOID = T.OIDRef(required=True)
    ItemGroupRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    ArchiveLayout = T.ODMObject(required=False, element_class=ArchiveLayout)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    ItemData = T.ODMListObject(required=False, element_class=ItemData)


class FormData(OE.ODMElement):
    FormOID = T.OIDRef(required=True)
    FormRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    ArchiveLayout = T.ODMObject(required=False, element_class=ArchiveLayout)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    ItemGroupData = T.ODMListObject(required=False, element_class=ItemGroupData)


class StudyEventData(OE.ODMElement):
    StudyEventOID = T.OIDRef(required=True)
    StudyEventRepeatKey = T.String(required=False)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    FormData = T.ODMListObject(required=False, element_class=FormData)


class SubjectData(OE.ODMElement):
    SubjectKey = T.String(required=True)
    TransactionType = T.ValueSetString(required=False)
    AuditRecord = T.ODMObject(required=False, element_class=AuditRecord)
    Signature = T.ODMObject(required=False, element_class=Signature)
    InvestigatorRef = T.ODMObject(required=False, element_class=InvestigatorRef)
    SiteRef = T.ODMObject(required=False, element_class=SiteRef)
    Annotation = T.ODMListObject(required=False, element_class=Annotation)
    StudyEventData = T.ODMListObject(required=False, element_class=StudyEventData)


class AuditRecords(OE.ODMElement):
    AuditRecord = T.ODMListObject(required=False, element_class=AuditRecord)


class Signatures(OE.ODMElement):
    Signature = T.ODMListObject(required=False, element_class=Signature)


class Annotations(OE.ODMElement):
    Annotation = T.ODMListObject(required=False, element_class=Annotation)


class ClinicalData(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    SubjectData = T.ODMListObject(element_class=SubjectData)
    AuditRecords = T.ODMListObject(element_class=AuditRecords)
    Signatures = T.ODMListObject(element_class=Signatures)
    Annotations = T.ODMListObject(element_class=Annotations)


class ReferenceData(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    ItemGroupData = T.ODMListObject(element_class=ItemGroupData)
    AuditRecords = T.ODMListObject(element_class=AuditRecords)
    Signatures = T.ODMListObject(element_class=Signatures)
    Annotations = T.ODMListObject(element_class=Annotations)


class KeySet(OE.ODMElement):
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
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)
    KeySet = T.ODMListObject(required=True, element_class=KeySet)
    Annotation = T.ODMObject(required=True, element_class=Annotation)


class ODM(OE.ODMElement):
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
