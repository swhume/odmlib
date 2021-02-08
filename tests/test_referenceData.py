from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_parser as ODM_PARSER
import xml.etree.ElementTree as ET
import os
import datetime


class TestReferenceData(TestCase):
    def setUp(self) -> None:
        self.odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data','test_referece_data_01.xml')

    def test_reference_data_to_xml(self):
        rd = []
        rd.append(ODM.ReferenceData(StudyOID="P2006-101", MetaDataVersionOID="101.01"))
        rd[0].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.REFSAMP", ItemGroupRepeatKey="1", TransactionType="Insert"))
        rd[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.REF1", Value="1"))
        rd[0].ItemGroupData[0].ItemData.append(ODM.ItemData(ItemOID="IT.REF2", Value="Sample reference data line 1"))
        rd[0].ItemGroupData.append(ODM.ItemGroupData(ItemGroupOID="IG.REFSAMP", ItemGroupRepeatKey="2", TransactionType="Insert"))
        rd[0].ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.REF1", Value="2"))
        rd[0].ItemGroupData[1].ItemData.append(ODM.ItemData(ItemOID="IT.REF2", Value="Sample reference data line 2"))
        root = self.create_odm_document(rd)
        odm_xml = root.to_xml()
        self.assertEqual(odm_xml.attrib["FileOID"], "ODM.TEST.RD.001")
        self.assertListEqual(["ReferenceData"], [e.tag for e in odm_xml.getchildren()])

    def test_clinical_data_from_xml(self):
        parser = ODM_PARSER.ODMParser(self.odm_test_file)
        parser.parse()
        rd = parser.ReferenceData()
        igd_list = parser.ItemGroupData(parent=rd[0])
        item_data = parser.ItemData(parent=igd_list[1]["elem"])
        self.assertEqual(item_data[0]["Value"], "2")

    def test_audit_records(self):
        ar = ODM.AuditRecord(EditPoint="Monitoring", UsedImputationMethod="Yes", ID="2")
        ar.UserRef = ODM.UserRef(UserOID="USER.001")
        ar.LocationRef = ODM.LocationRef(LocationOID="SITE.102")
        ar.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        ar.ReasonForChange = ODM.ReasonForChange(_content="Missing data")
        ar.SourceID = ODM.SourceID(_content="RECID14327")
        ars = ODM.AuditRecords()
        ars.AuditRecord.append(ar)
        rd = []
        rd.append(ODM.ReferenceData(StudyOID="P2006-101", MetaDataVersionOID="101.01"))
        rd[0].AuditRecords.append(ars)
        self.assertEqual(rd[0].AuditRecords[0].AuditRecord[0].ID, "2")
        self.assertEqual(rd[0].AuditRecords[0].AuditRecord[0].LocationRef.LocationOID, "SITE.102")

    def test_signatures(self):
        sig = ODM.Signature(ID="SIG.001.USER.002")
        sig.UserRef = ODM.UserRef(UserOID="USER.001")
        sig.LocationRef = ODM.LocationRef(LocationOID="SITE.101")
        sig.SignatureRef = ODM.SignatureRef(SignatureOID="SIG.002")
        sig.DateTimeStamp = ODM.DateTimeStamp(_content="2020-12-01T10:28:16")
        sigs = ODM.Signatures()
        sigs.Signature.append(sig)
        rd = []
        rd.append(ODM.ReferenceData(StudyOID="P2006-101", MetaDataVersionOID="101.01"))
        rd[0].Signatures.append(sigs)
        self.assertEqual(rd[0].Signatures[0].Signature[0].ID, "SIG.001.USER.002")
        self.assertEqual(rd[0].Signatures[0].Signature[0].SignatureRef.SignatureOID, "SIG.002")

    def test_annotations(self):
        annotation = ODM.Annotation(SeqNum="1", TransactionType="Insert", ID="ANN999")
        annotation.Comment = ODM.Comment(SponsorOrSite="Site", _content="Transferred from EHR")
        annotation.Flag.append(ODM.Flag())
        annotation.Flag[0].FlagValue = ODM.FlagValue(CodeListOID="CL.FLAGVALUE", _content="eSource")
        annotation.Flag[0].FlagType = ODM.FlagType(CodeListOID="CL.FLAGTYPE", _content="eDT")
        anns = ODM.Annotations()
        anns.Annotation.append(annotation)
        rd = []
        rd.append(ODM.ReferenceData(StudyOID="P2006-101", MetaDataVersionOID="101.01"))
        rd[0].Annotations.append(anns)
        self.assertEqual(rd[0].Annotations[0].Annotation[0].ID, "ANN999")
        self.assertEqual(rd[0].Annotations[0].Annotation[0].Flag[0].FlagValue.CodeListOID, "CL.FLAGVALUE")

    def create_odm_document(self, rd):
        """
        assemble the ODM document, add the ItemGroupDef, and write it to a file
        :param igd: ItemGroupDef object
        """
        root = self.create_root()
        for ref_data in rd:
            root.ReferenceData.append(ref_data)
        root.write_xml(self.odm_test_file)
        return root

    def create_root(self):
        """
        create the ODM root element object with test data
        :return: ODM root element object
        """
        root = {"FileOID": "ODM.TEST.RD.001", "Granularity": "Metadata", "AsOfDateTime": self.set_datetime(),
                "CreationDateTime": self.set_datetime(), "ODMVersion": "1.3.2", "Originator": "ODMLIB", "SourceSystem": "ODMLIB",
                "SourceSystemVersion": "0.1", "FileType": "Snapshot"}
        root = ODM.ODM(**root)
        return root

    def set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()
