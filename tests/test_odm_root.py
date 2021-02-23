from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import datetime
import xml.etree.ElementTree as ET
import os
import odmlib.odm_loader as OL
import odmlib.loader as LD


class TestODM(TestCase):
    def setUp(self) -> None:
        self.odm = self.add_root()
        self.odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_odm_001.xml')
        self.odm_writer_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_odm_002.xml')
        self.loader = LD.ODMLoader(OL.XMLODMLoader())

    def test_odm_attributes(self):
        self.assertEqual("ODM.MDV.TEST.001", self.odm.FileOID)
        self.assertEqual("Metadata", self.odm.Granularity)

    def test_odm_xml_file(self):
        study = self.add_study()
        self.odm.Study = [study]
        odm_xml = self.odm.to_xml()
        self.write_odm_file(odm_xml)
        found_list = [e.tag for e in odm_xml.getchildren()]
        print(found_list)
        self.assertListEqual(["Study"], [e.tag for e in odm_xml.getchildren()])

    def test_odm_xml_writer(self):
        study = self.add_study()
        self.odm.Study = [study]
        self.odm.write_xml(self.odm_writer_test_file)
        # now test roundtrip by parsing the file
        self.loader.open_odm_document(self.odm_writer_test_file)
        mdv = self.loader.MetaDataVersion()
        self.assertEqual(mdv.Name, "TRACE-XML MDV")
        self.assertEqual(mdv.OID, "MDV.TRACE-XML-ODM-01")

    def test_odm_dict(self):
        study = self.add_study()
        self.odm.Study = [study]
        odm_dict = self.odm.to_dict()
        print(odm_dict)
        self.assertDictEqual(self.expected_dict(), odm_dict)

    def write_odm_file(self, odm_xml):
        tree = ET.ElementTree(odm_xml)
        tree.write(self.odm_test_file, xml_declaration=True)

    def set_datetime(self):
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

    def add_study(self):
        study_name = ODM.StudyName(_content="ODM XML Test Study Name")
        protocol_name = ODM.ProtocolName(_content="ODM XML Test Study")
        study_description = ODM.StudyDescription(_content="Testing the generation of an ODM XML file")
        gv = ODM.GlobalVariables()
        gv.StudyName = study_name
        gv.StudyDescription = study_description
        gv.ProtocolName = protocol_name
        study = ODM.Study(OID="ODM.STUDY.001")
        study.GlobalVariables = gv
        mdv = self.add_mdv()
        study.MetaDataVersion = [mdv]
        return study

    def add_root(self):
        attrs = self.get_root_attributes()
        root = ODM.ODM(**attrs)
        return root

    def get_root_attributes(self):
        attrs = {"FileOID": "ODM.MDV.TEST.001", "Granularity": "Metadata",
                 "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
                 "CreationDateTime": "2020-07-13T00:13:51.309617+00:00", "ODMVersion": "1.3.2", "FileType": "Snapshot",
                 "Originator": "RDS", "SourceSystem": "ODMLib", "SourceSystemVersion": "0.1",
                 "schemaLocation": "http://www.cdisc.org/ns/odm/v1.3 odm1-3-2.xsd"}
        return attrs

    def add_mdv(self):
        attrs = self.set_mdv_attributes()
        mdv = ODM.MetaDataVersion(**attrs)
        mdv.Protocol = self.add_protocol()
        mdv.StudyEventDef = self.add_SED()
        mdv.FormDef = self.add_FD()
        mdv.ItemGroupDef = self.add_IGD()
        mdv.ItemDef = self.add_ITD()
        mdv.CodeList = self.add_CL()
        mdv.ConditionDef = self.add_CD()
        mdv.MethodDef = self.add_MD()
        return mdv

    def add_CD(self):
        tt1 = ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        cd = ODM.ConditionDef(OID="ODM.CD.BRTHMO", Name="Skip BRTHMO when no BRTHYR")
        cd.Description = desc
        return [cd]

    def add_MD(self):
        tt1 = ODM.TranslatedText(_content="Concatenation of BRTHYR, BRTHMO, and BRTHDY in ISO 8601 format", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt1]
        md = ODM.MethodDef(OID="ODM.MT.DOB", Name="Create BRTHDTC from date ELEMENTS", Type="Computation")
        md.Description = desc
        return [md]

    def add_CL(self):
        tt1 = ODM.TranslatedText(_content="No", lang="en")
        dc1 = ODM.Decode()
        dc1.TranslatedText = [tt1]
        cli1 = ODM.CodeListItem(CodedValue="N")
        cli1.Decode = dc1
        tt2 = ODM.TranslatedText(_content="Yes", lang="en")
        dc2 = ODM.Decode()
        dc2.TranslatedText = [tt2]
        cli2 = ODM.CodeListItem(CodedValue="Y")
        cli2.Decode = dc2
        cl = ODM.CodeList(OID="ODM.CL.NY_SUB_Y_N", Name="No Yes Response", DataType="text")
        cl.CodeListItem = [cli1, cli2]
        return [cl]


    def add_ITD(self):
        # ItemDef 1
        ttd1 = ODM.TranslatedText(_content="Date of measurements", lang="en")
        ttq1 = ODM.TranslatedText(_content="Date", lang="en")
        desc1 = ODM.Description()
        desc1.TranslatedText = [ttd1]
        q1 = ODM.Question()
        q1.TranslatedText = [ttq1]
        a1 = ODM.Alias(Context="CDASH", Name="VSDAT")
        itd1 = ODM.ItemDef(OID="ODM.IT.VS.VSDAT", Name="Date", DataType="partialDate")
        itd1.Description = desc1
        itd1.Question = q1
        itd1.Alias = [a1]
        # ItemDef 2
        ttd2 = ODM.TranslatedText(_content="Result of the vital signs measurement as originally received or collected.", lang="en")
        ttq2 = ODM.TranslatedText(_content="Diastolic", lang="en")
        desc2 = ODM.Description()
        desc2.TranslatedText = [ttd2]
        q2 = ODM.Question()
        q2.TranslatedText = [ttq2]
        a2a = ODM.Alias(Context="CDASH", Name="BP.DIABP.VSORRES")
        a2b = ODM.Alias(Context="CDASH/SDTM", Name="VSORRES+VSORRESU")
        itd2 = ODM.ItemDef(OID="ODM.IT.VS.BP.VSORRESU", Name="BP Units", DataType="text")
        itd2.Description = desc2
        itd2.Question = q2
        itd2.Alias = [a2a, a2b]
        return [itd1, itd2]

    def add_IGD(self):
        itr1 = ODM.ItemRef(ItemOID="ODM.IT.VS.VSDAT", Mandatory="Yes")
        itr2 = ODM.ItemRef(ItemOID="ODM.IT.VS.BP.DIABP.VSORRES", Mandatory="Yes")
        itr3 = ODM.ItemRef(ItemOID="ODM.IT.VS.BP.SYSBP.VSORRES", Mandatory="Yes")
        igd1 = ODM.ItemGroupDef(OID="ODM.IG.VS", Name="Vital Sign Measurement", Repeating="Yes")
        igd1.ItemRef = [itr1, itr2, itr3]
        igr4 = ODM.ItemRef(ItemOID="ODM.IT.DM.BRTHYR", Mandatory="Yes")
        igr5 = ODM.ItemRef(ItemOID="ODM.IT.DM.SEX", Mandatory="Yes")
        igd2 = ODM.ItemGroupDef(OID="ODM.IG.DM", Name="Demographics", Repeating="No")
        igd2.ItemRef = [igr4, igr5]
        return [igd1, igd2]

    def add_FD(self):
        igr1 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1)
        igr2 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2)
        igr3 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3)
        fd1 = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs", Repeating="No")
        fd1.ItemGroupRef = [igr1, igr2, igr3]
        igr4 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1)
        igr5 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.DM", Mandatory="Yes", OrderNumber=2)
        fd2 = ODM.FormDef(OID="ODM.F.DM", Name="Demographics", Repeating="No")
        fd2.ItemGroupRef = [igr4, igr5]
        return [fd1, fd2]

    def add_SED(self):
        fr1 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.AE", Mandatory="Yes", OrderNumber=3)
        ser1 = ODM.StudyEventDef(OID="BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
        ser1.FormRef = [fr1, fr2, fr3]
        ser2 = ODM.StudyEventDef(OID="FOLLOW-UP", Name="Follow-up Visit", Repeating="Yes", Type="Scheduled")
        ser2.FormRef = [fr1, fr2, fr3]
        return [ser1, ser2]

    def add_protocol(self):
        p = ODM.Protocol()
        tt = ODM.TranslatedText(_content="Trace-XML Test CDASH File", lang="en")
        desc = ODM.Description()
        desc.TranslatedText = [tt]
        ser1 = ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes")
        ser2 = ODM.StudyEventRef(StudyEventOID="FOLLOW-UP", OrderNumber=2, Mandatory="Yes")
        a = ODM.Alias(Context="ClinicalTrials.gov", Name="trace-protocol")
        p.Description = desc
        p.StudyEventRef = [ser1, ser2]
        p.Alias = [a]
        return p

    def set_mdv_attributes(self):
        return {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}

    def expected_dict(self):
        return {
    "FileOID": "ODM.MDV.TEST.001",
    "Granularity": "Metadata",
    "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
    "CreationDateTime": "2020-07-13T00:13:51.309617+00:00",
    "ODMVersion": "1.3.2",
    "FileType": "Snapshot",
    "Originator": "RDS",
    "SourceSystem": "ODMLib",
    "SourceSystemVersion": "0.1",
    "schemaLocation": "http://www.cdisc.org/ns/odm/v1.3 odm1-3-2.xsd",
    "Study": [{
        "OID": "ODM.STUDY.001",
        "GlobalVariables": {
            "StudyName": {"_content": "ODM XML Test Study Name"},
            "StudyDescription": {"_content": "Testing the generation of an ODM XML file"},
            "ProtocolName": {"_content": "ODM XML Test Study"}
        },
        "MetaDataVersion": [{
            "OID": "MDV.TRACE-XML-ODM-01",
            "Name": "TRACE-XML MDV",
            "Description": "Trace-XML Example",
            "Protocol": {
                "Description": {"TranslatedText": [{
                    "_content": "Trace-XML Test CDASH File",
                    "lang": "en"
                }]},
                "StudyEventRef": [
                    {
                        "StudyEventOID": "BASELINE",
                        "OrderNumber": 1,
                        "Mandatory": "Yes"
                    },
                    {
                        "StudyEventOID": "FOLLOW-UP",
                        "OrderNumber": 2,
                        "Mandatory": "Yes"
                    }
                ],
                "Alias": [{
                    "Context": "ClinicalTrials.gov",
                    "Name": "trace-protocol"
                }]
            },
            "StudyEventDef": [
                {
                    "OID": "BASELINE",
                    "Name": "Baseline Visit",
                    "Repeating": "No",
                    "Type": "Scheduled",
                    "FormRef": [
                        {
                            "FormOID": "ODM.F.DM",
                            "Mandatory": "Yes",
                            "OrderNumber": 1
                        },
                        {
                            "FormOID": "ODM.F.VS",
                            "Mandatory": "Yes",
                            "OrderNumber": 2
                        },
                        {
                            "FormOID": "ODM.F.AE",
                            "Mandatory": "Yes",
                            "OrderNumber": 3
                        }
                    ]
                },
                {
                    "OID": "FOLLOW-UP",
                    "Name": "Follow-up Visit",
                    "Repeating": "Yes",
                    "Type": "Scheduled",
                    "FormRef": [
                        {
                            "FormOID": "ODM.F.DM",
                            "Mandatory": "Yes",
                            "OrderNumber": 1
                        },
                        {
                            "FormOID": "ODM.F.VS",
                            "Mandatory": "Yes",
                            "OrderNumber": 2
                        },
                        {
                            "FormOID": "ODM.F.AE",
                            "Mandatory": "Yes",
                            "OrderNumber": 3
                        }
                    ]
                }
            ],
            "FormDef": [
                {
                    "OID": "ODM.F.VS",
                    "Name": "Vital Signs",
                    "Repeating": "No",
                    "ItemGroupRef": [
                        {
                            "ItemGroupOID": "ODM.IG.Common",
                            "Mandatory": "Yes",
                            "OrderNumber": 1
                        },
                        {
                            "ItemGroupOID": "ODM.IG.VS_GENERAL",
                            "Mandatory": "Yes",
                            "OrderNumber": 2
                        },
                        {
                            "ItemGroupOID": "ODM.IG.VS",
                            "Mandatory": "Yes",
                            "OrderNumber": 3
                        }
                    ]
                },
                {
                    "OID": "ODM.F.DM",
                    "Name": "Demographics",
                    "Repeating": "No",
                    "ItemGroupRef": [
                        {
                            "ItemGroupOID": "ODM.IG.Common",
                            "Mandatory": "Yes",
                            "OrderNumber": 1
                        },
                        {
                            "ItemGroupOID": "ODM.IG.DM",
                            "Mandatory": "Yes",
                            "OrderNumber": 2
                        }
                    ]
                }
            ],
            "ItemGroupDef": [
                {
                    "OID": "ODM.IG.VS",
                    "Name": "Vital Sign Measurement",
                    "Repeating": "Yes",
                    "ItemRef": [
                        {
                            "ItemOID": "ODM.IT.VS.VSDAT",
                            "Mandatory": "Yes"
                        },
                        {
                            "ItemOID": "ODM.IT.VS.BP.DIABP.VSORRES",
                            "Mandatory": "Yes"
                        },
                        {
                            "ItemOID": "ODM.IT.VS.BP.SYSBP.VSORRES",
                            "Mandatory": "Yes"
                        }
                    ]
                },
                {
                    "OID": "ODM.IG.DM",
                    "Name": "Demographics",
                    "Repeating": "No",
                    "ItemRef": [
                        {
                            "ItemOID": "ODM.IT.DM.BRTHYR",
                            "Mandatory": "Yes"
                        },
                        {
                            "ItemOID": "ODM.IT.DM.SEX",
                            "Mandatory": "Yes"
                        }
                    ]
                }
            ],
            "ItemDef": [
                {
                    "OID": "ODM.IT.VS.VSDAT",
                    "Name": "Date",
                    "DataType": "partialDate",
                    "Description": {"TranslatedText": [{
                        "_content": "Date of measurements",
                        "lang": "en"
                    }]},
                    "Question": {"TranslatedText": [{
                        "_content": "Date",
                        "lang": "en"
                    }]},
                    "Alias": [{
                        "Context": "CDASH",
                        "Name": "VSDAT"
                    }]
                },
                {
                    "OID": "ODM.IT.VS.BP.VSORRESU",
                    "Name": "BP Units",
                    "DataType": "text",
                    "Description": {"TranslatedText": [{
                        "_content": "Result of the vital signs measurement as originally received or collected.",
                        "lang": "en"
                    }]},
                    "Question": {"TranslatedText": [{
                        "_content": "Diastolic",
                        "lang": "en"
                    }]},
                    "Alias": [
                        {
                            "Context": "CDASH",
                            "Name": "BP.DIABP.VSORRES"
                        },
                        {
                            "Context": "CDASH/SDTM",
                            "Name": "VSORRES+VSORRESU"
                        }
                    ]
                }
            ],
            "CodeList": [{
                "OID": "ODM.CL.NY_SUB_Y_N",
                "Name": "No Yes Response",
                "DataType": "text",
                "CodeListItem": [
                    {
                        "CodedValue": "N",
                        "Decode": {"TranslatedText": [{
                            "_content": "No",
                            "lang": "en"
                        }]}
                    },
                    {
                        "CodedValue": "Y",
                        "Decode": {"TranslatedText": [{
                            "_content": "Yes",
                            "lang": "en"
                        }]}
                    }
                ]
            }],
            "ConditionDef": [{
                "OID": "ODM.CD.BRTHMO",
                "Name": "Skip BRTHMO when no BRTHYR",
                "Description": {"TranslatedText": [{
                    "_content": "Skip the BRTHMO field when BRTHYR length NE 4",
                    "lang": "en"
                }]}
            }],
            "MethodDef": [{
                "OID": "ODM.MT.DOB",
                "Name": "Create BRTHDTC from date ELEMENTS",
                "Type": "Computation",
                "Description": {"TranslatedText": [{
                    "_content": "Concatenation of BRTHYR, BRTHMO, and BRTHDY in ISO 8601 format",
                    "lang": "en"
                }]}
            }]
        }]
    }]
}
