"""Tests for the CT-XML 1.1.1 model (odmlib.ct_1_1_1).

CT-XML extends ODM with NCI EVS terminology elements under the nciodm
namespace.  These are the first tests for this model package.
"""
import json
from unittest import TestCase
import odmlib.ct_1_1_1.model as CT
import odmlib.ns_registry as NS
from odmlib.exceptions import OdmlibTypeError


def _setup_ct_namespaces():
    """Register the namespaces used by CT-XML 1.1.1."""
    NS.NamespaceRegistry(
        prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True,
    )
    NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
    NS.NamespaceRegistry(prefix="xs",     uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml",    uri="http://www.w3.org/XML/1998/namespace")


# ---------------------------------------------------------------------------
# TranslatedText
# ---------------------------------------------------------------------------

class TestCTTranslatedText(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create(self):
        tt = CT.TranslatedText(_content="Test text", lang="en")
        self.assertEqual(tt._content, "Test text")
        self.assertEqual(tt.lang, "en")

    def test_to_xml(self):
        tt = CT.TranslatedText(_content="Preferred Term Text", lang="en")
        elem = tt.to_xml()
        self.assertEqual(elem.text, "Preferred Term Text")
        # xml:lang attribute is stored with namespace prefix
        self.assertIn("lang", str(elem.attrib))

    def test_to_json(self):
        tt = CT.TranslatedText(_content="English text", lang="en")
        data = json.loads(tt.to_json())
        self.assertEqual(data["_content"], "English text")
        self.assertEqual(data["lang"], "en")

    def test_to_dict(self):
        tt = CT.TranslatedText(_content="Dict text", lang="fr")
        d = tt.to_dict()
        self.assertEqual(d["_content"], "Dict text")
        self.assertEqual(d["lang"], "fr")


# ---------------------------------------------------------------------------
# Alias
# ---------------------------------------------------------------------------

class TestCTAlias(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create(self):
        alias = CT.Alias(Context="CDISC", Name="C123456")
        self.assertEqual(alias.Context, "CDISC")
        self.assertEqual(alias.Name, "C123456")

    def test_to_xml(self):
        alias = CT.Alias(Context="CDISC", Name="C123456")
        elem = alias.to_xml()
        self.assertEqual(elem.attrib["Context"], "CDISC")
        self.assertEqual(elem.attrib["Name"], "C123456")

    def test_to_json(self):
        alias = CT.Alias(Context="CDISC", Name="C123456")
        data = json.loads(alias.to_json())
        self.assertEqual(data["Context"], "CDISC")
        self.assertEqual(data["Name"], "C123456")


# ---------------------------------------------------------------------------
# GlobalVariables components
# ---------------------------------------------------------------------------

class TestCTStudyName(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create(self):
        sn = CT.StudyName(_content="SDTM CT 2023-09-29")
        self.assertEqual(sn._content, "SDTM CT 2023-09-29")

    def test_to_xml(self):
        sn = CT.StudyName(_content="CT Study")
        elem = sn.to_xml()
        self.assertEqual(elem.text, "CT Study")


class TestCTGlobalVariables(TestCase):
    def setUp(self):
        _setup_ct_namespaces()
        self.sn = CT.StudyName(_content="SDTM CT")
        self.sd = CT.StudyDescription(_content="SDTM Controlled Terminology")
        self.pn = CT.ProtocolName(_content="SDTM CT Protocol")

    def test_create(self):
        gv = CT.GlobalVariables(
            StudyName=self.sn,
            StudyDescription=self.sd,
            ProtocolName=self.pn,
        )
        self.assertEqual(gv.StudyName._content, "SDTM CT")
        self.assertEqual(gv.StudyDescription._content, "SDTM Controlled Terminology")
        self.assertEqual(gv.ProtocolName._content, "SDTM CT Protocol")

    def test_to_xml(self):
        gv = CT.GlobalVariables(
            StudyName=self.sn,
            StudyDescription=self.sd,
            ProtocolName=self.pn,
        )
        elem = gv.to_xml()
        self.assertEqual(elem.tag, "GlobalVariables")
        children = list(elem)
        self.assertEqual(len(children), 3)

    def test_to_json(self):
        gv = CT.GlobalVariables(
            StudyName=self.sn,
            StudyDescription=self.sd,
            ProtocolName=self.pn,
        )
        data = json.loads(gv.to_json())
        self.assertIn("StudyName", data)
        self.assertIn("StudyDescription", data)
        self.assertIn("ProtocolName", data)


# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------

class TestCTDescription(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create_with_translated_text(self):
        tt = CT.TranslatedText(_content="A test description", lang="en")
        desc = CT.Description(TranslatedText=[tt])
        self.assertEqual(len(desc.TranslatedText), 1)
        self.assertEqual(desc.TranslatedText[0]._content, "A test description")

    def test_to_xml(self):
        tt = CT.TranslatedText(_content="Description text", lang="en")
        desc = CT.Description(TranslatedText=[tt])
        elem = desc.to_xml()
        self.assertEqual(elem.tag, "Description")
        self.assertEqual(len(list(elem)), 1)


# ---------------------------------------------------------------------------
# nciodm content elements
# ---------------------------------------------------------------------------

class TestCTNciodmElements(TestCase):
    """Test the nciodm namespace content elements."""

    def setUp(self):
        _setup_ct_namespaces()

    def test_cdisc_synonym(self):
        syn = CT.CDISCSynonym(_content="SERIOUS AE")
        self.assertEqual(syn._content, "SERIOUS AE")

    def test_cdisc_definition(self):
        defn = CT.CDISCDefinition(_content="A serious adverse event.")
        self.assertEqual(defn._content, "A serious adverse event.")

    def test_cdisc_submission_value(self):
        sv = CT.CDISCSubmissionValue(_content="SAE")
        self.assertEqual(sv._content, "SAE")

    def test_preferred_term(self):
        pt = CT.PreferredTerm(_content="Serious Adverse Event")
        self.assertEqual(pt._content, "Serious Adverse Event")

    def test_preferred_term_to_json(self):
        pt = CT.PreferredTerm(_content="Serious Adverse Event")
        data = json.loads(pt.to_json())
        self.assertEqual(data["_content"], "Serious Adverse Event")


# ---------------------------------------------------------------------------
# EnumeratedItem
# ---------------------------------------------------------------------------

class TestCTEnumeratedItem(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create_minimal(self):
        """EnumeratedItem with all required fields."""
        defn = CT.CDISCDefinition(_content="Serious adverse event.")
        pt   = CT.PreferredTerm(_content="Serious Adverse Event")
        item = CT.EnumeratedItem(
            CodedValue="Y",
            ExtCodeID="C49488",
            CDISCDefinition=defn,
            PreferredTerm=pt,
        )
        self.assertEqual(item.CodedValue, "Y")
        self.assertEqual(item.ExtCodeID, "C49488")

    def test_with_synonyms(self):
        defn = CT.CDISCDefinition(_content="No.")
        pt   = CT.PreferredTerm(_content="No")
        syn  = CT.CDISCSynonym(_content="N")
        item = CT.EnumeratedItem(
            CodedValue="N",
            ExtCodeID="C49487",
            CDISCSynonym=[syn],
            CDISCDefinition=defn,
            PreferredTerm=pt,
        )
        self.assertEqual(len(item.CDISCSynonym), 1)
        self.assertEqual(item.CDISCSynonym[0]._content, "N")

    def test_to_json(self):
        defn = CT.CDISCDefinition(_content="Yes.")
        pt   = CT.PreferredTerm(_content="Yes")
        item = CT.EnumeratedItem(
            CodedValue="Y",
            ExtCodeID="C49488",
            CDISCDefinition=defn,
            PreferredTerm=pt,
        )
        data = json.loads(item.to_json())
        self.assertEqual(data["CodedValue"], "Y")
        self.assertEqual(data["ExtCodeID"], "C49488")

    def test_to_xml(self):
        defn = CT.CDISCDefinition(_content="Yes.")
        pt   = CT.PreferredTerm(_content="Yes")
        item = CT.EnumeratedItem(
            CodedValue="Y",
            ExtCodeID="C49488",
            CDISCDefinition=defn,
            PreferredTerm=pt,
        )
        elem = item.to_xml()
        self.assertEqual(elem.tag, "EnumeratedItem")
        self.assertEqual(elem.attrib["CodedValue"], "Y")


# ---------------------------------------------------------------------------
# CodeList
# ---------------------------------------------------------------------------

class TestCTCodeList(TestCase):
    def setUp(self):
        _setup_ct_namespaces()
        self.sv = CT.CDISCSubmissionValue(_content="NY")
        self.syn = CT.CDISCSynonym(_content="Yes or No Response")
        self.pt  = CT.PreferredTerm(_content="Yes No Response")

    def _make_codelist(self, **extra):
        return CT.CodeList(
            OID="CL.C66742.NYSRSP",
            Name="No Yes Response",
            DataType="text",
            ExtCodeID="C66742",
            CodeListExtensible="No",
            CDISCSubmissionValue=self.sv,
            CDISCSynonym=self.syn,
            PreferredTerm=self.pt,
            **extra,
        )

    def test_create(self):
        cl = self._make_codelist()
        self.assertEqual(cl.OID, "CL.C66742.NYSRSP")
        self.assertEqual(cl.Name, "No Yes Response")
        self.assertEqual(cl.DataType, "text")
        self.assertEqual(cl.ExtCodeID, "C66742")
        self.assertEqual(cl.CodeListExtensible, "No")

    def test_valid_data_types(self):
        for dtype in ("text", "integer", "float", "string"):
            cl = CT.CodeList(
                OID=f"CL.TEST.{dtype.upper()}",
                Name=f"Test {dtype}",
                DataType=dtype,
                ExtCodeID="C00000",
                CodeListExtensible="No",
                CDISCSubmissionValue=self.sv,
                CDISCSynonym=self.syn,
                PreferredTerm=self.pt,
            )
            self.assertEqual(cl.DataType, dtype)

    def test_with_enumerated_items(self):
        defn_y = CT.CDISCDefinition(_content="Yes.")
        pt_y   = CT.PreferredTerm(_content="Yes")
        defn_n = CT.CDISCDefinition(_content="No.")
        pt_n   = CT.PreferredTerm(_content="No")
        items = [
            CT.EnumeratedItem(CodedValue="Y", ExtCodeID="C49488", CDISCDefinition=defn_y, PreferredTerm=pt_y),
            CT.EnumeratedItem(CodedValue="N", ExtCodeID="C49487", CDISCDefinition=defn_n, PreferredTerm=pt_n),
        ]
        cl = self._make_codelist(EnumeratedItem=items)
        self.assertEqual(len(cl.EnumeratedItem), 2)
        self.assertEqual(cl.EnumeratedItem[0].CodedValue, "Y")
        self.assertEqual(cl.EnumeratedItem[1].CodedValue, "N")

    def test_to_xml(self):
        cl = self._make_codelist()
        elem = cl.to_xml()
        self.assertEqual(elem.tag, "CodeList")
        self.assertEqual(elem.attrib["OID"], "CL.C66742.NYSRSP")
        self.assertEqual(elem.attrib["Name"], "No Yes Response")
        self.assertEqual(elem.attrib["DataType"], "text")

    def test_to_json(self):
        cl = self._make_codelist()
        data = json.loads(cl.to_json())
        self.assertEqual(data["OID"], "CL.C66742.NYSRSP")
        self.assertEqual(data["DataType"], "text")
        self.assertEqual(data["ExtCodeID"], "C66742")

    def test_to_dict(self):
        cl = self._make_codelist()
        d = cl.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("OID", d)
        self.assertIn("Name", d)
        self.assertIn("DataType", d)

    def test_invalid_data_type_raises(self):
        with self.assertRaises(OdmlibTypeError):
            CT.CodeList(
                OID="CL.BAD", Name="Bad", DataType="bad_type",
                ExtCodeID="C00000", CodeListExtensible="No",
                CDISCSubmissionValue=self.sv, CDISCSynonym=self.syn, PreferredTerm=self.pt,
            )

    def test_invalid_extensible_raises(self):
        with self.assertRaises(OdmlibTypeError):
            CT.CodeList(
                OID="CL.BAD", Name="Bad", DataType="text",
                ExtCodeID="C00000", CodeListExtensible="Maybe",
                CDISCSubmissionValue=self.sv, CDISCSynonym=self.syn, PreferredTerm=self.pt,
            )


# ---------------------------------------------------------------------------
# MetaDataVersion
# ---------------------------------------------------------------------------

class TestCTMetaDataVersion(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create_minimal(self):
        mdv = CT.MetaDataVersion(OID="MDV.CT.SDTM.2023-09-29", Name="SDTM CT 2023-09-29")
        self.assertEqual(mdv.OID, "MDV.CT.SDTM.2023-09-29")
        self.assertEqual(mdv.Name, "SDTM CT 2023-09-29")

    def test_create_with_description(self):
        mdv = CT.MetaDataVersion(
            OID="MDV.CT.SDTM", Name="SDTM CT",
            Description="CDISC SDTM Controlled Terminology",
        )
        self.assertEqual(mdv.Description, "CDISC SDTM Controlled Terminology")

    def test_to_xml(self):
        mdv = CT.MetaDataVersion(OID="MDV.CT.SDTM", Name="SDTM CT")
        elem = mdv.to_xml()
        self.assertEqual(elem.tag, "MetaDataVersion")
        self.assertEqual(elem.attrib["OID"], "MDV.CT.SDTM")

    def test_to_json(self):
        mdv = CT.MetaDataVersion(OID="MDV.CT.SDTM", Name="SDTM CT")
        data = json.loads(mdv.to_json())
        self.assertEqual(data["OID"], "MDV.CT.SDTM")
        self.assertEqual(data["Name"], "SDTM CT")

    def test_add_codelists(self):
        sv  = CT.CDISCSubmissionValue(_content="NY")
        syn = CT.CDISCSynonym(_content="Yes No")
        pt  = CT.PreferredTerm(_content="Yes No Response")
        cl = CT.CodeList(
            OID="CL.C66742.NYSRSP", Name="No Yes Response",
            DataType="text", ExtCodeID="C66742", CodeListExtensible="No",
            CDISCSubmissionValue=sv, CDISCSynonym=syn, PreferredTerm=pt,
        )
        mdv = CT.MetaDataVersion(OID="MDV.CT.SDTM", Name="SDTM CT")
        mdv.CodeList.append(cl)
        self.assertEqual(len(mdv.CodeList), 1)
        self.assertEqual(mdv.CodeList[0].OID, "CL.C66742.NYSRSP")


# ---------------------------------------------------------------------------
# Study and ODM root
# ---------------------------------------------------------------------------

class TestCTStudy(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def test_create_minimal(self):
        sn = CT.StudyName(_content="SDTM CT")
        sd = CT.StudyDescription(_content="SDTM Controlled Terminology")
        pn = CT.ProtocolName(_content="SDTM CT Protocol")
        gv = CT.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)
        study = CT.Study(OID="S.CT.SDTM", GlobalVariables=gv)
        self.assertEqual(study.OID, "S.CT.SDTM")

    def test_to_xml(self):
        sn = CT.StudyName(_content="SDTM CT")
        sd = CT.StudyDescription(_content="SDTM CT Desc")
        pn = CT.ProtocolName(_content="SDTM CT Protocol")
        gv = CT.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)
        study = CT.Study(OID="S.CT.SDTM", GlobalVariables=gv)
        elem = study.to_xml()
        self.assertEqual(elem.tag, "Study")
        self.assertEqual(elem.attrib["OID"], "S.CT.SDTM")

    def test_add_metadata_version(self):
        sn = CT.StudyName(_content="SDTM CT")
        sd = CT.StudyDescription(_content="SDTM CT Desc")
        pn = CT.ProtocolName(_content="SDTM CT Protocol")
        gv = CT.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)
        mdv = CT.MetaDataVersion(OID="MDV.CT.SDTM", Name="SDTM CT")
        study = CT.Study(OID="S.CT.SDTM", GlobalVariables=gv, MetaDataVersion=[mdv])
        self.assertEqual(len(study.MetaDataVersion), 1)
        self.assertEqual(study.MetaDataVersion[0].OID, "MDV.CT.SDTM")


class TestCTODMRoot(TestCase):
    def setUp(self):
        _setup_ct_namespaces()

    def _make_minimal_ct(self):
        sn = CT.StudyName(_content="SDTM CT")
        sd = CT.StudyDescription(_content="SDTM Controlled Terminology")
        pn = CT.ProtocolName(_content="SDTM CT Protocol")
        gv = CT.GlobalVariables(StudyName=sn, StudyDescription=sd, ProtocolName=pn)
        study = CT.Study(OID="S.CT.SDTM", GlobalVariables=gv)
        return CT.ODM(
            FileOID="F.CT.SDTM",
            FileType="Snapshot",
            CreationDateTime="2024-01-01T00:00:00",
            Study=[study],
        )

    def test_create_minimal(self):
        odm = self._make_minimal_ct()
        self.assertEqual(odm.FileOID, "F.CT.SDTM")
        self.assertEqual(odm.FileType, "Snapshot")

    def test_to_xml(self):
        odm = self._make_minimal_ct()
        elem = odm.to_xml()
        self.assertEqual(elem.tag, "ODM")
        self.assertEqual(elem.attrib["FileOID"], "F.CT.SDTM")
        self.assertEqual(elem.attrib["FileType"], "Snapshot")

    def test_to_json(self):
        odm = self._make_minimal_ct()
        data = json.loads(odm.to_json())
        self.assertEqual(data["FileOID"], "F.CT.SDTM")
        self.assertEqual(data["FileType"], "Snapshot")
        self.assertIn("Study", data)

    def test_to_dict(self):
        odm = self._make_minimal_ct()
        d = odm.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("FileOID", d)
        self.assertIn("Study", d)
        self.assertIsInstance(d["Study"], list)
        self.assertEqual(len(d["Study"]), 1)

    def test_study_count(self):
        odm = self._make_minimal_ct()
        self.assertEqual(len(odm.Study), 1)
        self.assertEqual(odm.Study[0].OID, "S.CT.SDTM")
