import odmlib.odm_element as OE
import odmlib.typed as T
import odmlib.ns_registry as NS

NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v2.0", is_default=True)
NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


class TranslatedText(OE.ODMElement):
    lang = T.String(namespace="xml")
    Type = T.String()
    _content = T.String(required=True)


class Description(OE.ODMElement):
    TranslatedText = T.ODMListObject(required=True, element_class=TranslatedText)


class Alias(OE.ODMElement):
    Context = T.String(required=True)
    Name = T.String(required=True)


class StudyDescription(OE.ODMElement):
    Description = T.ODMObject(element_class=Description, required=True)


class ProtocolName(OE.ODMElement):
    _content = T.String(required=True)


class StudyName(OE.ODMElement):
    _content = T.String(required=True)


class Include(OE.ODMElement):
    StudyOID = T.OIDRef(required=True)
    MetaDataVersionOID = T.OIDRef(required=True)


class StudyEventRef(OE.ODMElement):
    StudyEventOID = T.OID(required=True)
    OrderNumber = T.Integer(required=False)
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()


class Protocol(OE.ODMElement):
    Description = T.ODMObject(element_class=Description)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)
    Alias = T.ODMListObject(element_class=Alias)


class StudyEventDef(OE.ODMElement):
    """ represents ODM v2.0 StudyEventDef and can serialize as JSON or XML """
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Type = T.ValueSetString(required=True)
    Category = T.String(required=False)
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)
    Alias = T.ODMListObject(element_class=Alias)

    def __len__(self):
        """ returns the number of FormRefs in an StudyEventDef object as the length """
        return len(self.FormRef)

    def __getitem__(self, position):
        """
        creates an iterator from an StudyEventDef object that returns the FormRef in position
        """
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


    def __len__(self):
        return len(self.ItemGroupRef)

    def __getitem__(self, position):
        return self.ItemGroupRef[position]

    def __iter__(self):
        return iter(self.ItemGroupRef)


class PDFPageRef(OE.ODMElement):
    Type = T.ValueSetString(required=True)
    PageRefs = T.String()
    FirstPage = T.PositiveInteger()
    LastPage = T.PositiveInteger()


class DocumentRef(OE.ODMElement):
    leafID = T.String(required=True)
    PDFPageRef = T.ODMListObject(element_class=PDFPageRef, namespace="def")


class SourceItem(OE.ODMElement):
    leadID = T.IDRef()
    ItemGroupOID = T.OIDRef()
    Resource = T.String()
    Attribute = T.String()
    Path = T.String()
    Label = T.String()


class SourceItems(OE.ODMElement):
    SourceItem = T.ODMListObject(element_class=SourceItem, required=True)


class Origin(OE.ODMElement):
    Type = T.ValueSetString(required=True)
    Source = T.ValueSetString()
    DocumentRef = T.ODMListObject(element_class=DocumentRef, namespace="def")
    Description = T.ODMObject(element_class=Description)
    SourceItems = T.ODMObject(element_class=SourceItems)


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
    """ represents ODM v2.0 ItemGroupDef and can serialize as JSON or XML"""
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Repeating = T.ValueSetString(required=True)
    Type = T.ValueSetString()
    IsReferenceData = T.ValueSetString(required=False)
    DatasetName = T.Name()
    Domain = T.String()
    Purpose = T.String()
    CommentOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)
    ItemGroupRef = T.ODMListObject(element_class=ItemGroupRef)
    ItemRef = T.ODMListObject(element_class=ItemRef)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)
    Origin = T.ODMListObject(element_class=Origin)
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
    """ represents ODM v2.0 RangeCheck element that is a child of ItemDef and can serialize as JSON or XML """
    Comparator = T.ValueSetString(required=False)
    SoftHard = T.ValueSetString()
    CheckValue = T.ODMListObject(element_class=CheckValue)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    ErrorMessage = T.ODMObject(element_class=ErrorMessage)


class CodeListRef(OE.ODMElement):
    CodeListOID = T.String("CodeListOID", required=True)


