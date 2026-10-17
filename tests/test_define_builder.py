"""Tests for DefineBuilder — reconstructing Define-XML 2.1 from Dataset-JSON."""
import os
import tempfile
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.define_2_1.model as DEF
import odmlib.define_loader as DL
import odmlib.loader as LD
from odmlib import permissive, ValidationMode
from odmlib.dataset_json_1_1 import DefineFlattener, DefineBuilder
from odmlib.dataset_json_1_1.model import DatasetJSON, Column
from odmlib.exceptions import OdmlibTypeError


def _make_test_dataset(name, columns, rows):
    """Helper to create a minimal DatasetJSON for testing."""
    cols = [
        Column(itemOID=f"TEST.{c}", name=c, label=c, dataType="string")
        for c in columns
    ]
    ds = DatasetJSON(
        datasetJSONCreationDateTime="2026-01-01T00:00:00",
        datasetJSONVersion="1.1.0",
        itemGroupOID=f"IG.TEST.{name.upper()}",
        records=len(rows),
        name=name,
        label=f"Test {name}",
        columns=cols,
    )
    if rows:
        ds.rows = rows
    return ds


def _make_empty_datasets(**overrides):
    """Create a full set of 11 datasets with defaults for minimal build."""
    study_cols = [
        "FileOID", "CreationDateTime", "AsOfDateTime", "Originator",
        "SourceSystem", "SourceSystemVersion", "StudyOID", "StudyName",
        "StudyDescription", "ProtocolName", "MetaDataVersionOID",
        "MetaDataVersionName", "DefineVersion", "CommentOID", "Context",
    ]
    study_row = [
        "F.TEST", "2026-01-01T00:00:00", None, None,
        None, None, "S.TEST", "Test Study",
        "Test Description", "Test Protocol", "MDV.TEST",
        "Test MDV", "2.1.0", None, "Submission",
    ]
    defaults = {
        "study": _make_test_dataset("study", study_cols, [study_row]),
        "standards": _make_test_dataset("standards", ["OID"], []),
        "datasets": _make_test_dataset("datasets", ["OID"], []),
        "variables": _make_test_dataset("variables", ["DatasetOID"], []),
        "value_level": _make_test_dataset("value_level", ["ValueListOID"], []),
        "where_clauses": _make_test_dataset("where_clauses", ["WhereClauseOID"], []),
        "methods": _make_test_dataset("methods", ["OID"], []),
        "comments": _make_test_dataset("comments", ["OID"], []),
        "documents": _make_test_dataset("documents", ["ID"], []),
        "codelists": _make_test_dataset("codelists", ["OID"], []),
        "codelist_terms": _make_test_dataset("codelist_terms", ["CodeListOID"], []),
    }
    defaults.update(overrides)
    return defaults


class TestDefineBuilderDocuments(TestCase):
    """Test _build_documents()."""

    def test_build_documents(self):
        ds = _make_test_dataset("documents", ["ID", "href", "title"], [
            ["LF.blankcrf", "blankcrf.pdf", "Blank CRF"],
            ["LF.acrf", "acrf.pdf", "Annotated CRF"],
        ])
        builder = DefineBuilder(_make_empty_datasets(documents=ds))
        leaves = builder._build_documents()
        self.assertEqual(len(leaves), 2)
        self.assertEqual(leaves[0].ID, "LF.blankcrf")
        self.assertEqual(leaves[0].href, "blankcrf.pdf")
        self.assertEqual(leaves[0].title._content, "Blank CRF")

    def test_build_documents_empty(self):
        builder = DefineBuilder(_make_empty_datasets())
        leaves = builder._build_documents()
        self.assertEqual(len(leaves), 0)


