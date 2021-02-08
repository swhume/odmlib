from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import os


class TestMetaDataVersion(TestCase):
    def setUp(self) -> None:
        attrs = self.set_attributes()
        self.mdv = ODM.MetaDataVersion(**attrs)
        self.odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_mdv_001.xml')

    def test_add_include(self):
        inc = ODM.Include(StudyOID="STUDY.TRACE-XML-DEMO", MetaDataVersionOID="MDV.TRACE-XML-ODM-01")
        self.mdv.Include = inc
        self.assertEqual(self.mdv.Include.StudyOID, 'STUDY.TRACE-XML-DEMO')

    def test_add_protocol(self):
        self.mdv.Protocol = self.add_protocol()
        print(self.mdv.Protocol.to_dict())
        self.assertEqual(self.mdv.Protocol.StudyEventRef[1].StudyEventOID, "FOLLOW-UP")
        self.assertEqual(self.mdv.Protocol.Description.TranslatedText[0]._content, "Trace-XML Test CDASH File")

    def test_add_studyeventdef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.assertEqual(len(self.mdv.StudyEventDef[1].FormRef), 3)
        self.assertEqual(self.mdv.StudyEventDef[1].FormRef[2].FormOID, 'ODM.F.AE')

    def test_add_formdef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.assertEqual(len(self.mdv.FormDef[1].ItemGroupRef), 2)
        self.assertEqual(self.mdv.FormDef[0].ItemGroupRef[2].ItemGroupOID, 'ODM.IG.VS')

    def test_add_itemgroupdef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.assertEqual(len(self.mdv.ItemGroupDef[1].ItemRef), 2)
        self.assertEqual(self.mdv.ItemGroupDef[0].ItemRef[2].ItemOID, 'ODM.IT.VS.BP.SYSBP.VSORRES')

    def test_add_itemdef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.assertEqual("CDASH/SDTM", self.mdv.ItemDef[1].Alias[1].Context)
        self.assertEqual("Diastolic", self.mdv.ItemDef[1].Question.TranslatedText[0]._content)
        self.assertEqual("partialDate", self.mdv.ItemDef[0].DataType)

    def test_add_codelist(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.assertEqual("ODM.CL.NY_SUB_Y_N", self.mdv.CodeList[0].OID)
        self.assertEqual("Yes", self.mdv.CodeList[0].CodeListItem[1].Decode.TranslatedText[0]._content)

    def test_add_methoddef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.assertEqual("ODM.MT.DOB", self.mdv.MethodDef[0].OID)
        self.assertEqual("Concatenation of BRTHYR, BRTHMO, and BRTHDY in ISO 8601 format", self.mdv.MethodDef[0].Description.TranslatedText[0]._content)

    def test_add_conditiondef(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        self.assertEqual("ODM.CD.BRTHMO", self.mdv.ConditionDef[0].OID)
        self.assertEqual("Skip the BRTHMO field when BRTHYR length NE 4", self.mdv.ConditionDef[0].Description.TranslatedText[0]._content)

    def test_add_presentation(self):
        p = ODM.Presentation(OID="ODM.PR.CRF.DM", lang="en", _content="stylesheet")
        self.mdv.Presentation = [p]
        self.assertEqual("ODM.PR.CRF.DM", self.mdv.Presentation[0].OID)

    def test_mdv_to_dict(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        mdv_dict = self.mdv.to_dict()
        print(mdv_dict)
        self.assertDictEqual(self.expected_dict(), mdv_dict)

    def test_mdv_to_xml(self):
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        mdv_xml = self.mdv.to_xml()
        self.assertEqual("MDV.TRACE-XML-ODM-01", mdv_xml.attrib["OID"])
        children = ['Protocol', 'StudyEventDef', 'StudyEventDef', 'FormDef', 'FormDef', 'ItemGroupDef', 'ItemGroupDef',
                    'ItemDef', 'ItemDef', 'CodeList', 'MethodDef', 'ConditionDef']
        found_list = [e.tag for e in mdv_xml.getchildren()]
        print(found_list)
        self.assertListEqual(children, [e.tag for e in mdv_xml.getchildren()])

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
        p.Description = ODM.Description()
        p.Description.TranslatedText = [tt]
        ser1 = ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes")
        ser2 = ODM.StudyEventRef(StudyEventOID="FOLLOW-UP", OrderNumber=2, Mandatory="Yes")
        p.StudyEventRef = [ser1, ser2]
        p.Alias = [ODM.Alias(Context="ClinicalTrials.gov", Name="trace-protocol")]
        return p

    def set_attributes(self):
        return {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}

    def expected_dict(self):
        return {
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
    "MethodDef": [{
        "OID": "ODM.MT.DOB",
        "Name": "Create BRTHDTC from date ELEMENTS",
        "Type": "Computation",
        "Description": {"TranslatedText": [{
            "_content": "Concatenation of BRTHYR, BRTHMO, and BRTHDY in ISO 8601 format",
            "lang": "en"
        }]}
    }],
    "ConditionDef": [{
        "OID": "ODM.CD.BRTHMO",
        "Name": "Skip BRTHMO when no BRTHYR",
        "Description": {"TranslatedText": [{
            "_content": "Skip the BRTHMO field when BRTHYR length NE 4",
            "lang": "en"
        }]}
    }]
}
