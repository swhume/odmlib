from __future__ import annotations
from typing import Optional, List
from odmlib.odm_element import ODMElement

AUXILIARY_NAMESPACES: dict[str, str]

def register_namespaces() -> None: ...


class TranslatedText(ODMElement):
    lang: Optional[str]
    _content: Optional[str]


class Alias(ODMElement):
    Context: Optional[str]
    Name: Optional[str]


class StudyDescription(ODMElement):
    _content: Optional[str]


class ProtocolName(ODMElement):
    _content: Optional[str]


class StudyName(ODMElement):
    _content: Optional[str]


class GlobalVariables(ODMElement):
    StudyName: Optional[StudyName]
    StudyDescription: Optional[StudyDescription]
    ProtocolName: Optional[ProtocolName]


class Symbol(ODMElement):
    TranslatedText: List[TranslatedText]


class MeasurementUnit(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Symbol: Optional[Symbol]
    Alias: List[Alias]


class BasicDefinitions(ODMElement):
    MeasurementUnit: List[MeasurementUnit]


class Include(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]


class Description(ODMElement):
    TranslatedText: List[TranslatedText]


class StudyEventRef(ODMElement):
    StudyEventOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class Protocol(ODMElement):
    Description: Optional[Description]
    StudyEventRef: List[StudyEventRef]
    Alias: List[Alias]


class FormRef(ODMElement):
    FormOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class StudyEventDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Type: Optional[str]
    Category: Optional[str]
    Description: Optional[Description]
    FormRef: List[FormRef]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> FormRef: ...
    def __iter__(self): ...


class ItemGroupRef(ODMElement):
    ItemGroupOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class ArchiveLayout(ODMElement):
    OID: Optional[str]
    PdfFileName: Optional[str]
    PresentationOID: Optional[str]


class FormDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Description: Optional[Description]
    ItemGroupRef: List[ItemGroupRef]
    ArchiveLayout: List[ArchiveLayout]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemGroupRef: ...
    def __iter__(self): ...


class ItemRef(ODMElement):
    ItemOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    KeySequence: Optional[int]
    MethodOID: Optional[str]
    Role: Optional[str]
    RoleCodeListOID: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class ItemGroupDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    IsReferenceData: Optional[str]
    SASDatasetName: Optional[str]
    Domain: Optional[str]
    Origin: Optional[str]
    Purpose: Optional[str]
    Comment: Optional[str]
    Description: Optional[Description]
    ItemRef: List[ItemRef]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemRef: ...
    def __iter__(self): ...


class Question(ODMElement):
    TranslatedText: List[TranslatedText]


class ExternalQuestion(ODMElement):
    Dictionary: Optional[str]
    Version: Optional[str]
    Code: Optional[str]


class MeasurementUnitRef(ODMElement):
    MeasurementUnitOID: Optional[str]


class CheckValue(ODMElement):
    _content: Optional[str]


class FormalExpression(ODMElement):
    Context: Optional[str]
    _content: Optional[str]


class ErrorMessage(ODMElement):
    TranslatedText: List[TranslatedText]


class RangeCheck(ODMElement):
    Comparator: Optional[str]
    SoftHard: Optional[str]
    CheckValue: List[CheckValue]
    FormalExpression: List[FormalExpression]
    MeasurementUnitRef: Optional[MeasurementUnitRef]
    ErrorMessage: Optional[ErrorMessage]


class CodeListRef(ODMElement):
    CodeListOID: Optional[str]


class ItemDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    Length: Optional[int]
    SignificantDigits: Optional[int]
    SASFieldName: Optional[str]
    SDSVarName: Optional[str]
    Origin: Optional[str]
    Comment: Optional[str]
    Description: Optional[Description]
    Question: Optional[Question]
    ExternalQuestion: Optional[ExternalQuestion]
    MeasurementUnitRef: List[MeasurementUnitRef]
    RangeCheck: List[RangeCheck]
    CodeListRef: Optional[CodeListRef]
    Alias: List[Alias]


class Decode(ODMElement):
    TranslatedText: List[TranslatedText]


class CodeListItem(ODMElement):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    Decode: Optional[Decode]
    Alias: List[Alias]


class EnumeratedItem(ODMElement):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    Alias: List[Alias]


class ExternalCodeList(ODMElement):
    Dictionary: Optional[str]
    Version: Optional[str]
    ref: Optional[str]
    href: Optional[str]


class CodeList(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    SASFormatName: Optional[str]
    Description: Optional[Description]
    CodeListItem: List[CodeListItem]
    EnumeratedItem: List[EnumeratedItem]
    ExternalCodeList: Optional[ExternalCodeList]
    Alias: List[Alias]


class Presentation(ODMElement):
    OID: Optional[str]
    lang: Optional[str]
    _content: Optional[str]


class ConditionDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]


class MethodDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    Description: Optional[Description]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]