class TestDefineBuilderComments(TestCase):
    """Test _build_comments()."""

    def test_build_comments(self):
        ds = _make_test_dataset("comments",
                                ["OID", "DescriptionText", "DocumentRefLeafIDs"],
                                [["COM.1", "Test comment", "LF.1, LF.2"]])
        builder = DefineBuilder(_make_empty_datasets(comments=ds))
        comments = builder._build_comments()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].OID, "COM.1")
        self.assertEqual(comments[0].Description.TranslatedText[0]._content,
                         "Test comment")
        self.assertEqual(len(comments[0].DocumentRef), 2)
        self.assertEqual(comments[0].DocumentRef[0].leafID, "LF.1")
        self.assertEqual(comments[0].DocumentRef[1].leafID, "LF.2")

    def test_build_comments_no_doc_refs(self):
        ds = _make_test_dataset("comments",
                                ["OID", "DescriptionText", "DocumentRefLeafIDs"],
                                [["COM.1", "Just text", None]])
        builder = DefineBuilder(_make_empty_datasets(comments=ds))
        comments = builder._build_comments()
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].OID, "COM.1")


class TestDefineBuilderMethods(TestCase):
    """Test _build_methods()."""

    def test_build_methods_single_expression(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             "SAS", "age = today - dob;", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].OID, "MT.1")
        self.assertEqual(methods[0].Type, "Computation")
        self.assertEqual(len(methods[0].FormalExpression), 1)
        self.assertEqual(methods[0].FormalExpression[0].Context, "SAS")

    def test_build_methods_multiple_expressions(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             "SAS", "age = today - dob;", None],
            ["MT.1", "Method1", "Computation", "Compute age",
             "R", "age <- today - dob", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        self.assertEqual(len(methods[0].FormalExpression), 2)
        self.assertEqual(methods[0].FormalExpression[1].Context, "R")

    def test_build_methods_no_expressions(self):
        ds = _make_test_dataset("methods", [
            "OID", "Name", "Type", "DescriptionText",
            "FormalExpressionContext", "FormalExpressionText",
            "DocumentRefLeafIDs",
        ], [
            ["MT.1", "Method1", "Computation", "Compute age",
             None, None, None],
        ])
        builder = DefineBuilder(_make_empty_datasets(methods=ds))
        methods = builder._build_methods()
        self.assertEqual(len(methods), 1)
        fe = getattr(methods[0], "FormalExpression", None) or []
        self.assertEqual(len(fe), 0)


class TestDefineBuilderWhereClauses(TestCase):
    """Test _build_where_clauses()."""

    def test_build_where_clauses(self):
        ds = _make_test_dataset("where_clauses", [
            "WhereClauseOID", "WhereClauseCommentOID", "Comparator",
            "SoftHard", "ItemOID", "CheckValues",
        ], [
            ["WC.1", None, "EQ", "Soft", "IT.PARAMCD", "SYSBP"],
            ["WC.1", None, "EQ", "Soft", "IT.AVISIT", "WEEK 4"],
        ])
        builder = DefineBuilder(_make_empty_datasets(where_clauses=ds))
        wcs = builder._build_where_clauses()
        self.assertEqual(len(wcs), 1)
        self.assertEqual(wcs[0].OID, "WC.1")
        self.assertEqual(len(wcs[0].RangeCheck), 2)
        self.assertEqual(wcs[0].RangeCheck[0].Comparator, "EQ")
        self.assertEqual(wcs[0].RangeCheck[0].ItemOID, "IT.PARAMCD")
        self.assertEqual(wcs[0].RangeCheck[0].CheckValue[0]._content, "SYSBP")

    def test_build_where_clauses_multiple_check_values(self):
        ds = _make_test_dataset("where_clauses", [
            "WhereClauseOID", "WhereClauseCommentOID", "Comparator",
            "SoftHard", "ItemOID", "CheckValues",
        ], [
            ["WC.1", None, "IN", "Soft", "IT.PARAMCD", "SYSBP, DIABP"],
        ])
        builder = DefineBuilder(_make_empty_datasets(where_clauses=ds))
        wcs = builder._build_where_clauses()
        rc = wcs[0].RangeCheck[0]
        self.assertEqual(len(rc.CheckValue), 2)
        self.assertEqual(rc.CheckValue[0]._content, "SYSBP")
        self.assertEqual(rc.CheckValue[1]._content, "DIABP")


class TestDefineBuilderCodeLists(TestCase):
    """Test _build_codelists()."""

    def test_build_codelist_with_items(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.SEX", "Sex", "text", None, None, "SEX.", None, None,
             None, None, None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [
            ["CL.SEX", "M", None, 1, None, "Male"],
            ["CL.SEX", "F", None, 2, None, "Female"],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        self.assertEqual(len(codelists), 1)
        cl = codelists[0]
        self.assertEqual(cl.OID, "CL.SEX")
        self.assertEqual(len(cl.CodeListItem), 2)
        self.assertEqual(cl.CodeListItem[0].CodedValue, "M")
        self.assertEqual(cl.CodeListItem[0].Decode.TranslatedText[0]._content,
                         "Male")

    def test_build_codelist_enumerated_items(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.NY", "No Yes", "text", None, None, None, None, None,
             None, None, None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [
            ["CL.NY", "N", None, 1, None, None],
            ["CL.NY", "Y", None, 2, None, None],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        cl = codelists[0]
        self.assertEqual(len(cl.EnumeratedItem), 2)
        self.assertEqual(cl.EnumeratedItem[0].CodedValue, "N")

    def test_build_codelist_external(self):
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.MED", "MedDRA", "text", None, None, None, None, None,
             "MedDRA", "25.0", None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        cl = codelists[0]
        self.assertEqual(cl.ExternalCodeList.Dictionary, "MedDRA")
        self.assertEqual(cl.ExternalCodeList.Version, "25.0")


class TestDefineBuilderStandards(TestCase):
    """Test _build_standards()."""

    def test_build_standards(self):
        ds = _make_test_dataset("standards", [
            "OID", "Name", "Type", "PublishingSet", "Version",
            "Status", "CommentOID",
        ], [
            ["STD.1", "SDTMIG", "IG", "SDTM", "3.3", "Final", None],
        ])
        builder = DefineBuilder(_make_empty_datasets(standards=ds))
        standards = builder._build_standards()
        self.assertIsNotNone(standards)
        self.assertEqual(len(standards.Standard), 1)
        self.assertEqual(standards.Standard[0].OID, "STD.1")
        self.assertEqual(standards.Standard[0].Name, "SDTMIG")

    def test_build_standards_empty(self):
        builder = DefineBuilder(_make_empty_datasets())
        standards = builder._build_standards()
        self.assertIsNone(standards)


class TestDefineBuilderBuild(TestCase):
    """Test the full build() method."""

    def test_post_build_hook_mutates_root(self):
        """A post-build hook can inject elements the 11 datasets omit."""
        builder = DefineBuilder(_make_empty_datasets())

        def add_alias(odm):
            odm.Study.MetaDataVersion.ItemGroupDef.append(
                DEF.ItemGroupDef(OID="IG.HOOK", Name="Hooked",
                                 Repeating="No",
                                 Structure="One record per subject",
                                 Alias=[DEF.Alias(Context="x", Name="y")]))

        odm = builder.add_post_build_hook(add_alias).build()
        igd = odm.Study.MetaDataVersion.ItemGroupDef[0]
        self.assertEqual(igd.OID, "IG.HOOK")
        self.assertEqual(igd.Alias[0].Name, "y")

    def test_post_build_hook_replacement(self):
        """A hook returning a value replaces the ODM root."""
        builder = DefineBuilder(_make_empty_datasets())

        def replace(root):
            root.FileOID = "REPLACED"
            return root  # non-None return becomes the new root

        odm = builder.add_post_build_hook(replace).build()
        self.assertEqual(odm.FileOID, "REPLACED")

    def test_minimal_build(self):
        """Build with just study metadata and no child elements."""
        builder = DefineBuilder(_make_empty_datasets())
        odm = builder.build()
        self.assertEqual(odm.FileType, "Snapshot")
        self.assertEqual(odm.FileOID, "F.TEST")
        self.assertEqual(odm.ODMVersion, "1.3.2")
        self.assertEqual(odm.Context, "Submission")
        self.assertEqual(odm.Study.OID, "S.TEST")
        self.assertEqual(odm.Study.GlobalVariables.StudyName._content, "Test Study")
        self.assertEqual(odm.Study.MetaDataVersion.OID, "MDV.TEST")
        self.assertEqual(odm.Study.MetaDataVersion.DefineVersion, "2.1.0")


class TestDefineBuilderRoundtrip(TestCase):
    """Integration tests: flatten -> rebuild -> compare."""

    def _load_define(self, filename):
        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(filename)
        return loader.root()

    def test_roundtrip_sdtm_metadata(self):
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        # Element counts
        self.assertEqual(len(rebuilt_mdv.ItemGroupDef),
                         len(orig_mdv.ItemGroupDef))
        self.assertEqual(len(rebuilt_mdv.CodeList), len(orig_mdv.CodeList))
        self.assertEqual(len(rebuilt_mdv.MethodDef), len(orig_mdv.MethodDef))

        # OIDs match
        orig_igd_oids = {igd.OID for igd in orig_mdv.ItemGroupDef}
        rebuilt_igd_oids = {igd.OID for igd in rebuilt_mdv.ItemGroupDef}
        self.assertEqual(orig_igd_oids, rebuilt_igd_oids)

        # Key attributes
        self.assertEqual(rebuilt.FileOID, original.FileOID)
        self.assertEqual(rebuilt.Study.OID, original.Study.OID)
        self.assertEqual(rebuilt_mdv.DefineVersion, orig_mdv.DefineVersion)

    def test_roundtrip_alias_and_full_origin_lossless(self):
        """Alias (all 5 owners) + full Origin survive flatten -> rebuild."""
        original = self._load_define(
            "tests/data/defineV21-SDTM-metadata.xml")
        omdv = original.Study.MetaDataVersion
        igd = omdv.ItemGroupDef[0]
        idf = omdv.ItemDef[0]
        cl = omdv.CodeList[0]
        terms = (list(getattr(cl, "CodeListItem", None) or [])
                 + list(getattr(cl, "EnumeratedItem", None) or []))
        term = terms[0]

        igd.Alias.append(DEF.Alias(Context="SDTM", Name="IG-ALIAS"))
        idf.Alias.append(DEF.Alias(Context="SDTM", Name="IT-ALIAS"))
        cl.Alias.append(DEF.Alias(Context="nci:ExtCodeID", Name="CL-ALIAS"))
        term.Alias.append(DEF.Alias(Context="nci:ExtCodeID",
                                    Name="TERM-ALIAS"))
        idf.Origin = [DEF.Origin(
            Type="Derived", Source="Sponsor",
            Description=DEF.Description(TranslatedText=[
                DEF.TranslatedText(_content="Derived per SAP", lang="en")]),
            DocumentRef=[DEF.DocumentRef(leafID="LF.SAP")])]

        flat = DefineFlattener(original).flatten_all()
        self.assertIn("aliases", flat)
        self.assertIn("origins", flat)
        rebuilt = DefineBuilder(flat).build()
        rmdv = rebuilt.Study.MetaDataVersion

        r_igd = next(x for x in rmdv.ItemGroupDef if x.OID == igd.OID)
        r_idf = next(x for x in rmdv.ItemDef if x.OID == idf.OID)
        r_cl = next(x for x in rmdv.CodeList if x.OID == cl.OID)
        r_terms = (list(getattr(r_cl, "CodeListItem", None) or [])
                   + list(getattr(r_cl, "EnumeratedItem", None) or []))
        r_term = next(t for t in r_terms
                      if t.CodedValue == term.CodedValue)

        self.assertEqual(r_igd.Alias[-1].Name, "IG-ALIAS")
        self.assertEqual(r_idf.Alias[-1].Name, "IT-ALIAS")
        self.assertEqual(r_cl.Alias[-1].Name, "CL-ALIAS")
        self.assertEqual(r_term.Alias[-1].Name, "TERM-ALIAS")

        o = r_idf.Origin[0]
        self.assertEqual(o.Type, "Derived")
        self.assertEqual(o.Source, "Sponsor")
        self.assertEqual(o.Description.TranslatedText[0]._content,
                         "Derived per SAP")
        self.assertEqual(o.Description.TranslatedText[0].lang, "en")
        self.assertEqual(o.DocumentRef[0].leafID, "LF.SAP")

    def test_roundtrip_adam(self):
        original = self._load_define("tests/data/definev21-adam.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        self.assertEqual(len(rebuilt_mdv.ItemGroupDef),
                         len(orig_mdv.ItemGroupDef))
        self.assertEqual(len(rebuilt_mdv.CodeList), len(orig_mdv.CodeList))
        self.assertEqual(len(rebuilt_mdv.MethodDef), len(orig_mdv.MethodDef))

    def test_roundtrip_write_xml(self):
        """Verify rebuilt Define-XML writes valid XML."""
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            tmpfile = f.name
        try:
            rebuilt.write_xml(tmpfile)
            self.assertTrue(os.path.exists(tmpfile))
            self.assertGreater(os.path.getsize(tmpfile), 0)
            # the file must re-parse: def:leaf carries xlink:href, whose xmlns:xlink
            # was omitted before 0.3.0 once the registry had been reset
            root = ET.parse(tmpfile).getroot()
            self.assertEqual(root.tag, "{http://www.cdisc.org/ns/odm/v1.3}ODM")
            self.assertIsNotNone(root.find(".//{http://www.cdisc.org/ns/def/v2.1}leaf"))
        finally:
            os.unlink(tmpfile)

    def test_roundtrip_itemref_counts(self):
        """Verify ItemRef counts match per ItemGroupDef."""
        original = self._load_define("tests/data/defineV21-SDTM-metadata.xml")
        flat = DefineFlattener(original).flatten_all()
        rebuilt = DefineBuilder(flat).build()

        orig_mdv = original.Study.MetaDataVersion
        rebuilt_mdv = rebuilt.Study.MetaDataVersion

        for orig_igd in orig_mdv.ItemGroupDef:
            rebuilt_igd = None
            for r in rebuilt_mdv.ItemGroupDef:
                if r.OID == orig_igd.OID:
                    rebuilt_igd = r
                    break
            self.assertIsNotNone(rebuilt_igd,
                                 f"Missing ItemGroupDef {orig_igd.OID}")
            orig_refs = getattr(orig_igd, "ItemRef", None) or []
            rebuilt_refs = getattr(rebuilt_igd, "ItemRef", None) or []
            self.assertEqual(
                len(rebuilt_refs), len(orig_refs),
                f"ItemRef count mismatch for {orig_igd.OID}")


class TestDefineBuilderEdgeCases(TestCase):
    """Edge case tests for DefineBuilder (Issue 2.6)."""

    def test_empty_codelist(self):
        """A codelist with no terms should still build without error."""
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.EMPTY", "Empty List", "text", None, None, None, None, None,
             None, None, None, None],
        ])
        # No terms at all for CL.EMPTY
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [])
        builder = DefineBuilder(_make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds))
        codelists = builder._build_codelists()
        self.assertEqual(len(codelists), 1)
        cl = codelists[0]
        self.assertEqual(cl.OID, "CL.EMPTY")
        # No CodeListItem or EnumeratedItem
        cli = getattr(cl, "CodeListItem", None) or []
        eni = getattr(cl, "EnumeratedItem", None) or []
        self.assertEqual(len(cli), 0)
        self.assertEqual(len(eni), 0)

    def test_missing_optional_fields(self):
        """Build succeeds when no Comment or Method datasets have rows."""
        datasets = _make_empty_datasets()
        # comments and methods datasets exist but have no rows (empty)
        builder = DefineBuilder(datasets)
        odm = builder.build()
        mdv = odm.Study.MetaDataVersion
        # No CommentDef or MethodDef should be created
        comment_defs = getattr(mdv, "CommentDef", None) or []
        method_defs = getattr(mdv, "MethodDef", None) or []
        self.assertEqual(len(comment_defs), 0)
        self.assertEqual(len(method_defs), 0)

    def test_single_variable_dataset(self):
        """A dataset with a single variable should build correctly."""
        # Column names must match what DefineFlattener produces
        ds_ds = _make_test_dataset("datasets", [
            "OID", "Name", "Repeating", "IsReferenceData",
            "SASDatasetName", "Domain", "Purpose", "Structure",
            "ArchiveLocationID", "CommentOID", "IsNonStandard",
            "StandardOID", "HasNoData", "DescriptionText",
            "ClassName", "SubClassName", "leafID", "leafHref", "leafTitle",
        ], [
            ["IG.SINGLE", "SINGLE", "No", "No",
             "SINGLE", None, "Tabulation", "One Record Per Subject",
             None, None, None,
             None, None, None,
             "SPECIAL PURPOSE", None, None, None, None],
        ])
        var_ds = _make_test_dataset("variables", [
            "DatasetOID", "ItemOID", "OrderNumber", "Mandatory",
            "KeySequence", "MethodOID", "Role", "RoleCodeListOID",
            "IsNonStandard", "HasNoData", "Name", "DataType",
            "Length", "SignificantDigits", "SASFieldName",
            "DisplayFormat", "CommentOID", "DescriptionText",
            "CodeListOID", "ValueListOID", "OriginType", "OriginSource",
        ], [
            ["IG.SINGLE", "IT.SINGLE.VAR1", "1", "Yes",
             "1", None, None, None,
             None, None, "VAR1", "text",
             "20", None, "VAR1",
             None, None, None,
             None, None, "Collected", "Sponsor"],
        ])
        builder = DefineBuilder(_make_empty_datasets(
            datasets=ds_ds, variables=var_ds))
        odm = builder.build()
        mdv = odm.Study.MetaDataVersion
        self.assertEqual(len(mdv.ItemGroupDef), 1)
        igd = mdv.ItemGroupDef[0]
        self.assertEqual(igd.OID, "IG.SINGLE")
        item_refs = getattr(igd, "ItemRef", None) or []
        self.assertEqual(len(item_refs), 1)
        self.assertEqual(item_refs[0].ItemOID, "IT.SINGLE.VAR1")
        # Should also have one ItemDef
        self.assertEqual(len(mdv.ItemDef), 1)
        self.assertEqual(mdv.ItemDef[0].OID, "IT.SINGLE.VAR1")


