from __future__ import annotations
from typing import Optional, List
from odmlib.odm_element import ODMElement
from odmlib.odm_1_3_2 import model as ODMBase

AUXILIARY_NAMESPACES: dict[str, str]

def register_namespaces() -> None: ...


class TranslatedText(ODMBase.TranslatedText):
    lang: Optional[str]
    _content: Optional[str]


class Alias(ODMBase.Alias):
    Context: Optional[str]
    Name: Optional[str]


class StudyDescription(ODMBase.StudyDescription):
    _content: Optional[str]


class ProtocolName(ODMBase.ProtocolName):
    _content: Optional[str]


class StudyName(ODMBase.StudyName):
    _content: Optional[str]


class GlobalVariables(ODMBase.GlobalVariables):
    StudyName: Optional[StudyName]
    StudyDescription: Optional[StudyDescription]
    ProtocolName: Optional[ProtocolName]


class Description(ODMBase.Description):
    TranslatedText: List[TranslatedText]


class WhereClauseRef(ODMElement):
    WhereClauseOID: Optional[str]


class ItemRef(ODMBase.ItemRef):
    ItemOID: Optional[str]
    OrderNumber: Optional[int]
    Mandatory: Optional[str]
    KeySequence: Optional[int]
    MethodOID: Optional[str]
    Role: Optional[str]
    RoleCodeListOID: Optional[str]
    IsNonStandard: Optional[str]
    HasNoData: Optional[str]
    WhereClauseRef: List[WhereClauseRef]


class title(ODMElement):
    _content: Optional[str]


class leaf(ODMElement):
    ID: Optional[str]
    href: Optional[str]
    title: Optional[title]


class SubClass(ODMElement):
    Name: Optional[str]
    ParentClass: Optional[str]


class Class(ODMElement):
    Name: Optional[str]
    SubClass: List[SubClass]


class ItemGroupDef(ODMBase.ItemGroupDef):
    OID: Optional[str]
    Name: Optional[str]
    Repeating: Optional[str]
    IsReferenceData: Optional[str]
    SASDatasetName: Optional[str]
    Domain: Optional[str]
    Purpose: Optional[str]
    Structure: Optional[str]
    ArchiveLocationID: Optional[str]
    CommentOID: Optional[str]
    IsNonStandard: Optional[str]
    StandardOID: Optional[str]
    HasNoData: Optional[str]
    Description: Optional[Description]
    ItemRef: List[ItemRef]
    Alias: List[Alias]
    Class: Optional[Class]
    leaf: Optional[leaf]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemRef: ...
    def __iter__(self): ...


class CheckValue(ODMBase.CheckValue):
    _content: Optional[str]


class FormalExpression(ODMBase.FormalExpression):
    Context: Optional[str]
    _content: Optional[str]


class RangeCheck(ODMBase.RangeCheck):
    Comparator: Optional[str]
    SoftHard: Optional[str]
    ItemOID: Optional[str]
    CheckValue: List[CheckValue]


class CodeListRef(ODMBase.CodeListRef):
    CodeListOID: Optional[str]


class ValueListRef(ODMElement):
    ValueListOID: Optional[str]


class PDFPageRef(ODMElement):
    Type: Optional[str]
    PageRefs: Optional[str]
    FirstPage: Optional[int]
    LastPage: Optional[int]
    Title: Optional[str]


class DocumentRef(ODMElement):
    leafID: Optional[str]
    PDFPageRef: List[PDFPageRef]


class Origin(ODMElement):
    Type: Optional[str]
    Source: Optional[str]
    Description: Optional[Description]
    DocumentRef: List[DocumentRef]


class ItemDef(ODMBase.ItemDef):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    Length: Optional[int]
    SignificantDigits: Optional[int]
    SASFieldName: Optional[str]
    DisplayFormat: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    CodeListRef: Optional[CodeListRef]
    Origin: List[Origin]
    ValueListRef: Optional[ValueListRef]
    Alias: List[Alias]


class Decode(ODMBase.Decode):
    TranslatedText: List[TranslatedText]


class CodeListItem(ODMBase.CodeListItem):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    ExtendedValue: Optional[str]
    Description: Optional[Description]
    Decode: Optional[Decode]
    Alias: List[Alias]


class EnumeratedItem(ODMBase.EnumeratedItem):
    CodedValue: Optional[str]
    Rank: Optional[float]
    OrderNumber: Optional[int]
    ExtendedValue: Optional[str]
    Description: Optional[Description]
    Alias: List[Alias]


class ExternalCodeList(ODMBase.ExternalCodeList):
    Dictionary: Optional[str]
    Version: Optional[str]
    ref: Optional[str]
    href: Optional[str]


class CodeList(ODMBase.CodeList):
    OID: Optional[str]
    Name: Optional[str]
    DataType: Optional[str]
    IsNonStandard: Optional[str]
    StandardOID: Optional[str]
    SASFormatName: Optional[str]
    CommentOID: Optional[str]
    Description: Optional[Description]
    CodeListItem: List[CodeListItem]
    EnumeratedItem: List[EnumeratedItem]
    ExternalCodeList: Optional[ExternalCodeList]
    Alias: List[Alias]


class MethodDef(ODMBase.MethodDef):
    OID: Optional[str]
    Name: Optional[str]
    Type: Optional[str]
    Description: Optional[Description]
    FormalExpression: List[FormalExpression]
    DocumentRef: List[DocumentRef]


class AnnotatedCRF(ODMElement):
    DocumentRef: Optional[DocumentRef]


class SupplementalDoc(ODMElement):
    DocumentRef: List[DocumentRef]


class WhereClauseDef(ODMElement):
    OID: Optional[str]
    CommentOID: Optional[str]
    RangeCheck: List[RangeCheck]


class ValueListDef(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    ItemRef: List[ItemRef]
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> ItemRef: ...
    def __iter__(self): ...


class CommentDef(ODMElement):
    OID: Optional[str]
    Description: Optional[Description]
    DocumentRef: List[DocumentRef]


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
    def __len__(self) -> int: ...
    def __getitem__(self, position: int) -> Standard: ...
    def __iter__(self): ...


class MetaDataVersion(ODMBase.MetaDataVersion):
    OID: Optional[str]
    Name: Optional[str]
    Description: Optional[str]
    DefineVersion: Optional[str]
    CommentOID: Optional[str]
    Standards: Optional[Standards]
    AnnotatedCRF: Optional[AnnotatedCRF]
    SupplementalDoc: Optional[SupplementalDoc]
    ValueListDef: List[ValueListDef]
    WhereClauseDef: List[WhereClauseDef]
    ItemGroupDef: List[ItemGroupDef]
    ItemDef: List[ItemDef]
    CodeList: List[CodeList]
    MethodDef: List[MethodDef]
    CommentDef: List[CommentDef]
    leaf: List[leaf]


class Study(ODMBase.Study):
    OID: Optional[str]
    GlobalVariables: Optional[GlobalVariables]
    MetaDataVersion: Optional[MetaDataVersion]


class ODM(ODMBase.ODM):
    FileType: Optional[str]
    FileOID: Optional[str]
    CreationDateTime: Optional[str]
    AsOfDateTime: Optional[str]
    ODMVersion: Optional[str]
    Originator: Optional[str]
    SourceSystem: Optional[str]
    SourceSystemVersion: Optional[str]
    schemaLocation: Optional[str]
    Context: Optional[str]
    ID: Optional[str]
    Study: Optional[Study]