class MetaDataVersion(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[str]
    Include: Optional[Include]
    Protocol: Optional[Protocol]
    StudyEventDef: List[StudyEventDef]
    FormDef: List[FormDef]
    ItemGroupDef: List[ItemGroupDef]
    ItemDef: List[ItemDef]
    CodeList: List[CodeList]
    Presentation: List[Presentation]
    ConditionDef: List[ConditionDef]
    MethodDef: List[MethodDef]


class LoginName(ODMElement):
    _content: Optional[str]


class DisplayName(ODMElement):
    _content: Optional[str]


class FullName(ODMElement):
    _content: Optional[str]


class FirstName(ODMElement):
    _content: Optional[str]


class LastName(ODMElement):
    _content: Optional[str]


class Organization(ODMElement):
    _content: Optional[str]


class StreetName(ODMElement):
    _content: Optional[str]


class City(ODMElement):
    _content: Optional[str]


class StateProv(ODMElement):
    _content: Optional[str]


class Country(ODMElement):
    _content: Optional[str]


class PostalCode(ODMElement):
    _content: Optional[str]


class OtherText(ODMElement):
    _content: Optional[str]


class Address(ODMElement):
    StreetName: List[StreetName]
    City: Optional[City]
    StateProv: Optional[StateProv]
    Country: Optional[Country]
    PostalCode: Optional[PostalCode]
    OtherText: Optional[OtherText]


class Email(ODMElement):
    _content: Optional[str]


class Picture(ODMElement):
    PictureFileName: Optional[str]
    ImageType: Optional[str]


class Pager(ODMElement):
    _content: Optional[str]


class Fax(ODMElement):
    _content: Optional[str]


class Phone(ODMElement):
    _content: Optional[str]


class LocationRef(ODMElement):
    LocationOID: Optional[str]


class Certificate(ODMElement):
    _content: Optional[str]


class User(ODMElement):
    OID: Optional[str]
    UserType: Optional[str]
    LoginName: Optional[LoginName]
    DisplayName: Optional[DisplayName]
    FullName: Optional[FullName]
    FirstName: Optional[FirstName]
    LastName: Optional[LastName]
    Organization: Optional[Organization]
    Address: List[Address]
    Email: List[Email]
    Pager: Optional[Pager]
    Fax: List[Fax]
    Phone: List[Phone]
    LocationRef: List[LocationRef]
    Certificate: List[Certificate]


class MetaDataVersionRef(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    EffectiveDate: Optional[str]


class Location(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    LocationType: Optional[str]
    MetaDataVersionRef: List[MetaDataVersionRef]


class Meaning(ODMElement):
    _content: Optional[str]


class LegalReason(ODMElement):
    _content: Optional[str]


class SignatureDef(ODMElement):
    OID: Optional[str]
    Methodology: Optional[str]
    Meaning: Optional[Meaning]
    LegalReason: Optional[LegalReason]


class AdminData(ODMElement):
    StudyOID: Optional[str]
    User: List[User]
    Location: List[Location]
    SignatureDef: List[SignatureDef]


class Study(ODMElement):
    OID: Optional[str]
    GlobalVariables: Optional[GlobalVariables]
    BasicDefinitions: Optional[BasicDefinitions]
    MetaDataVersion: List[MetaDataVersion]


class UserRef(ODMElement):
    UserOID: Optional[str]


class DateTimeStamp(ODMElement):
    _content: Optional[str]


class ReasonForChange(ODMElement):
    _content: Optional[str]


class SourceID(ODMElement):
    _content: Optional[str]


class AuditRecord(ODMElement):
    EditPoint: Optional[str]
    UsedImputationMethod: Optional[str]
    ID: Optional[str]
    UserRef: Optional[UserRef]
    LocationRef: Optional[LocationRef]
    DateTimeStamp: Optional[DateTimeStamp]
    ReasonForChange: Optional[ReasonForChange]
    SourceID: Optional[SourceID]


class SignatureRef(ODMElement):
    SignatureOID: Optional[str]


class Signature(ODMElement):
    ID: Optional[str]
    UserRef: Optional[UserRef]
    LocationRef: Optional[LocationRef]
    SignatureRef: Optional[SignatureRef]
    DateTimeStamp: Optional[DateTimeStamp]


class InvestigatorRef(ODMElement):
    UserOID: Optional[str]


class SiteRef(ODMElement):
    LocationOID: Optional[str]


class FlagValue(ODMElement):
    CodeListOID: Optional[str]
    _content: Optional[str]


class FlagType(ODMElement):
    CodeListOID: Optional[str]
    _content: Optional[str]


class Flag(ODMElement):
    FlagValue: Optional[FlagValue]
    FlagType: Optional[FlagType]


class Comment(ODMElement):
    SponsorOrSite: Optional[str]
    _content: Optional[str]


class Annotation(ODMElement):
    SeqNum: Optional[int]
    TransactionType: Optional[str]
    ID: Optional[str]
    Comment: Optional[Comment]
    Flag: List[Flag]


class ItemData(ODMElement):
    ItemOID: Optional[str]
    TransactionType: Optional[str]
    Value: Optional[str]
    IsNull: Optional[str]
    AuditRecord: Optional[AuditRecord]
    Signature: Optional[Signature]
    MeasurementUnitRef: Optional[MeasurementUnitRef]
    Annotation: List[Annotation]


class ItemGroupData(ODMElement):
    ItemGroupOID: Optional[str]
    ItemGroupRepeatKey: Optional[str]
    TransactionType: Optional[str]
    AuditRecord: Optional[AuditRecord]
    Signature: Optional[Signature]
    ArchiveLayout: Optional[ArchiveLayout]
    Annotation: List[Annotation]
    ItemData: List[ItemData]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemData: ...
    def __iter__(self): ...


class FormData(ODMElement):
    FormOID: Optional[str]
    FormRepeatKey: Optional[str]
    TransactionType: Optional[str]
    AuditRecord: Optional[AuditRecord]
    Signature: Optional[Signature]
    ArchiveLayout: Optional[ArchiveLayout]
    Annotation: List[Annotation]
    ItemGroupData: List[ItemGroupData]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemGroupData: ...
    def __iter__(self): ...


class StudyEventData(ODMElement):
    StudyEventOID: Optional[str]
    StudyEventRepeatKey: Optional[str]
    TransactionType: Optional[str]
    AuditRecord: Optional[AuditRecord]
    Signature: Optional[Signature]
    Annotation: List[Annotation]
    FormData: List[FormData]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> FormData: ...
    def __iter__(self): ...


class SubjectData(ODMElement):
    SubjectKey: Optional[str]
    TransactionType: Optional[str]
    AuditRecord: Optional[AuditRecord]
    Signature: Optional[Signature]
    InvestigatorRef: Optional[InvestigatorRef]
    SiteRef: Optional[SiteRef]
    Annotation: List[Annotation]
    StudyEventData: List[StudyEventData]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> StudyEventData: ...
    def __iter__(self): ...


class AuditRecords(ODMElement):
    AuditRecord: List[AuditRecord]


class Signatures(ODMElement):
    Signature: List[Signature]


class Annotations(ODMElement):
    Annotation: List[Annotation]


class ClinicalData(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    SubjectData: List[SubjectData]
    AuditRecords: List[AuditRecords]
    Signatures: List[Signatures]
    Annotations: List[Annotations]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> SubjectData: ...
    def __iter__(self): ...


class ReferenceData(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    ItemGroupData: List[ItemGroupData]
    AuditRecords: List[AuditRecords]
    Signatures: List[Signatures]
    Annotations: List[Annotations]


class KeySet(ODMElement):
    StudyOID: Optional[str]
    SubjectKey: Optional[str]
    StudyEventOID: Optional[str]
    StudyEventRepeatKey: Optional[str]
    FormOID: Optional[str]
    FormRepeatKey: Optional[str]
    ItemGroupOID: Optional[str]
    ItemGroupRepeatKey: Optional[str]
    ItemOID: Optional[str]


class Association(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    KeySet: List[KeySet]
    Annotation: Optional[Annotation]


class ODM(ODMElement):
    Description: Optional[str]
    FileType: Optional[str]
    Granularity: Optional[str]
    Archival: Optional[str]
    FileOID: Optional[str]
    CreationDateTime: Optional[str]
    PriorFileOID: Optional[str]
    AsOfDateTime: Optional[str]
    ODMVersion: Optional[str]
    Originator: Optional[str]
    SourceSystem: Optional[str]
    SourceSystemVersion: Optional[str]
    schemaLocation: Optional[str]
    ID: Optional[str]
    Study: List[Study]
    AdminData: List[AdminData]
    ReferenceData: List[ReferenceData]
    ClinicalData: List[ClinicalData]
    Association: List[Association]