class TestDefineBuilderFileIO(TestCase):
    """Test write_all + read_all + build roundtrip."""

    def test_write_read_build(self):
        original = LD.ODMLoader(
            DL.XMLDefineLoader(model_package="define_2_1"))
        original.open_odm_document("tests/data/defineV21-SDTM-metadata.xml")
        odm = original.root()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write flattened datasets
            flattener = DefineFlattener(odm)
            flattener.write_all(tmpdir)

            # Read them back and rebuild
            datasets = DefineBuilder.read_all(tmpdir)
            rebuilt = DefineBuilder(datasets).build()

            self.assertEqual(rebuilt.FileOID, odm.FileOID)
            self.assertEqual(
                len(rebuilt.Study.MetaDataVersion.ItemGroupDef),
                len(odm.Study.MetaDataVersion.ItemGroupDef))


class TestDefineBuilderPermissive(TestCase):
    """Verify permissive() applies to DefineBuilder via the descriptor layer.

    DefineBuilder has no permissive plumbing of its own. It constructs ODM
    objects through the standard DEF.ClassName(**kwargs) path, so a
    process-wide permissive() context bypasses validation during build().
    """

    VARIABLES_COLS = [
        "DatasetOID", "ItemOID", "Name", "DataType",
        "Length", "SignificantDigits", "SASFieldName", "DisplayFormat",
        "CommentOID", "DescriptionText",
        "ValueListOID", "CodeListOID", "OriginType", "OriginSource",
        "Mandatory", "OrderNumber", "KeySequence", "MethodOID",
        "Role", "RoleCodeListOID", "IsNonStandard", "HasNoData",
    ]

    def _datasets_with_bad_datatype(self):
        # One ItemDef row with an invalid DataType valueset value.
        row = [
            "IG.TEST",            # DatasetOID
            "IT.TEST.AETERM",     # ItemOID
            "AETERM",             # Name
            "bogus",              # DataType — fails ValidValues under strict
            None, None, None, None, None, None,
            None, None, None, None,
            None, None, None, None, None, None, None, None,
        ]
        variables = _make_test_dataset("variables", self.VARIABLES_COLS, [row])
        return _make_empty_datasets(variables=variables)

    def test_invalid_valueset_fails_strict(self):
        datasets = self._datasets_with_bad_datatype()
        with self.assertRaises(OdmlibTypeError):
            DefineBuilder(datasets).build()

    def test_invalid_valueset_succeeds_under_permissive(self):
        datasets = self._datasets_with_bad_datatype()
        with permissive():
            rebuilt = DefineBuilder(datasets).build()
        self.assertIsInstance(rebuilt, DEF.ODM)
        item_def = rebuilt.Study.MetaDataVersion.ItemDef[0]
        self.assertEqual(item_def.OID, "IT.TEST.AETERM")
        self.assertEqual(item_def.DataType, "bogus")

    def test_targeted_skip_valueset_only(self):
        datasets = self._datasets_with_bad_datatype()
        with permissive(ValidationMode.SKIP_VALUESET):
            rebuilt = DefineBuilder(datasets).build()
        self.assertIsInstance(rebuilt, DEF.ODM)
        self.assertEqual(
            rebuilt.Study.MetaDataVersion.ItemDef[0].DataType, "bogus")

    # ------------------------------------------------------------------ #
    # Text-in-numeric-field tests — exercise _int_or_none / _float_or_none
    # end-to-end through DefineBuilder.build().
    # ------------------------------------------------------------------ #

    def _datasets_with_bad_length(self):
        # variables row with non-numeric Length (gated by _int_or_none).
        row = [
            "IG.TEST",            # DatasetOID
            "IT.TEST.AETERM",     # ItemOID
            "AETERM",             # Name
            "text",               # DataType
            "notanumber",         # Length — non-numeric
            None, None, None, None, None,
            None, None, None, None,
            None, None, None, None, None, None, None, None,
        ]
        variables = _make_test_dataset("variables", self.VARIABLES_COLS, [row])
        return _make_empty_datasets(variables=variables)

    def test_invalid_length_fails_strict(self):
        datasets = self._datasets_with_bad_length()
        with self.assertRaises(OdmlibTypeError) as cm:
            DefineBuilder(datasets).build()
        self.assertEqual(cm.exception.attribute, "Length")
        self.assertEqual(cm.exception.expected_type, "int")
        self.assertEqual(cm.exception.actual_value, "notanumber")

    def test_invalid_length_succeeds_under_permissive(self):
        datasets = self._datasets_with_bad_length()
        with permissive():
            rebuilt = DefineBuilder(datasets).build()
        self.assertIsInstance(rebuilt, DEF.ODM)
        item_def = rebuilt.Study.MetaDataVersion.ItemDef[0]
        self.assertEqual(item_def.OID, "IT.TEST.AETERM")
        self.assertEqual(item_def.Length, "notanumber")

    def test_invalid_length_targeted_skip_type_only(self):
        datasets = self._datasets_with_bad_length()
        with permissive(ValidationMode.SKIP_TYPE):
            rebuilt = DefineBuilder(datasets).build()
        self.assertIsInstance(rebuilt, DEF.ODM)
        self.assertEqual(
            rebuilt.Study.MetaDataVersion.ItemDef[0].Length, "notanumber")

    def test_invalid_rank_succeeds_under_permissive(self):
        # codelist term with non-numeric Rank — exercises _float_or_none.
        cl_ds = _make_test_dataset("codelists", [
            "OID", "Name", "DataType", "IsNonStandard", "StandardOID",
            "SASFormatName", "CommentOID", "DescriptionText",
            "ExternalDictionary", "ExternalVersion", "ExternalRef", "ExternalHref",
        ], [
            ["CL.SEX", "Sex", "text", None, None, None, None, None,
             None, None, None, None],
        ])
        term_ds = _make_test_dataset("codelist_terms", [
            "CodeListOID", "CodedValue", "Rank", "OrderNumber",
            "ExtendedValue", "DecodedText",
        ], [
            ["CL.SEX", "M", "notanumber", 1, None, "Male"],
        ])
        datasets = _make_empty_datasets(
            codelists=cl_ds, codelist_terms=term_ds)
        with permissive():
            rebuilt = DefineBuilder(datasets).build()
        cl = rebuilt.Study.MetaDataVersion.CodeList[0]
        self.assertEqual(cl.CodeListItem[0].Rank, "notanumber")

    def test_valid_float_from_json_still_works(self):
        # JSON often delivers integers as floats (e.g. 1.0). The helpers must
        # still coerce them under strict mode — guard the original happy path
        # that motivated the helpers' existence.
        from odmlib.dataset_json_1_1.define_builder import (
            _int_or_none, _float_or_none,
        )
        self.assertEqual(_int_or_none(1.0), 1)
        self.assertIsNone(_int_or_none(None))
        self.assertEqual(_float_or_none(2), 2.0)
        self.assertIsNone(_float_or_none(None))
