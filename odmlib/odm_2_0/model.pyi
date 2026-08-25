from __future__ import annotations
from typing import Any, List, Optional
from odmlib.odm_element import ODMElement


class TranslatedText(ODMElement):
    lang: Optional[str]
    Type: Optional[str]
    _content: Optional[str]


class Description(ODMElement):
    TranslatedText: List[TranslatedText]


class Alias(ODMElement):
    Context: Optional[str]
    Name: Optional[str]


class Title(ODMElement):
    _content: Optional[str]


class Leaf(ODMElement):
    ID: Optional[str]
    href: Optional[str]
    Title: Optional[Title]


class Coding(ODMElement):
    Code: Optional[str]
    System: Optional[str]
    SystemName: Optional[str]
    SystemVersion: Optional[str]
    Label: Optional[str]
    href: Optional[str]
    ref: Optional[str]
    CommentOID: Optional[str]


class Include(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    href: Optional[str]


class Standard(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    PublishingSet: Optional[str]
    Version: Optional[str]
    Status: Optional[str]
    CommentOID: Optional[str]


class Standards(ODMElement):
    Standard: List[Standard]


class StudyEventRef(ODMElement):
    StudyEventOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class ParameterValue(ODMElement):
    Value: Optional[str]
    Coding: List[Coding]


class StudyParameter(ODMElement):
    OID: Optional[str]
    Term: Optional[str]
    ShortName: Optional[str]
    ParameterValue: Optional[ParameterValue]
    Coding: List[Coding]


class StudySummary(ODMElement):
    StudyParameter: List[StudyParameter]


class TrialPhase(ODMElement):
    Value: Optional[str]
    Description: Optional[Description]


class StudyIndication(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    Coding: List[Coding]


class StudyIndications(ODMElement):
    StudyIndication: List[StudyIndication]


class StudyIntervention(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    Coding: List[Coding]


class StudyInterventions(ODMElement):
    StudyIntervention: List[StudyIntervention]


class StudyInterventionRef(ODMElement):
    StudyInterventionOID: Optional[str]


class StudyEndPoint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    Level: Optional[str]
    Description: Optional[Description]
    FormalExpression: List[FormalExpression]


class StudyEndPoints(ODMElement):
    StudyEndPoint: List[StudyEndPoint]


class StudyEndPointRef(ODMElement):
    StudyEndPointOID: Optional[str]
    OrderNumber: Optional[int]


class StudyObjective(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Level: Optional[str]
    Description: Optional[Description]
    StudyEndPointRef: List[StudyEndPointRef]


class StudyObjectives(ODMElement):
    StudyObjective: List[StudyObjective]


class StudyTargetPopulation(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    Coding: List[Coding]
    FormalExpression: List[FormalExpression]


class StudyTargetPopulationRef(ODMElement):
    StudyTargetPopulationOID: Optional[str]


class IntercurrentEvent(ODMElement):
    Description: Optional[Description]


class SummaryMeasure(ODMElement):
    Description: Optional[Description]


class StudyEstimand(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Level: Optional[str]
    Description: Optional[Description]
    StudyTargetPopulationRef: Optional[StudyTargetPopulationRef]
    StudyInterventionRef: Optional[StudyInterventionRef]
    StudyEndPointRef: Optional[StudyEndPointRef]
    IntercurrentEvent: List[IntercurrentEvent]
    SummaryMeasure: Optional[SummaryMeasure]


class StudyEstimands(ODMElement):
    StudyEstimand: List[StudyEstimand]


class Criterion(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    ConditionOID: Optional[str]
    Description: Optional[Description]
    Coding: List[Coding]


class InclusionCriteria(ODMElement):
    Criterion: List[Criterion]


class ExclusionCriteria(ODMElement):
    Criterion: List[Criterion]


class InclusionExclusionCriteria(ODMElement):
    InclusionCriteria: Optional[InclusionCriteria]
    ExclusionCriteria: Optional[ExclusionCriteria]


class Protocol(ODMElement):
    Description: Optional[Description]
    StudySummary: Optional[StudySummary]
    StudyStructure: Optional[StudyStructure]
    TrialPhase: Optional[TrialPhase]
    StudyTimings: Optional[StudyTimings]
    StudyIndications: Optional[StudyIndications]
    StudyInterventions: Optional[StudyInterventions]
    StudyObjectives: Optional[StudyObjectives]
    StudyEndPoints: Optional[StudyEndPoints]
    StudyTargetPopulation: Optional[StudyTargetPopulation]
    StudyEstimands: Optional[StudyEstimands]
    InclusionExclusionCriteria: Optional[InclusionExclusionCriteria]
    StudyEventGroupRef: List[StudyEventGroupRef]
    WorkflowRef: Optional[WorkflowRef]
    Alias: List[Alias]


class ItemGroupRef(ODMElement):
    ItemGroupOID: Optional[str]
    MethodOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]


class WorkflowRef(ODMElement):
    WorkflowOID: Optional[str]


class StudyEventDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Type: Optional[str]
    Category: Optional[str]
    Description: Optional[Description]
    ItemGroupRef: List[ItemGroupRef]
    WorkflowRef: Optional[WorkflowRef]
    Coding: List[Coding]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemGroupRef: ...
    def __iter__(self): ...


class PDFPageRef(ODMElement):
    Type: Optional[str]
    PageRefs: Optional[str]
    FirstPage: Optional[int]
    LastPage: Optional[int]
    Title: Optional[str]


class DocumentRef(ODMElement):
    LeafID: Optional[str]
    PDFPageRef: List[PDFPageRef]


class AnnotatedCRF(ODMElement):
    DocumentRef: List[DocumentRef]


class SupplementalDoc(ODMElement):
    DocumentRef: List[DocumentRef]


class CommentDef(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    DocumentRef: List[DocumentRef]


class Selection(ODMElement):
    Path: Optional[str]


class Resource(ODMElement):
    Type: Optional[str]
    Name: Optional[str]
    Attribute: Optional[str]
    Label: Optional[str]
    Selection: List[Selection]


class SourceItem(ODMElement):
    ItemOID: Optional[str]
    ItemGroupOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    StudyOID: Optional[str]
    leafID: Optional[str]
    Name: Optional[str]
    Resource: List[Resource]
    Coding: List[Coding]


class SourceItems(ODMElement):
    SourceItem: List[SourceItem]
    Coding: List[Coding]


class Origin(ODMElement):
    Type: Optional[str]
    Source: Optional[str]
    Description: Optional[Description]
    SourceItems: Optional[SourceItems]
    Coding: List[Coding]
    DocumentRef: List[DocumentRef]


class ItemRef(ODMElement):
    ItemOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    KeySequence: Optional[int]
    MethodOID: Optional[str]
    Role: Optional[str]
    RoleCodeListOID: Optional[str]
    CollectionExceptionConditionOID: Optional[str]
    UnitsItemOID: Optional[str]
    PreSpecifiedValue: Optional[str]


class SubClass(ODMElement):
    Name: Optional[str]
    ParentClass: Optional[str]


class Class(ODMElement):
    Name: Optional[str]
    SubClass: List[SubClass]


class ItemGroupDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    Type: Optional[str]
    IsReferenceData: Optional[str]
    DatasetName: Optional[str]
    Domain: Optional[str]
    Purpose: Optional[str]
    Structure: Optional[str]
    ArchiveLocationID: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    Class: Optional[Class]
    ItemGroupRef: List[ItemGroupRef]
    ItemRef: List[ItemRef]
    WorkflowRef: Optional[WorkflowRef]
    Origin: List[Origin]
    Alias: List[Alias]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemRef: ...
    def __iter__(self): ...


class Question(ODMElement):
    TranslatedText: List[TranslatedText]


class CheckValue(ODMElement):
    _content: Optional[str]


class Code(ODMElement):
    _content: Optional[str]


class ExternalCodeLib(ODMElement):
    Library: Optional[str]
    Method: Optional[str]
    Version: Optional[str]
    ref: Optional[str]
    href: Optional[str]


class FormalExpression(ODMElement):
    Context: Optional[str]
    Code: Optional[Code]
    ExternalCodeLib: Optional[ExternalCodeLib]


class ErrorMessage(ODMElement):
    TranslatedText: List[TranslatedText]


class RangeCheck(ODMElement):
    Comparator: Optional[str]
    SoftHard: Optional[str]
    ItemOID: Optional[str]
    CheckValue: List[CheckValue]
    MethodSignature: Optional[MethodSignature]
    FormalExpression: List[FormalExpression]
    ErrorMessage: Optional[ErrorMessage]


class ValueListDef(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    ItemRef: List[ItemRef]


class WhereClauseDef(ODMElement):
    OID: Optional[str]
    CommentOID: Optional[str]
    RangeCheck: List[RangeCheck]


class CodeListRef(ODMElement):
    CodeListOID: Optional[str]


class ValueListRef(ODMElement):
    ValueListOID: Optional[str]


class ItemDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    Length: Optional[int]
    DisplayFormat: Optional[str]
    VariableSet: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    # The element classes below are defined in model.py but have no stub
    # in this partial .pyi (13 of 97 classes are unstubbed); typed as Any
    # to keep this block correct without expanding stub scope.
    Definition: Optional[Any]
    Question: Optional[Question]
    Prompt: Optional[Any]
    CRFCompletionInstructions: Optional[Any]
    ImplementationNotes: Optional[Any]
    CDISCNotes: Optional[Any]
    RangeCheck: List[RangeCheck]
    CodeListRef: Optional[CodeListRef]
    ValueListRef: Optional[ValueListRef]
    Coding: List[Any]
    Alias: List[Alias]


class Decode(ODMElement):
    TranslatedText: List[TranslatedText]


class CodeListItem(ODMElement):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    ExtendedValue: Optional[str]
    Decode: Optional[Decode]
    Alias: List[Alias]


class CodeList(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    CommentOID: Optional[str]
    StandardOID: Optional[str]
    IsNonStandard: Optional[str]
    Description: Optional[Description]
    CodeListItem: List[CodeListItem]
    Coding: List[Coding]
    Alias: List[Alias]


class ConditionDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    MethodSignature: Optional[MethodSignature]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]


class Parameter(ODMElement):
    Name: Optional[str]
    Definition: Optional[str]
    DataType: Optional[str]
    OrderNumber: Optional[int]


class ReturnValue(ODMElement):
    Name: Optional[str]
    Definition: Optional[str]
    DataType: Optional[str]
    OrderNumber: Optional[int]


class MethodSignature(ODMElement):
    Parameter: List[Parameter]
    ReturnValue: List[ReturnValue]


class MethodDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    Description: Optional[Description]
    MethodSignature: Optional[MethodSignature]
    FormalExpression: List[FormalExpression]
    Alias: List[Alias]
    DocumentRef: List[DocumentRef]


class StudyEventGroupRef(ODMElement):
    StudyEventGroupOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    CollectionExceptionConditionOID: Optional[str]
    Description: Optional[Description]


class Arm(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    WorkflowRef: Optional[WorkflowRef]


class Epoch(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    SequenceNumber: Optional[int]
    Description: Optional[Description]


class StudyStructure(ODMElement):
    Description: Optional[Description]
    Arm: List[Arm]
    Epoch: List[Epoch]
    WorkflowRef: Optional[WorkflowRef]


class WorkflowStart(ODMElement):
    StartOID: Optional[str]


class Transition(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    SourceOID: Optional[str]
    TargetOID: Optional[str]
    StartConditionOID: Optional[str]
    EndConditionOID: Optional[str]


class TargetTransition(ODMElement):
    TargetTransitionOID: Optional[str]
    ConditionOID: Optional[str]


class DefaultTransition(ODMElement):
    TargetTransitionOID: Optional[str]


class Branching(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    TargetTransition: List[TargetTransition]
    DefaultTransition: List[DefaultTransition]


class WorkflowEnd(ODMElement):
    EndOID: Optional[str]
    _content: Optional[str]


class WorkflowDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[Description]
    WorkflowStart: Optional[WorkflowStart]
    Transition: List[Transition]
    Branching: List[Branching]
    WorkflowEnd: List[WorkflowEnd]


class AbsoluteTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    StudyEventGroupOID: Optional[str]
    StudyEventOID: Optional[str]
    TimepointTarget: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class RelativeTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    PredecessorOID: Optional[str]
    SuccessorOID: Optional[str]
    Type: Optional[str]
    TimepointRelativeTarget: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class TransitionTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    TransitionOID: Optional[str]
    MethodOID: Optional[str]
    Type: Optional[str]
    TimepointTarget: Optional[str]
    TimepointPreWindow: Optional[str]
    TimepointPostWindow: Optional[str]
    Description: Optional[Description]


class DurationTimingConstraint(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    StructuralElementOID: Optional[str]
    DurationTarget: Optional[str]
    DurationPreWindow: Optional[str]
    DurationPostWindow: Optional[str]
    Description: Optional[Description]


class StudyTiming(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    AbsoluteTimingConstraint: List[AbsoluteTimingConstraint]
    RelativeTimingConstraint: List[RelativeTimingConstraint]
    TransitionTimingConstraint: List[TransitionTimingConstraint]
    DurationTimingConstraint: List[DurationTimingConstraint]


class StudyTimings(ODMElement):
    StudyTiming: List[StudyTiming]


class StudyEventGroupDef(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    ArmOID: Optional[str]
    EpochOID: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    StudyEventGroupRef: List[StudyEventGroupRef]
    StudyEventRef: List[StudyEventRef]
    WorkflowRef: Optional[WorkflowRef]
    Coding: List[Coding]


class MetaDataVersion(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    Include: Optional[Include]
    Standards: Optional[Standards]
    AnnotatedCRF: Optional[AnnotatedCRF]
    SupplementalDoc: Optional[SupplementalDoc]
    ValueListDef: List[ValueListDef]
    WhereClauseDef: List[WhereClauseDef]
    Protocol: Optional[Protocol]
    WorkflowDef: List[WorkflowDef]
    StudyEventGroupDef: List[StudyEventGroupDef]
    StudyEventDef: List[StudyEventDef]
    ItemGroupDef: List[ItemGroupDef]
    ItemDef: List[ItemDef]
    CodeList: List[CodeList]
    ConditionDef: List[ConditionDef]
    MethodDef: List[MethodDef]
    CommentDef: List[CommentDef]
    Leaf: List[Leaf]


class Prefix(ODMElement):
    _content: Optional[str]


class Suffix(ODMElement):
    _content: Optional[str]


class FullName(ODMElement):
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


class HouseNumber(ODMElement):
    _content: Optional[str]


class GeoPosition(ODMElement):
    Longitude: Optional[float]
    Latitude: Optional[float]
    Altitude: Optional[float]


class Address(ODMElement):
    StreetName: Optional[StreetName]
    HouseNumber: Optional[HouseNumber]
    City: Optional[City]
    StateProv: Optional[StateProv]
    Country: Optional[Country]
    PostalCode: Optional[PostalCode]
    GeoPosition: Optional[GeoPosition]
    OtherText: Optional[OtherText]


class LocationRef(ODMElement):
    LocationOID: Optional[str]


class Telecom(ODMElement):
    TelecomType: Optional[str]
    Value: Optional[str]


class Organization(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Role: Optional[str]
    Type: Optional[str]
    LocationOID: Optional[str]
    PartOfOrganizationOID: Optional[str]
    Description: Optional[Description]
    Address: List[Address]
    Telecom: List[Telecom]


class UserName(ODMElement):
    _content: Optional[str]


class GivenName(ODMElement):
    _content: Optional[str]


class FamilyName(ODMElement):
    _content: Optional[str]


class Image(ODMElement):
    ImageFileName: Optional[str]
    href: Optional[str]
    MimeType: Optional[str]


class User(ODMElement):
    OID: Optional[str]
    UserType: Optional[str]
    OrganizationOID: Optional[str]
    LocationOID: Optional[str]
    UserName: Optional[UserName]
    Prefix: Optional[Prefix]
    Suffix: Optional[Suffix]
    FullName: Optional[FullName]
    GivenName: Optional[GivenName]
    FamilyName: Optional[FamilyName]
    Image: Optional[Image]
    Address: List[Address]
    Telecom: List[Telecom]


class MetaDataVersionRef(ODMElement):
    StudyOID: Optional[str]
    MetaDataVersionOID: Optional[str]
    EffectiveDate: Optional[str]


class Location(ODMElement):
    OID: Optional[str]
    Name: Optional[str]
    Role: Optional[str]
    OrganizationOID: Optional[str]
    Description: Optional[Description]
    MetaDataVersionRef: List[MetaDataVersionRef]
    Address: List[Address]
    Telecom: List[Telecom]


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
    Organization: List[Organization]
    Location: List[Location]
    SignatureDef: List[SignatureDef]


class Study(ODMElement):
    OID: Optional[str]
    StudyName: Optional[str]
    ProtocolName: Optional[str]
    Description: Optional[Description]
    MetaDataVersion: List[MetaDataVersion]


class ODM(ODMElement):
    Description: Optional[str]
    FileType: Optional[str]
    Granularity: Optional[str]
    FileOID: Optional[str]
    CreationDateTime: Optional[str]
    PriorFileOID: Optional[str]
    AsOfDateTime: Optional[str]
    ODMVersion: Optional[str]
    Originator: Optional[str]
    SourceSystem: Optional[str]
    SourceSystemVersion: Optional[str]
    Study: List[Study]
