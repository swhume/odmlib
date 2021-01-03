from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA
import odmlib.odm_1_3_2.rules.oid_ref as OID


class TestConformanceCheckODM(TestCase):
    def setUp(self):
        self.validator = METADATA.MetadataSchema()
        self.oid_checker = OID.OIDRef()

    def test_OID_unique_clean(self):
        attrs = {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}
        self.mdv = ODM.MetaDataVersion(**attrs)
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        # oid uniqueness check and ref/def init
        self.mdv.verify_oids(self.oid_checker)
        # oid ref/def check
        self.assertTrue(self.oid_checker.check_oid_refs())

    def test_OID_unique_dirty(self):
        attrs = {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}
        self.mdv = ODM.MetaDataVersion(**attrs)
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD()
        self.mdv.ItemDef = self.add_ITD_nonunique()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        oid_checker = OID.OIDRef()
        with self.assertRaises(ValueError):
            # checks for non-unique OIDs and runs the ref/def check
            self.mdv.verify_oids(oid_checker)

    def test_OID_refdef_dirty(self):
        attrs = {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}
        self.mdv = ODM.MetaDataVersion(**attrs)
        self.mdv.Protocol = self.add_protocol()
        self.mdv.StudyEventDef = self.add_SED()
        self.mdv.FormDef = self.add_FD()
        self.mdv.ItemGroupDef = self.add_IGD_refdef()
        self.mdv.ItemDef = self.add_ITD()
        self.mdv.CodeList = self.add_CL()
        self.mdv.MethodDef = self.add_MD()
        self.mdv.ConditionDef = self.add_CD()
        oid_checker = OID.OIDRef()
        with self.assertRaises(ValueError):
            # checks for non-unique OIDs and runs the ref/def check
            self.mdv.verify_oids(oid_checker)

    def test_OID_creation_dirty(self):
        attrs = {"OID": "MDV.TRACE-XML-ODM-01", "Description": "Trace-XML Example"}
        with self.assertRaises(ValueError):
            # MDV creation should fail due to missing Name attribute
            self.mdv = ODM.MetaDataVersion(**attrs)

    def test_MethodDef_missing_Description(self):
        attrs = {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}
        self.mdv = ODM.MetaDataVersion(**attrs)
        tt1 = ODM.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        desc1 = ODM.Description()
        desc1.TranslatedText.append(tt1)
        # MethodDef creation that includes the Description object
        md1 = ODM.MethodDef(OID="ODM.MT.AGE", Name="Algorithm to dervive AGE", Type="Computation", Description=desc1)
        self.mdv.MethodDef.append(md1)
        # MethodDef creation succeeds without Description object
        md2 = ODM.MethodDef(OID="ODM.MT.DOB", Name="Create BRTHDTC from date ELEMENTS", Type="Computation")
        self.mdv.MethodDef.append(md2)
        # test that both MethodDefs were added to MDV
        self.assertEqual(len(self.mdv.MethodDef), 2)
        # test that the content of Description exists for the first MethodDef
        self.assertEqual(self.mdv.MethodDef[0].Description.TranslatedText[0]._content, "Age at Screening Date (Screening Date - Birth date)")
        validator = METADATA.MetadataSchema()
        # this is how you check conformance that includes required elements, not just attributes
        is_valid = self.mdv.MethodDef[0].verify_conformance(validator)
        # Test shows that MethodDef conforms to schema
        self.assertTrue(is_valid)
        print(self.mdv.MethodDef[0].to_dict())
        print(self.mdv.MethodDef[1].to_dict())
        with self.assertRaises(ValueError):
            # test shows that MethodDef two fails the schema check because it is missing the required Description object
            self.mdv.MethodDef[1].verify_conformance(validator)

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

    def add_SED(self):
        fr1 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber=1)
        fr2 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber=2)
        fr3 = ODM.FormRef(FormOID="ODM.F.AE", Mandatory="Yes", OrderNumber=3)
        ser1 = ODM.StudyEventDef(OID="BASELINE", Name="Baseline Visit", Repeating="No", Type="Scheduled")
        ser1.FormRef = [fr1, fr2, fr3]
        ser2 = ODM.StudyEventDef(OID="FOLLOW-UP", Name="Follow-up Visit", Repeating="Yes", Type="Scheduled")
        ser2.FormRef = [fr1, fr2, fr3]
        return [ser1, ser2]

    def add_FD(self):
        igr1 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1)
        #igr2 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2)
        igr3 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3)
        fd1 = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs", Repeating="No")
        #fd1.ItemGroupRef = [igr1, igr2, igr3]
        fd1.ItemGroupRef = [igr1, igr3]
        igr4 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1)
        igr5 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.DM", Mandatory="Yes", OrderNumber=2)
        fd2 = ODM.FormDef(OID="ODM.F.DM", Name="Demographics", Repeating="No")
        fd2.ItemGroupRef = [igr4, igr5]
        igr6 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.Common", Mandatory="Yes", OrderNumber=1)
        igr7 = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.AE", Mandatory="Yes", OrderNumber=2)
        fd3 = ODM.FormDef(OID="ODM.F.AE", Name="Adverse Events", Repeating="No")
        fd3.ItemGroupRef = [igr6, igr7]
        return [fd1, fd2, fd3]

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
        igr6 = ODM.ItemRef(ItemOID="ODM.IT.Common.SubjectID", Mandatory="Yes")
        igr7 = ODM.ItemRef(ItemOID="ODM.IT.Common.Visit", Mandatory="Yes")
        igd3 = ODM.ItemGroupDef(OID="ODM.IG.Common", Name="Common", Repeating="No")
        igd3.ItemRef = [igr6, igr7]
        igr8 = ODM.ItemRef(ItemOID="ODM.IT.AE.AETERM", Mandatory="Yes")
        igr9 = ODM.ItemRef(ItemOID="ODM.IT.AE.AESEV", Mandatory="Yes")
        igd4 = ODM.ItemGroupDef(OID="ODM.IG.AE", Name="Adverse Events", Repeating="Yes")
        igd4.ItemRef = [igr8, igr9]
        return [igd1, igd2, igd3, igd4]

    def add_IGD_refdef(self):
        itr1 = ODM.ItemRef(ItemOID="ODM.IT.VS.VSDAT", Mandatory="Yes")
        itr2 = ODM.ItemRef(ItemOID="ODM.IT.VS.BP.DIABP.VSORRES_BAD", Mandatory="Yes")
        itr3 = ODM.ItemRef(ItemOID="ODM.IT.VS.BP.SYSBP.VSORRES", Mandatory="Yes")
        igd1 = ODM.ItemGroupDef(OID="ODM.IG.VS", Name="Vital Sign Measurement", Repeating="Yes")
        igd1.ItemRef = [itr1, itr2, itr3]
        igr4 = ODM.ItemRef(ItemOID="ODM.IT.DM.BRTHYR", Mandatory="Yes")
        igr5 = ODM.ItemRef(ItemOID="ODM.IT.DM.SEX", Mandatory="Yes")
        igd2 = ODM.ItemGroupDef(OID="ODM.IG.DM", Name="Demographics", Repeating="No")
        igd2.ItemRef = [igr4, igr5]
        igr6 = ODM.ItemRef(ItemOID="ODM.IT.Common.SubjectID", Mandatory="Yes")
        igr7 = ODM.ItemRef(ItemOID="ODM.IT.Common.Visit", Mandatory="Yes")
        igd3 = ODM.ItemGroupDef(OID="ODM.IG.Common", Name="Common", Repeating="No")
        igd3.ItemRef = [igr6, igr7]
        igr8 = ODM.ItemRef(ItemOID="ODM.IT.AE.AETERM", Mandatory="Yes")
        igr9 = ODM.ItemRef(ItemOID="ODM.IT.AE.AESEV", Mandatory="Yes")
        igd4 = ODM.ItemGroupDef(OID="ODM.IG.AE", Name="Adverse Events", Repeating="Yes")
        igd4.ItemRef = [igr8, igr9]
        return [igd1, igd2, igd3, igd4]

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
        # ItemDef 3
        ttd3 = ODM.TranslatedText(_content="Adverse Event Term", lang="en")
        ttq3 = ODM.TranslatedText(_content="AE Term", lang="en")
        desc3 = ODM.Description()
        desc3.TranslatedText = [ttd3]
        q3 = ODM.Question()
        q3.TranslatedText = [ttq3]
        itd3 = ODM.ItemDef(OID="ODM.IT.AE.AETERM", Name="AE Term", DataType="text")
        itd3.Description = desc3
        itd3.Question = q3
        # ItemDef 4
        ttd4 = ODM.TranslatedText(_content="Adverse Event Severity", lang="en")
        ttq4 = ODM.TranslatedText(_content="AE Severity", lang="en")
        desc4 = ODM.Description()
        desc4.TranslatedText = [ttd4]
        q4 = ODM.Question()
        q4.TranslatedText = [ttq4]
        itd4 = ODM.ItemDef(OID="ODM.IT.AE.AESEV", Name="AE Severity", DataType="text")
        itd4.Description = desc4
        itd4.Question = q4
        # ItemDef 5
        ttd5 = ODM.TranslatedText(_content="Subject ID", lang="en")
        ttq5 = ODM.TranslatedText(_content="Subject ID", lang="en")
        desc5 = ODM.Description()
        desc5.TranslatedText = [ttd5]
        q5 = ODM.Question()
        q5.TranslatedText = [ttq5]
        itd5 = ODM.ItemDef(OID="ODM.IT.Common.SubjectID", Name="Subject ID", DataType="text")
        itd5.Description = desc5
        itd5.Question = q5
        # ItemDef 6
        ttd6 = ODM.TranslatedText(_content="Diastolic Blood Pressure Result", lang="en")
        ttq6 = ODM.TranslatedText(_content="Diastolic BP", lang="en")
        desc6 = ODM.Description()
        desc6.TranslatedText = [ttd6]
        q6 = ODM.Question()
        q6.TranslatedText = [ttq6]
        itd6 = ODM.ItemDef(OID="ODM.IT.VS.BP.DIABP.VSORRES", Name="DBP Result", DataType="text")
        itd6.Description = desc6
        itd6.Question = q6
        # ItemDef 7
        ttd7 = ODM.TranslatedText(_content="Birth Year", lang="en")
        ttq7 = ODM.TranslatedText(_content="DOB Year", lang="en")
        desc7 = ODM.Description()
        desc7.TranslatedText = [ttd7]
        q7 = ODM.Question()
        q7.TranslatedText = [ttq7]
        itd7 = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="text")
        itd7.Description = desc7
        itd7.Question = q7
        # ItemDef 8
        ttd8 = ODM.TranslatedText(_content="Visit", lang="en")
        ttq8 = ODM.TranslatedText(_content="Visit", lang="en")
        desc8 = ODM.Description()
        desc8.TranslatedText = [ttd8]
        q8 = ODM.Question()
        q8.TranslatedText = [ttq8]
        itd8 = ODM.ItemDef(OID="ODM.IT.Common.Visit", Name="Visit", DataType="text")
        itd8.Description = desc8
        itd8.Question = q8
        # ItemDef 9
        ttd9 = ODM.TranslatedText(_content="Sex", lang="en")
        ttq9 = ODM.TranslatedText(_content="Sex", lang="en")
        desc9 = ODM.Description()
        desc9.TranslatedText = [ttd9]
        q9 = ODM.Question()
        q9.TranslatedText = [ttq9]
        itd9 = ODM.ItemDef(OID="ODM.IT.DM.SEX", Name="Sex", DataType="text")
        itd9.Description = desc9
        itd9.Question = q9
        # ItemDef 10
        ttd10 = ODM.TranslatedText(_content="Systolic Blood Pressure Result", lang="en")
        ttq10 = ODM.TranslatedText(_content="Systolic BP", lang="en")
        desc10 = ODM.Description()
        desc10.TranslatedText = [ttd10]
        q10 = ODM.Question()
        q10.TranslatedText = [ttq10]
        itd10 = ODM.ItemDef(OID="ODM.IT.VS.BP.SYSBP.VSORRES", Name="Systolic BP Result", DataType="text")
        itd10.Description = desc10
        itd10.Question = q10
        return [itd1, itd2, itd3, itd4, itd5, itd6, itd7, itd8, itd9, itd10]


    def add_ITD_nonunique(self):
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
        # ItemDef 3
        ttd3 = ODM.TranslatedText(_content="Adverse Event Term", lang="en")
        ttq3 = ODM.TranslatedText(_content="AE Term", lang="en")
        desc3 = ODM.Description()
        desc3.TranslatedText = [ttd3]
        q3 = ODM.Question()
        q3.TranslatedText = [ttq3]
        itd3 = ODM.ItemDef(OID="ODM.IT.AE.AETERM", Name="AE Term", DataType="text")
        itd3.Description = desc3
        itd3.Question = q3
        # ItemDef 4
        ttd4 = ODM.TranslatedText(_content="Adverse Event Severity", lang="en")
        ttq4 = ODM.TranslatedText(_content="AE Severity", lang="en")
        desc4 = ODM.Description()
        desc4.TranslatedText = [ttd4]
        q4 = ODM.Question()
        q4.TranslatedText = [ttq4]
        itd4 = ODM.ItemDef(OID="ODM.IT.AE.AESEV", Name="AE Severity", DataType="text")
        itd4.Description = desc4
        itd4.Question = q4
        # ItemDef 5
        ttd5 = ODM.TranslatedText(_content="Subject ID", lang="en")
        ttq5 = ODM.TranslatedText(_content="Subject ID", lang="en")
        desc5 = ODM.Description()
        desc5.TranslatedText = [ttd5]
        q5 = ODM.Question()
        q5.TranslatedText = [ttq5]
        itd5 = ODM.ItemDef(OID="ODM.IT.Common.SubjectID", Name="Subject ID", DataType="text")
        itd5.Description = desc5
        itd5.Question = q5
        # ItemDef 6
        ttd6 = ODM.TranslatedText(_content="Diastolic Blood Pressure Result", lang="en")
        ttq6 = ODM.TranslatedText(_content="Diastolic BP", lang="en")
        desc6 = ODM.Description()
        desc6.TranslatedText = [ttd6]
        q6 = ODM.Question()
        q6.TranslatedText = [ttq6]
        itd6 = ODM.ItemDef(OID="ODM.IT.VS.BP.SYSBP.VSORRES", Name="DBP Result", DataType="text")
        itd6.Description = desc6
        itd6.Question = q6
        # ItemDef 7
        ttd7 = ODM.TranslatedText(_content="Birth Year", lang="en")
        ttq7 = ODM.TranslatedText(_content="DOB Year", lang="en")
        desc7 = ODM.Description()
        desc7.TranslatedText = [ttd7]
        q7 = ODM.Question()
        q7.TranslatedText = [ttq7]
        itd7 = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="text")
        itd7.Description = desc7
        itd7.Question = q7
        # ItemDef 8
        ttd8 = ODM.TranslatedText(_content="Visit", lang="en")
        ttq8 = ODM.TranslatedText(_content="Visit", lang="en")
        desc8 = ODM.Description()
        desc8.TranslatedText = [ttd8]
        q8 = ODM.Question()
        q8.TranslatedText = [ttq8]
        itd8 = ODM.ItemDef(OID="ODM.IT.Common.Visit", Name="Visit", DataType="text")
        itd8.Description = desc8
        itd8.Question = q8
        # ItemDef 9
        ttd9 = ODM.TranslatedText(_content="Sex", lang="en")
        ttq9 = ODM.TranslatedText(_content="Sex", lang="en")
        desc9 = ODM.Description()
        desc9.TranslatedText = [ttd9]
        q9 = ODM.Question()
        q9.TranslatedText = [ttq9]
        itd9 = ODM.ItemDef(OID="ODM.IT.DM.SEX", Name="Sex", DataType="text")
        itd9.Description = desc9
        itd9.Question = q9
        # ItemDef 10
        ttd10 = ODM.TranslatedText(_content="Systolic Blood Pressure Result", lang="en")
        ttq10 = ODM.TranslatedText(_content="Systolic BP", lang="en")
        desc10 = ODM.Description()
        desc10.TranslatedText = [ttd10]
        q10 = ODM.Question()
        q10.TranslatedText = [ttq10]
        itd10 = ODM.ItemDef(OID="ODM.IT.VS.BP.SYSBP.VSORRES", Name="Systolic BP Result", DataType="text")
        itd10.Description = desc10
        itd10.Question = q10
        return [itd1, itd2, itd3, itd4, itd5, itd6, itd7, itd8, itd9, itd10]

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


