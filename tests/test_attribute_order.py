import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA


class TestAttributeOrder(unittest.TestCase):
    def setUp(self):
        self.validator = METADATA.MetadataSchema()

    def test_study_invalid_study_object(self):
        study = ODM.Study(OID="ST.001.Test")
        # StudyName is a child of GLobalVariables, not of Study
        with self.assertRaises(TypeError):
            study.StudyName = ODM.StudyName(_content="The ODM study name")

    def test_study_invalid_study_object_assignment(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        with self.assertRaises(TypeError):
            study.GlobalVariables.StudyName = ODM.ProtocolName(_content="The ODM protocol name")

    def test_valid_order_study_objects(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        self.assertTrue(study.verify_order())

    def test_invalid_order_study_objects(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        with self.assertRaises(ValueError):
            study.verify_order()

    def test_odm_order_incomplete(self):
        attrs = self.get_root_attributes()
        odm = ODM.ODM(**attrs)
        odm.Study.append(ODM.Study(OID="ST.001.Test"))
        odm.Study[0].GlobalVariables = ODM.GlobalVariables()
        odm.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        odm.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        odm.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        attrs = self.get_mdv_attributes()
        odm.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(**attrs))
        odm.Study[0].verify_order()

    def test_odm_order_multiple(self):
        attrs = self.get_root_attributes()
        odm = ODM.ODM(**attrs)
        odm.Study.append(ODM.Study(OID="ST.001.Test"))
        odm.Study[0].GlobalVariables = ODM.GlobalVariables()
        odm.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        odm.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        odm.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        attrs = self.get_mdv_attributes()
        odm.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(**attrs))
        fd1 = ODM.FormDef(OID="ODM.F.VS", Name="Vital Signs Form", Repeating="Yes")
        fd1.Description = ODM.Description()
        fd1.Description.TranslatedText.append(ODM.TranslatedText(lang="en", _content="this is the test description"))
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.COMMON", Mandatory="Yes", OrderNumber=1))
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS_GENERAL", Mandatory="Yes", OrderNumber=2))
        fd1.ItemGroupRef.append(ODM.ItemGroupRef(ItemGroupOID="ODM.IG.VS", Mandatory="Yes", OrderNumber=3))
        fd2 = ODM.FormDef(OID="ODM.F.DM", Name="Demographics Form", Repeating="No")
        fd3 = ODM.FormDef(OID="ODM.F.AE", Name="Adverse Events Form", Repeating="Yes")
        odm.Study[0].MetaDataVersion[0].FormDef = [fd1, fd2, fd3]
        odm.Study[0].verify_order()

    def test_odm_order_itemdef(self):
        # create an ItemDef
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
        itd.Question = ODM.Question()
        itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
        self.assertTrue(itd.verify_order())

    def test_odm_order_itemdef_invalid(self):
        # create an ItemDef
        attrs = self.get_root_attributes()
        odm = ODM.ODM(**attrs)
        odm.Study.append(ODM.Study(OID="ST.001.Test"))
        odm.Study[0].GlobalVariables = ODM.GlobalVariables()
        odm.Study[0].GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        odm.Study[0].GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        odm.Study[0].GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        attrs = self.get_mdv_attributes()
        odm.Study[0].MetaDataVersion.append(ODM.MetaDataVersion(**attrs))
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
        itd.Question = ODM.Question()
        itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
        odm.Study[0].MetaDataVersion[0].ItemDef.append(itd)
        with self.assertRaises(ValueError):
            self.assertTrue(odm.Study[0].MetaDataVersion[0].verify_order())

    def test_reordering_object(self):
        itd = ODM.ItemDef(OID="ODM.IT.DM.BRTHYR", Name="Birth Year", DataType="integer")
        itd.Alias.append(ODM.Alias(Context="CDASH", Name="BRTHYR"))
        itd.Alias.append(ODM.Alias(Context="SDTM", Name="BRTHDTC"))
        itd.Description = ODM.Description()
        itd.Description.TranslatedText.append(ODM.TranslatedText(_content="Year of the subject's birth", lang="en"))
        itd.Question = ODM.Question()
        itd.Question.TranslatedText.append(ODM.TranslatedText(_content="Birth Year", lang="en"))
        with self.assertRaises(ValueError):
            itd.verify_order()
        itd.reorder_object()
        self.assertTrue(itd.verify_order())

    def test_reorder_study_objects(self):
        study = ODM.Study(OID="ST.001.Test")
        study.GlobalVariables = ODM.GlobalVariables()
        study.GlobalVariables.ProtocolName = ODM.ProtocolName(_content="The ODM protocol name")
        study.GlobalVariables.StudyName = ODM.StudyName(_content="The ODM study name")
        study.GlobalVariables.StudyDescription = ODM.StudyDescription(_content="The description of the ODM study")
        with self.assertRaises(ValueError):
            study.verify_order()
        study.GlobalVariables.reorder_object()
        self.assertTrue(study.verify_order())

    def test_reorder_mdv_object(self):
        attrs = self.get_mdv_attributes()
        mdv = ODM.MetaDataVersion(**attrs)
        mdv.StudyEventDef = self.add_SED()
        mdv.FormDef = self.add_FD()
        mdv.ItemGroupDef = self.add_IGD()
        mdv.ItemDef = self.add_ITD()
        self.assertTrue(mdv.verify_order())
        mdv2 = ODM.MetaDataVersion(**attrs)
        mdv2.StudyEventDef = self.add_SED()
        mdv2.ItemDef = self.add_ITD()
        mdv2.ItemGroupDef = self.add_IGD()
        mdv2.FormDef = self.add_FD()
        with self.assertRaises(ValueError):
            mdv2.verify_order()
        mdv2.reorder_object()
        self.assertTrue(mdv2.verify_order())

    def test_reorder_mdv_protocol_objects(self):
        attrs = self.get_mdv_attributes()
        mdv = ODM.MetaDataVersion(**attrs)
        mdv.Protocol = self.add_protocol()
        mdv.MethodDef = self.add_MD()
        mdv.StudyEventDef = self.add_SED()
        mdv.FormDef = self.add_FD()
        mdv.CodeList = self.add_CL()
        mdv.ItemGroupDef = self.add_IGD()
        mdv.ItemDef = self.add_ITD()
        # test mdv order
        with self.assertRaises(ValueError):
            mdv.verify_order()
        mdv.reorder_object()
        # test protocol order
        with self.assertRaises(ValueError):
            mdv.verify_order()
        mdv.Protocol.reorder_object()
        self.assertTrue(mdv.verify_order())

    def get_mdv_attributes(self):
        return {"OID": "MDV.TRACE-XML-ODM-01", "Name": "TRACE-XML MDV", "Description": "Trace-XML Example"}

    def get_root_attributes(self):
        return {"FileOID": "ODM.MDV.TEST.001", "Granularity": "Metadata",
                 "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
                 "CreationDateTime": "2020-07-13T00:13:51.309617+00:00", "ODMVersion": "1.3.2", "FileType": "Snapshot",
                 "Originator": "RDS", "SourceSystem": "ODMLib", "SourceSystemVersion": "0.1",
                 "schemaLocation": "http://www.cdisc.org/ns/odm/v1.3 odm1-3-2.xsd"}

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

    def add_protocol(self):
        p = ODM.Protocol()
        # invalid order for protocol content to test re-order
        p.Alias = [ODM.Alias(Context="ClinicalTrials.gov", Name="trace-protocol")]
        tt = ODM.TranslatedText(_content="Trace-XML Test CDASH File", lang="en")
        p.Description = ODM.Description()
        p.Description.TranslatedText = [tt]
        ser1 = ODM.StudyEventRef(StudyEventOID="BASELINE", OrderNumber=1, Mandatory="Yes")
        ser2 = ODM.StudyEventRef(StudyEventOID="FOLLOW-UP", OrderNumber=2, Mandatory="Yes")
        p.StudyEventRef = [ser1, ser2]
        return p
