from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_parser as ODM_PARSER
import os
import datetime


class TestClinicalData(TestCase):
    def setUp(self) -> None:
        self.odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data','test_clinical_data_01.xml')

    def test_clinical_data_to_xml(self):
        cd = []
        cd.append(ODM.ClinicalData(StudyOID="P2006-101", MetaDataVersionOID="101.01"))
        cd[0].SubjectData.append(ODM.SubjectData(SubjectKey="1000", TransactionType="Insert"))
        cd[0].SubjectData[0].StudyEventData.append(ODM.StudyEventData(StudyEventOID="Screen"))
        cd[0].SubjectData[0].StudyEventData[0].FormData.append(ODM.FormData(FormOID="DEMOG"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="DM"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="USUBJID", Value="101-001-001"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="SEX", Value="F"))
        cd[0].SubjectData[0].StudyEventData[0].FormData.append(ODM.FormData(FormOID="LABDATA"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="LB"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBDTC", Value="2006-07-14T14:48"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBTESTCD", Value="ALT"))
        cd[0].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBORRES", Value="245"))

        cd.append(ODM.ClinicalData(StudyOID="P2006-101", MetaDataVersionOID="101.02"))
        cd[1].SubjectData.append(ODM.SubjectData(SubjectKey="1000", TransactionType="Insert"))
        cd[1].SubjectData[0].StudyEventData.append(ODM.StudyEventData(StudyEventOID="VISIT_1"))
        cd[1].SubjectData[0].StudyEventData[0].FormData.append(ODM.FormData(FormOID="AENONSER"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="AE"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="AETERM", Value="Fever"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="AESTDTC", Value="2006-08-21"))
        cd[1].SubjectData[0].StudyEventData[0].FormData.append(ODM.FormData(FormOID="LABDATA"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="LB"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBDTC", Value="2006-07-14T14:48"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBTESTCD", Value="ALT"))
        cd[1].SubjectData[0].StudyEventData[0].FormData[1].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="LBORRES", Value="300"))

        root = self.create_odm_document(cd)
        odm_xml = root.to_xml()
        self.assertEqual(odm_xml.attrib["FileOID"], "ODM.TEST.CD.001")
        self.assertListEqual(["ClinicalData", "ClinicalData"], [e.tag for e in odm_xml.getchildren()])

    def test_clinical_data_from_xml(self):
        parser = ODM_PARSER.ODMParser(self.odm_test_file)
        parser.parse()
        cd = parser.ClinicalData()
        subj_list = parser.SubjectData(parent=cd[1])
        sed = parser.StudyEventData(parent=subj_list[0]["elem"])
        fd = parser.FormData(parent=sed[0]["elem"])
        igd = parser.ItemGroupData(parent=fd[0]["elem"])
        item_data = parser.ItemData(parent=igd[0]["elem"])
        self.assertEqual(item_data[0]["Value"], "Fever")

    def test_audit_record(self):
        ar = ODM.AuditRecord(EditPoint="Monitoring", UsedImputationMethod="Yes", ID="1")
        ar.UserRef = ODM.UserRef(UserOID="USER.001")
        ar.LocationRef = ODM.LocationRef(LocationOID="SITE.101")
        ar.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        ar.ReasonForChange = ODM.ReasonForChange(_content="Missing data")
        ar.SourceID = ODM.SourceID(_content="RECID14327")
        ar_dict = ar.to_dict()
        print(ar_dict)
        self.assertEqual(ar_dict["EditPoint"], "Monitoring")
        id = ODM.ItemData(ItemOID="IT.AE.AETERM", TransactionType="Insert", Value="Fever")
        id.AuditRecord = ar
        id_dict = id.to_dict()
        self.assertEqual(id_dict["AuditRecord"]["UserRef"]["UserOID"], "USER.001")

    def test_annotation(self):
        annotation = ODM.Annotation(SeqNum="1", TransactionType="Insert", ID="ANN001")
        annotation.Comment = ODM.Comment(SponsorOrSite="Site", _content="Transferred from EHR")
        annotation.Flag.append(ODM.Flag())
        annotation.Flag[0].FlagValue = ODM.FlagValue(CodeListOID="CL.FLAGVALUE", _content="eSource")
        annotation.Flag[0].FlagType = ODM.FlagType(CodeListOID="CL.FLAGTYPE", _content="eDT")
        annotation_dict = annotation.to_dict()
        print(annotation_dict)
        self.assertEqual(annotation_dict["Flag"][0]["FlagValue"]["CodeListOID"], "CL.FLAGVALUE")
        self.assertEqual(annotation.Flag[0].FlagValue.CodeListOID, "CL.FLAGVALUE")

    def test_signature(self):
        sig = ODM.Signature(ID="SIG.001.USER.001")
        sig.UserRef = ODM.UserRef(UserOID="USER.001")
        sig.LocationRef = ODM.LocationRef(LocationOID="SITE.101")
        sig.SignatureRef = ODM.SignatureRef(SignatureOID="SIG.001")
        sig.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        sig_dict = sig.to_dict()
        print(sig_dict)
        self.assertEqual(sig_dict["SignatureRef"]["SignatureOID"], "SIG.001")
        self.assertEqual(sig.SignatureRef.SignatureOID, "SIG.001")

    def test_audit_records(self):
        ar = ODM.AuditRecord(EditPoint="Monitoring", UsedImputationMethod="Yes", ID="1")
        ar.UserRef = ODM.UserRef(UserOID="USER.001")
        ar.LocationRef = ODM.LocationRef(LocationOID="SITE.101")
        ar.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        ar.ReasonForChange = ODM.ReasonForChange(_content="Missing data")
        ar.SourceID = ODM.SourceID(_content="RECID14327")
        ars = ODM.AuditRecords()
        ars.AuditRecord.append(ar)
        self.assertEqual(ars.AuditRecord[0].ID, "1")
        self.assertEqual(ars.AuditRecord[0].LocationRef.LocationOID, "SITE.101")

    def test_signatures(self):
        sig = ODM.Signature(ID="SIG.001.USER.001")
        sig.UserRef = ODM.UserRef(UserOID="USER.001")
        sig.LocationRef = ODM.LocationRef(LocationOID="SITE.101")
        sig.SignatureRef = ODM.SignatureRef(SignatureOID="SIG.001")
        sig.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        sigs = ODM.Signatures()
        sigs.Signature.append(sig)
        self.assertEqual(sigs.Signature[0].ID, "SIG.001.USER.001")
        self.assertEqual(sigs.Signature[0].SignatureRef.SignatureOID, "SIG.001")

    def test_annotations(self):
        annotation = ODM.Annotation(SeqNum="1", TransactionType="Insert", ID="ANN001")
        annotation.Comment = ODM.Comment(SponsorOrSite="Site", _content="Transferred from EHR")
        annotation.Flag.append(ODM.Flag())
        annotation.Flag[0].FlagValue = ODM.FlagValue(CodeListOID="CL.FLAGVALUE", _content="eSource")
        annotation.Flag[0].FlagType = ODM.FlagType(CodeListOID="CL.FLAGTYPE", _content="eDT")
        anns = ODM.Annotations()
        anns.Annotation.append(annotation)
        self.assertEqual(anns.Annotation[0].ID, "ANN001")
        self.assertEqual(anns.Annotation[0].Flag[0].FlagValue.CodeListOID, "CL.FLAGVALUE")

    def create_odm_document(self, cd):
        """
        assemble the ODM document, add the ItemGroupDef, and write it to a file
        :param igd: ItemGroupDef object
        """
        root = self.create_root()
        for clin_data in cd:
            root.ClinicalData.append(clin_data)
        root.write_xml(self.odm_test_file)
        return root

    def create_root(self):
        """
        create the ODM root element object with test data
        :return: ODM root element object
        """
        root = {"FileOID": "ODM.TEST.CD.001", "Granularity": "Metadata", "AsOfDateTime": self.set_datetime(),
                "CreationDateTime": self.set_datetime(), "ODMVersion": "1.3.2", "Originator": "ODMLIB", "SourceSystem": "ODMLIB",
                "SourceSystemVersion": "0.1", "FileType": "Snapshot"}
        root = ODM.ODM(**root)
        return root

    def set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
