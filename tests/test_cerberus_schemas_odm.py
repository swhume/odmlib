from unittest import TestCase
import cerberus as C
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA
import odmlib.odm_1_3_2.rules.oid_ref as OID


class CheckODM:
    def __init__(self, schema, doc):
        self.schema = schema
        self.doc = doc

    def check_odm(self):
        v = C.Validator(self.schema)
        is_valid = v.validate(self.doc)
        return is_valid


class TestCheckODM(TestCase):
    def setUp(self):
        self.validator = METADATA.MetadataSchema()

    def test_TranslatedText(self):
        schema = {"lang": {"type": "string"}, "_content": {"type": "string"}}
        doc = {"lang": "en", "_content": "hello, world"}
        check = CheckODM(schema, doc)
        is_valid = check.check_odm()
        self.assertTrue(is_valid)

    def test_Alias(self):
        schema = {"Context": {"type": "string", "required": True}, "Name": {"type": "string", "required": True}}
        doc = {"Context": "nci:ExtCodeID", "Name": "C64848"}
        check = CheckODM(schema, doc)
        is_valid = check.check_odm()
        self.assertTrue(is_valid)

    def test_Description(self):
        schema = {"TranslatedText": {"type": "list", "schema": {
            "type": "dict", "schema": {"lang": {"type": "string"}, "_content": {"type": "string", "required": True}}}}}
        doc = {'TranslatedText': [{'_content': 'Trace-XML Test CDASH File', 'lang': 'en'}]}
        check = CheckODM(schema, doc)
        is_valid = check.check_odm()
        self.assertTrue(is_valid)

    def test_Protocol(self):
        p = ODM.Protocol()
        tt = ODM.TranslatedText(_content="Trace-XML Test CDASH File", lang="en")
        p.Description = ODM.Description()
        p.Description.TranslatedText = [tt]
        ser1 = ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber="1", Mandatory="Yes")
        ser2 = ODM.StudyEventRef(StudyEventOID="FOLLOW-UP", OrderNumber="2", Mandatory="Yes")
        p.StudyEventRef = [ser1, ser2]
        p.Alias = [ODM.Alias(Context="ClinicalTrials.gov", Name="trace-protocol")]
        description_dict = p.Description.to_dict()
        print(description_dict)
        is_valid = self.validator.verify_conformance(description_dict, "Description")
        self.assertTrue(is_valid)
        protocol_dict = p.to_dict()
        print(protocol_dict)
        is_valid = self.validator.verify_conformance(protocol_dict, "Protocol")
        self.assertTrue(is_valid)

    def test_StudEventDef(self):
        attrs = {"OID": "ODM.SE.BASELINE", "Name": "Baseline Visit", "Repeating": "No", "Type": "Scheduled",
         "Category": "Pre-treatment"}
        sed = ODM.StudyEventDef(**attrs)
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        sed.Description = ODM.Description()
        sed.Description.TranslatedText = [tt1]
        fr1 = ODM.FormRef(FormOID="ODM.F.VS", Mandatory="Yes", OrderNumber="1")
        fr2 = ODM.FormRef(FormOID="ODM.F.DM", Mandatory="Yes", OrderNumber="2")
        fr3 = ODM.FormRef(FormOID="ODM.F.MH", Mandatory="Yes", OrderNumber="3")
        sed.FormRef = [fr1, fr2, fr3]
        a1 = ODM.Alias(Context="SDTMIG", Name="VS")
        a2 = ODM.Alias(Context="CDASHIG", Name="VS")
        sed.Alias = [a1, a2]
        sed_dict = sed.to_dict()
        print(sed_dict)
        is_valid = self.validator.verify_conformance(sed_dict, "StudyEventDef")
        self.assertTrue(is_valid)

    def test_FormDef(self):
        formdef = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs Form", Repeating="Yes")
        tt1 = ODM.TranslatedText(_content="this is the first test description", lang="en")
        formdef.Description = ODM.Description()
        formdef.Description.TranslatedText = [tt1]
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber="1")
        formdef.ItemGroupRef.append(igr)
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber="2")
        formdef.ItemGroupRef.append(igr)
        igr = ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber="3")
        formdef.ItemGroupRef.append(igr)
        formdef.Alias.append(ODM.Alias(Context="SDTMIG", Name="VS"))
        fd_dict = formdef.to_dict()
        print(fd_dict)
        is_valid = self.validator.verify_conformance(fd_dict, "FormDef")
        self.assertTrue(is_valid)

    def test_ItemGroupDef(self):
        attrs = {"OID": "IG.VS", "Name": "VS", "Repeating": "Yes", "Domain": "VS", "Name": "VS", "SASDatasetName": "VS",
                "IsReferenceData": "No", "Purpose": "Tabulation"}
        igd = ODM.ItemGroupDef(**attrs)
        tt = ODM.TranslatedText(_content="this is the first test description", lang="en")
        igd.Description = ODM.Description()
        igd.Description.TranslatedText = [tt]
        ir1 = ODM.ItemRef(ItemOID="IT.STUDYID", Mandatory="Yes", OrderNumber="1")
        ir2 = ODM.ItemRef(ItemOID="IT.VS.VSTEST", Mandatory="No", OrderNumber="2")
        igd.ItemRef = [ir1, ir2]
        igd_dict = igd.to_dict()
        print(igd_dict)
        is_valid = self.validator.verify_conformance(igd_dict, "ItemGroupDef")
        self.assertTrue(is_valid)

    def test_RangeCheck(self):
        rc = ODM.RangeCheck(Comparator="EQ", SoftHard="Soft")
        tt1 = ODM.TranslatedText(_content="invalid test code", lang="en")
        tt2 = ODM.TranslatedText(_content="code de test invalide", lang="fr")
        rc.ErrorMessage.TranslatedText = [tt1, tt2]
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        rc_dict = rc.to_dict()
        print(rc_dict)
        is_valid = self.validator.verify_conformance(rc_dict, "RangeCheck")
        self.assertTrue(is_valid)

    def test_ItemDef(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": "1", "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field"}
        item = ODM.ItemDef(**attrs)
        item.Description.TranslatedText = [ODM.TranslatedText(_content="this is the first test description", lang="en")]
        item.Question.TranslatedText = [ODM.TranslatedText(_content="Any AEs?", lang="en")]
        item.CodeListRef = ODM.CodeListRef(CodeListOID="CL.NY_SUB_Y_N_2011-10-24")
        item_dict = item.to_dict()
        print(item_dict)
        is_valid = self.validator.verify_conformance(item_dict, "ItemDef")
        self.assertTrue(is_valid)

    def test_CodeListItem(self):
        cli = ODM.CodeListItem(CodedValue="HGB", OrderNumber="1")
        tt1 = ODM.TranslatedText(_content="Hemoglobin", lang="en")
        decode = ODM.Decode()
        decode.TranslatedText.append(tt1)
        cli.Decode = decode
        cli.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C64848"))
        cli_dict = cli.to_dict()
        print(cli_dict)
        is_valid = self.validator.verify_conformance(cli_dict, "CodeListItem")
        self.assertTrue(is_valid)

    def test_CodeList(self):
        attrs = {"OID": "ODM.CL.LBTESTCD", "Name": "Laboratory Test Code", "DataType": "text"}
        cl = ODM.CodeList(**attrs)
        eni = ODM.EnumeratedItem(CodedValue="HGB", OrderNumber=1)
        eni.Alias = [ODM.Alias(Context="nci:ExtCodeID", Name="C64848")]
        cl.EnumeratedItem.append(eni)
        eni.Alias.append(ODM.Alias(Context="nci:ExtCodeID", Name="C65047"))
        cl_dict = cl.to_dict()
        print(cl_dict)
        is_valid = self.validator.verify_conformance(cl_dict, "CodeList")
        self.assertTrue(is_valid)

    def test_ExternalCodeList(self):
        attrs = {"OID": "ODM.CL.LBTESTCD", "Name": "Laboratory Test Code", "DataType": "text"}
        cl = ODM.CodeList(**attrs)
        excl = ODM.ExternalCodeList(Dictionary="MedDRA", Version="23.0", href="https://www.meddra.org/")
        cl.ExternalCodeList = excl
        cl_dict = cl.to_dict()
        is_valid = self.validator.verify_conformance(cl_dict, "CodeList")
        self.assertTrue(is_valid)

    def test_ConditionDef(self):
        attrs = {"OID": "ODM.CD.BRTHMO", "Name": "Skip BRTHMO when no BRTHYR"}
        cd = ODM.ConditionDef(**attrs)
        cd.Description = ODM.Description()
        cd.Description.TranslatedText = [ODM.TranslatedText(_content="Skip the BRTHMO field when BRTHYR length NE 4", lang="en")]
        cd.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="BRTHYR != 4")]
        cd_dict = cd.to_dict()
        print(cd_dict)
        is_valid = self.validator.verify_conformance(cd_dict, "ConditionDef")
        self.assertTrue(is_valid)

    def test_MethodDef(self):
        attrs = {"OID": "ODM.MT.AGE", "Name": "Algorithm to derive AGE", "Type": "Computation"}
        method = ODM.MethodDef(**attrs)
        desc = ODM.Description()
        tt1 = ODM.TranslatedText(_content="Age at Screening Date (Screening Date - Birth date)", lang="en")
        desc.TranslatedText = [tt1]
        method.Description = desc
        fex = ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")
        method.FormalExpression = [fex]
        method_dict = method.to_dict()
        print(method_dict)
        is_valid = self.validator.verify_conformance(method_dict, "MethodDef")
        self.assertTrue(is_valid)

    def test_OID_unique(self):
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
        oid_checker = OID.OIDRef()
        self.mdv.verify_oids(oid_checker)
        self.assertTrue(oid_checker.check_oid_refs())

    def test_unused_OID(self):
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
        oid_checker = OID.OIDRef()
        self.mdv.verify_oids(oid_checker)
        orphans = oid_checker.check_unreferenced_oids()
        print(orphans)
        expected_orphans = {'MDV.TRACE-XML-ODM-01': 'MetaDataVersionOID', 'ODM.IT.VS.BP.VSORRESU': 'ItemOID',
                            'ODM.CL.NY_SUB_Y_N': 'CodeListOID', 'ODM.MT.DOB': 'MethodOID',
                            'ODM.CD.BRTHMO': 'CollectionExceptionConditionOID'}
        self.assertDictEqual(orphans, expected_orphans)

    def test_MetaDataVersion(self):
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
        mdv_dict = self.mdv.to_dict()
        print(mdv_dict)
        is_valid = self.validator.verify_conformance(mdv_dict, "MetaDataVersion")
        self.assertTrue(is_valid)

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