class ItemDef(OE.ODMElement):
    """ represents ODM v2.0 ItemDef and can serialize as JSON or XML - ordering of properties matters """
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    Length = T.PositiveInteger()
    FractionDigits = T.NonNegativeInteger()
    DatasetVarName = T.Name()
    SDSVarName = T.SASName()
    CommentOID = T.String()
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
    """ represents ODM CodeListItem element that is a child of CodeList and can serialize as JSON or XML """
    CodedValue = T.String(required=True)
    Rank = T.Float(required=False)
    OrderNumber = T.Integer(required=False)
    Decode = T.ODMObject(element_class=Decode)
    Alias = T.ODMListObject(element_class=Alias)


class EnumeratedItem(OE.ODMElement):
    """ represents ODM EnumeratedItem element that is a child of CodeList and can serialize as JSON or XML """
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
    """ represents ODM v1.3.2 CodeList element that can serialize as JSON or XML """
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    DataType = T.ValueSetString(required=True)
    SASFormatName = T.SASFormat()
    Description = T.ODMObject(element_class=Description)
    CodeListItem = T.ODMListObject(element_class=CodeListItem)
    EnumeratedItem = T.ODMListObject(element_class=EnumeratedItem)
    ExternalCodeList = T.ODMObject(element_class=ExternalCodeList)
    Alias = T.ODMListObject(element_class=Alias)


class ConditionDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class Parameter(OE.ODMElement):
    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class ReturnValue(OE.ODMElement):
    Name = T.Name(required=True)
    Definition = T.String()
    DataType = T.ValueSetString(required=True)
    OrderNumber = T.PositiveInteger()


class MethodSignature(OE.ODMElement):
    Parameter = T.ODMListObject(element_class=Parameter)
    ReturnValue = T.ODMListObject(element_class=ReturnValue)


class MethodDef(OE.ODMElement):
    """ represents ODM v2.0 MethodDef and can serialize as JSON or XML """
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    MethodSignature = T.ODMObject(element_class=MethodSignature)
    FormalExpression = T.ODMListObject(element_class=FormalExpression)
    Alias = T.ODMListObject(element_class=Alias)


class StudyEventGroupRef(OE.ODMElement):
    StudyEventGroupOID = T.OIDRef(required=True)
    OrderNumber = T.Integer()
    Mandatory = T.ValueSetString(required=True)
    CollectionExceptionConditionOID = T.OIDRef()
    Description = T.ODMObject(element_class=Description)


