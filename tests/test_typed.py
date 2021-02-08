import unittest
import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as METADATA
import datetime
import odmlib.typed as T
import odmlib.odm_element as OE


class TestText(OE.ODMElement):
    Name = T.String(required=True)
    Label = T.Sized(required=True, max_length=4)
    Range = T.Regex(required=False, pat="[0-4]-[0-9]")
    Link = T.Url(required=False)
    TestDateTime = T.IncompleteDateTimeString(required=False)
    TestDate = T.IncompleteDateString(required=False)
    TestTime = T.IncompleteTimeString(required=False)


class TestPartialDate(OE.ODMElement):
    Name = T.String(required=True)
    TestDateTime = T.PartialDateTimeString(required=False)
    TestDate = T.PartialDateString(required=False)
    TestTime = T.PartialTimeString(required=False)


class TestTyped(unittest.TestCase):
    def test_integer_type(self):
        # order number is an integer - test as an integer
        attrs = {"CodedValue": "HGB", "OrderNumber": 1}
        cli = ODM.CodeListItem(**attrs)
        self.assertEqual(cli.OrderNumber, 1)
        # test integer as string
        attrs = {"CodedValue": "HGB", "OrderNumber": "1"}
        cli = ODM.CodeListItem(**attrs)
        self.assertEqual(cli.OrderNumber, 1)
        # test integer as float
        attrs = {"CodedValue": "HGB", "OrderNumber": 1.1}
        with self.assertRaises(TypeError):
            cli = ODM.CodeListItem(**attrs)
        # test non-integer as
        attrs = {"CodedValue": "HGB", "OrderNumber": "a"}
        with self.assertRaises(TypeError):
            cli = ODM.CodeListItem(**attrs)

    def test_float_type(self):
        # rank is a float - test as a float
        attrs = {"CodedValue": "HGB", "Rank": 1.1}
        cli = ODM.CodeListItem(**attrs)
        self.assertEqual(cli.Rank, 1.1)
        # test float as string
        attrs = {"CodedValue": "HGB", "Rank": "1.1"}
        cli = ODM.CodeListItem(**attrs)
        self.assertEqual(cli.Rank, 1.1)
        # test integer as float
        attrs = {"CodedValue": "HGB", "Rank": 1}
        cli = ODM.CodeListItem(**attrs)
        self.assertEqual(cli.Rank, 1.0)
        # test non-float as string
        attrs = {"CodedValue": "HGB", "Rank": "a"}
        with self.assertRaises(TypeError):
            cli = ODM.CodeListItem(**attrs)
        # test object as float
        clr = ODM.CodeListRef(CodeListOID="CL.TEST")
        attrs = {"CodedValue": "HGB", "Rank": clr}
        with self.assertRaises(TypeError):
            cli = ODM.CodeListItem(**attrs)

    def test_positive_type(self):
        # testing Length as a positive integer
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field"}
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.Length, 1)
        # testing Length = 0 as a positive integer
        attrs["Length"] = 0
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        # testing Length = -1 as a positive integer
        attrs["Length"] = -1
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        # testing Length = float as a positive integer
        attrs["Length"] = 1.0
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)

    def test_non_negative_type(self):
        # testing SignificantDigits as a non-negative integer
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "SignificantDigits": 1}
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.SignificantDigits, 1)
        # testing SignificantDigits = 0 as a non-negative integer
        attrs["SignificantDigits"] = 0
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.SignificantDigits, 0)
        # testing SignificantDigits = -1 as a non-negative integer
        attrs["SignificantDigits"] = -1
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        # testing SignificantDigits = float as a non-negative integer
        attrs["SignificantDigits"] = 1.0
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)

    def test_add_undefined_content(self):
        # use conformance rules to check for unknown objects being added after creation
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "SignificantDigits": 1}
        item = ODM.ItemDef(**attrs)
        clr = ODM.CodeListRef(CodeListOID="CL.TEST")
        with self.assertRaises(TypeError):
            item.NewCodeList = clr
        # cannot add unknown attributes or elements during creation, but can afterwards; catch with conformance checks
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "SignificantDigits": 1}
        item = ODM.ItemDef(**attrs)
        with self.assertRaises(TypeError):
            item.InSignificantDigits = 1
        # can add all objects during creation and they are validated
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "CodeListRef": clr}
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.CodeListRef, clr)
        attrs["CodeListReference"] = clr
        with self.assertRaises(TypeError):
            # test shows that ItemDef fails the schema check because it has an unknown CodeListReference object
            item = ODM.ItemDef(**attrs)
        self.assertEqual(item.CodeListRef, clr)
        # test adding the wrong type of object to a list
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "Alias": [clr]}
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        # test adding the wrong type of object to a list
        alias = ODM.Alias(Context="CDASH", Name="AEYN")
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "Alias": alias}
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        # assign wrong type of object to an element
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "CodeListRef": alias}
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)

    def test_email_type(self):
        # good email
        email = ODM.Email(_content="swhume@gmail.com")
        self.assertEqual(email._content, "swhume@gmail.com")
        # missing @
        with self.assertRaises(ValueError):
            email = ODM.Email(_content="swhumegmail.com")
        # includes a space
        with self.assertRaises(ValueError):
            email = ODM.Email(_content="swhume @gmail.com")

    def test_sasformat_type(self):
        attrs = {"OID": "ODM.CL.LBTESTCD", "Name": "Laboratory Test Code", "DataType": "text",
                 "SASFormatName": "$AETERM"}
        cl = ODM.CodeList(**attrs)
        self.assertEqual(cl.SASFormatName, "$AETERM")
        # start with an underscore
        attrs["SASFormatName"] = "_AETERM"
        cl = ODM.CodeList(**attrs)
        self.assertEqual(cl.SASFormatName, "_AETERM")
        # start with a number
        attrs["SASFormatName"] = "9AETERM"
        with self.assertRaises(ValueError):
            cl = ODM.CodeList(**attrs)
        # end with a symbol
        attrs["SASFormatName"] = "AETERM%"
        with self.assertRaises(ValueError):
            cl = ODM.CodeList(**attrs)
        # test with none - does not throw an error when value is None
        attrs["SASFormatName"] = None
        cl = ODM.CodeList(**attrs)
        self.assertIsNone(cl.SASFormatName)

    def test_sasname_type(self):
        # valid test
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "SignificantDigits": 1}
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.SASFieldName, "AEYN")
        # start with an underscore
        attrs["SASFieldName"] = "_AETERM"
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.SASFieldName, "_AETERM")
        # start with a number
        attrs["SASFieldName"] = "9AETERM"
        with self.assertRaises(ValueError):
            item = ODM.ItemDef(**attrs)
        # end with a symbol
        attrs["SASFieldName"] = "AETERM%"
        with self.assertRaises(ValueError):
            item = ODM.ItemDef(**attrs)
        # test with none - does not throw an error when value is None
        attrs["SASFieldName"] = None
        item = ODM.ItemDef(**attrs)
        self.assertIsNone(item.SASFieldName)

    def test_datetime_type(self):
        attrs = {"FileOID": "ODM.MDV.TEST.001", "Granularity": "Metadata",
                 "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
                 "CreationDateTime": "2020-07-13T00:13:51.309617+00:00",
                 "ODMVersion": "1.3.2", "FileType": "Snapshot", "Originator": "RDS", "SourceSystem": "ODMLib"}
        odm = ODM.ODM(**attrs)
        self.assertEqual(odm.AsOfDateTime, "2020-07-13T00:13:51.309617+00:00")
        # derived current datetime in ISO formate from datetime library
        attrs["AsOfDateTime"] = self.set_datetime()
        odm = ODM.ODM(**attrs)
        self.assertIsInstance(odm, ODM.ODM)
        # date only
        attrs["AsOfDateTime"] = "2020-07-13"
        with self.assertRaises(ValueError):
            odm = ODM.ODM(**attrs)
        # basic time
        attrs["AsOfDateTime"] = "2020-07-13T00:13:51"
        odm = ODM.ODM(**attrs)
        self.assertEqual(odm.AsOfDateTime, "2020-07-13T00:13:51")
        # out of range time
        attrs["AsOfDateTime"] = "2020-07-13T00:13:61"
        with self.assertRaises(ValueError):
            odm = ODM.ODM(**attrs)

    def set_datetime(self):
        """return the current datetime in ISO 8601 format"""
        return datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat()

    def test_string_type(self):
        attrs = {"OID": "ODM.IT.AE.AEYN", "Name": "Any AEs?", "DataType": "text", "Length": 1, "SASFieldName": "AEYN",
                "SDSVarName": "AEYN", "Origin": "CRF", "Comment": "Data management field", "SignificantDigits": 1}
        item = ODM.ItemDef(**attrs)
        self.assertEqual(item.Origin, "CRF")
        # integer
        attrs["Origin"] = 1
        with self.assertRaises(TypeError):
            item = ODM.ItemDef(**attrs)
        attrs["Origin"] = None
        item = ODM.ItemDef(**attrs)
        self.assertIsNone(item.Origin)

    def test_sized_type(self):
        sized = TestText(Name="AETERM", Label="help")
        self.assertEqual(sized.Label, "help")
        # too long
        with self.assertRaises(ValueError):
            sized = TestText(Name="AETERM", Label="Verbatim Term")

    def test_regex_type(self):
        regex = TestText(Name="AETERM", Label="help", Range="4-9")
        self.assertEqual(regex.Range, "4-9")
        # not a match
        with self.assertRaises(ValueError):
            regex = TestText(Name="AETERM", Label="help", Range="6-7")

    def test_url_type(self):
        url = TestText(Name="AETERM", Label="help", Range="4-9", Link="https://cdisc.org")
        self.assertEqual(url.Link, "https://cdisc.org")
        # not a match
        with self.assertRaises(ValueError):
            url = TestText(Name="AETERM", Label="help", Range="4-9", Link="cdisc.org")

    def test_filename_type(self):
        archive = ODM.ArchiveLayout(OID="AL.AECRF", PdfFileName="ae_annotated_crf.pdf")
        self.assertEqual(archive.PdfFileName, "ae_annotated_crf.pdf")
        # with path
        with self.assertRaises(ValueError):
            archive = ODM.ArchiveLayout(OID="AL.AECRF", PdfFileName="c:\\users\\shume\\ae_annotated_crf.pdf")
        # with space
        archive = ODM.ArchiveLayout(OID="AL.AECRF", PdfFileName="ae_annotated crf.pdf")
        self.assertEqual(archive.PdfFileName, "ae_annotated crf.pdf")
        # with invalid character
        with self.assertRaises(ValueError):
            archive = ODM.ArchiveLayout(OID="AL.AECRF", PdfFileName="ae_annotated>crf.pdf")

    def test_incomplete_datetime_type(self):
        # valid incomplete datetime 2004-12-01T01:01:01Z and 2004---15T-:05:-
        idatetime = TestText(Name="AETERM", Label="help", Range="4-9", TestDateTime="2004-12-01T01:01:01Z")
        self.assertEqual(idatetime.TestDateTime, "2004-12-01T01:01:01Z")
        idatetime = TestText(Name="AETERM", Label="help", Range="4-9", TestDateTime="2004---15T-:05:-")
        self.assertEqual(idatetime.TestDateTime, "2004---15T-:05:-")
        # invalid incomplete datetime
        with self.assertRaises(ValueError):
            idatetime = TestText(Name="AETERM", Label="help", Range="4-7", TestDateTime="2004---15T-:05")

    def test_incomplete_date_type(self):
        # valid incomplete date 2004-12-20 and 2004---15 and ------
        idate = TestText(Name="AETERM", Label="help", Range="4-9", TestDate="2004-12-20")
        self.assertEqual(idate.TestDate, "2004-12-20")
        idate = TestText(Name="AETERM", Label="help", Range="4-9", TestDate="2004---15")
        self.assertEqual(idate.TestDate, "2004---15")
        idate = TestText(Name="AETERM", Label="help", Range="4-7", TestDate="-----")
        self.assertEqual(idate.TestDate, "-----")
        # invalid incomplete date
        with self.assertRaises(ValueError):
            idate = TestText(Name="AETERM", Label="help", Range="4-7", TestDate="----32")

    def test_incomplete_time_type(self):
        # valid incomplete time 2004-12-01T01:01:01Z and 2004---15T-:05:-
        itime = TestText(Name="AETERM", Label="help", Range="4-9", TestTime="01:01:01Z")
        self.assertEqual(itime.TestTime, "01:01:01Z")
        itime = TestText(Name="AETERM", Label="help", Range="4-9", TestTime="-:05:-")
        self.assertEqual(itime.TestTime, "-:05:-")
        # invalid incomplete datetime
        with self.assertRaises(ValueError):
            itime = TestText(Name="AETERM", Label="help", Range="4-7", TestTime="-:05")

    def test_partial_datetime_type(self):
        # valid partial datetime
        pdatetime = TestPartialDate(Name="AETERM", TestDateTime="2004-12-01T01:01:01Z")
        self.assertEqual(pdatetime.TestDateTime, "2004-12-01T01:01:01Z")
        pdatetime = TestPartialDate(Name="AETERM", TestDateTime="2004-12")
        self.assertEqual(pdatetime.TestDateTime, "2004-12")
        pdatetime = TestPartialDate(Name="AETERM", TestDateTime="2004-12-05T12")
        self.assertEqual(pdatetime.TestDateTime, "2004-12-05T12")
        # invalid partial datetime
        with self.assertRaises(ValueError):
            pdatetime = TestText(Name="AETERM", TestDateTime="2004---15T-:05")

    def test_partial_date_type(self):
        # valid partial date
        pdate = TestPartialDate(Name="AETERM", TestDate="2004-12-20")
        self.assertEqual(pdate.TestDate, "2004-12-20")
        pdate = TestPartialDate(Name="AETERM", TestDate="2004-12")
        self.assertEqual(pdate.TestDate, "2004-12")
        pdate = TestPartialDate(Name="AETERM", TestDate="2004")
        self.assertEqual(pdate.TestDate, "2004")
        # invalid partial date
        with self.assertRaises(ValueError):
            pdate = TestPartialDate(Name="AETERM", TestDate="----20")
        with self.assertRaises(ValueError):
            pdate = TestPartialDate(Name="AETERM", TestDate="2004-13-20")

    def test_partial_time_type(self):
        # valid partial time
        ptime = TestPartialDate(Name="AETERM", TestTime="01:01:01Z")
        self.assertEqual(ptime.TestTime, "01:01:01Z")
        ptime = TestPartialDate(Name="AETERM", TestTime="12:05")
        self.assertEqual(ptime.TestTime, "12:05")
        ptime = TestPartialDate(Name="AETERM", TestTime="12")
        self.assertEqual(ptime.TestTime, "12")
        # invalid partial datetime
        with self.assertRaises(ValueError):
            ptime = TestPartialDate(Name="AETERM", TestTime="-:05")