class ExceptionEvent(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ConditionOID = T.OIDRef(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)
    StudyEventGroupRef = T.ODMListObject(element_class=StudyEventGroupRef)
    StudyEventRef = T.ODMListObject(element_class=StudyEventRef)


class WorkflowRef(OE.ODMElement):
    WorkflowOID = T.OID(required=True)


class Arm(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowRef = T.ODMObject(element_class=WorkflowRef)


class Epoch(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SequenceNumber = T.PositiveInteger(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyStructure(OE.ODMElement):
    Description = T.ODMObject(element_class=Description)
    Arm = T.ODMListObject(element_class=Arm)
    Epoch = T.ODMListObject(element_class=Epoch)
    WorkflowRef = T.ODMListObject(element_class=WorkflowRef)


class WorkflowStart(OE.ODMElement):
    StartOID = T.OIDRef(required=True)


class Transition(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    SourceOID = T.OIDRef(required=True)
    TargetOID = T.OIDRef(required=True)
    StartConditionOID = T.OIDRef()
    EndConditionOID = T.OIDRef()


class TargetTransition(OE.ODMElement):
    TargetTransitionOID = T.OIDRef(required=True)
    ConditionOID = T.OIDRef(required=True)


class DefaultTransition(OE.ODMElement):
    TargetTransitionOID = T.OIDRef(required=True)


class Branching(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Type = T.ValueSetString(required=True)
    TargetTransition = T.ODMListObject(element_class=TargetTransition, required=True)
    DefaultTransition = T.ODMListObject(element_class=DefaultTransition)


class WorkflowEnd(OE.ODMElement):
    EndOID = T.OIDRef(required=True)


class WorkflowDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    WorkflowStart = T.ODMObject(element_class=WorkflowStart, required=True)
    Transition = T.ODMListObject(element_class=Transition)
    Branching = T.ODMListObject(element_class=Branching)
    WorkflowEnd = T.ODMListObject(element_class=WorkflowEnd, required=True)


class AbsoluteTimingConstraint(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StudyEventGroupOID = T.OIDRef()
    StudyEventOID = T.OIDRef()
    TimepointTarget = T.IncompleteDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class RelativeTimingConstraint(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    PredecessorStudyEventGroupOID = T.OIDRef()
    PredecessorStudyEventOID = T.OIDRef()
    SuccessorStudyEventGroupOID = T.OIDRef()
    SuccessorStudyEventOID = T.OIDRef()
    Type = T.ValueSetString()
    TimepointRelativeTarget = T.DurationDateTimeString(required=True)
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class TransitionTimingConstraint(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    TransitionOID = T.OIDRef(required=True)
    TimepointRelativeTarget = T.DurationDateTimeString(required=True)
    MethodOID = T.OIDRef()
    TimepointPreWindow = T.DurationDateTimeString(required=True)
    TimepointPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class DurationTimingConstraint(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    StructuralElementOID = T.OIDRef(required=True)
    DurationTarget = T.DurationDateTimeString(required=True)
    DurationPreWindow = T.DurationDateTimeString(required=True)
    DurationPostWindow = T.DurationDateTimeString(required=True)
    Description = T.ODMObject(element_class=Description)


class StudyTiming(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    AbsoluteTimingConstraint = T.ODMListObject(element_class=AbsoluteTimingConstraint)
    RelativeTimingConstraint = T.ODMListObject(element_class=RelativeTimingConstraint)
    TransitionTimingConstraint = T.ODMObject(element_class=TransitionTimingConstraint)
    DurationTimingConstraint = T.ODMListObject(element_class=DurationTimingConstraint)


class StudyEventGroupDef(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    ArmOID = T.OIDRef(required=True)
    EpochOID = T.OIDRef(required=True)
    Description = T.ODMObject(element_class=Description)


class MetaDataVersion(OE.ODMElement):
    OID = T.OID(required=True)
    Name = T.Name(required=True)
    Description = T.ODMObject(element_class=Description)
    Include = T.ODMObject(element_class=Include)
    Protocol = T.ODMObject(element_class=Protocol)
    StudyStructure = T.ODMObject(element_class=StudyStructure)
    WorkflowDef = T.ODMListObject(element_class=WorkflowDef)
    StudyTiming = T.ODMObject(element_class=StudyTiming)
    StudyEventGroupDef = T.ODMListObject(element_class=StudyEventGroupDef)
    StudyEventDef = T.ODMListObject(element_class=StudyEventDef)
    ItemGroupDef = T.ODMListObject(element_class=ItemGroupDef)
    ItemDef = T.ODMListObject(element_class=ItemDef)
    CodeList = T.ODMListObject(element_class=CodeList)
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
    """ v2.0 """
    OID = T.String(required=True)
    StudyName = T.String(required=True)
    ProtocolName = T.String(required=True)
    Description = T.ODMObject(required=True, element_class=Description)
    MetaDataVersion = T.ODMListObject(required=False, element_class=MetaDataVersion)


class ODM(OE.ODMElement):
    """ v2.0 """
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
    ID = T.ID()
    Study = T.ODMListObject(element_class=Study)
    AdminData = T.ODMListObject(element_class=AdminData)
    #ReferenceData = T.ODMListObject(element_class=referencedata.ReferenceData)
    #ClinicalData = T.ODMListObject(element_class=clinicaldata.ClinicalData)
    #Association = T.ODMListObject(element_class=association.Association)
    #ds_Signature = T.ODMListObject(element_class=dssignature.ds_Signature)

