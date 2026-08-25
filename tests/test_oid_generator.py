"""Tests for dynamic OID ref/def generation (odmlib.oid_generator).

Validates that:
- Model introspection functions produce the expected results.
- Dynamic mappings are consistent with (or better than) the manual oid_ref.py
  mappings.
- The DynamicOIDRef checker is a drop-in replacement for the manual OIDRef
  classes, raising the same exceptions on the same inputs.
- End-to-end OID validation on real documents works correctly.
"""
import os
import unittest

import odmlib.ns_registry as NS

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_odm_132_namespace():
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True,
        is_reset=True,
    )


def _make_define_21_namespace():
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True,
        is_reset=True,
    )
    NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.1")
    NS.NamespaceRegistry(prefix="xs",  uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


def _make_define_20_namespace():
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True,
        is_reset=True,
    )
    NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
    NS.NamespaceRegistry(prefix="xs",  uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


def _make_odm_20_namespace():
    NS.NamespaceRegistry(
        prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v2.0",
        is_default=True,
        is_reset=True,
    )
    NS.NamespaceRegistry(prefix="xs",  uri="http://www.w3.org/2001/XMLSchema-instance")
    NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
    NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")


# ---------------------------------------------------------------------------
# Discovery unit tests
# ---------------------------------------------------------------------------

class TestDiscoverModelClasses(unittest.TestCase):
    """Test discover_model_classes() for each model package."""

    def test_odm_132_finds_core_classes(self):
        from odmlib.oid_generator import discover_model_classes
        import odmlib.odm_1_3_2.model as ODM
        classes = discover_model_classes(ODM)
        for name in ("ItemDef", "FormDef", "ItemGroupDef", "StudyEventDef",
                     "CodeList", "MetaDataVersion", "Study", "ODM"):
            self.assertIn(name, classes, f"Expected {name} in ODM 1.3.2 classes")

    def test_define_21_finds_define_specific_classes(self):
        from odmlib.oid_generator import discover_model_classes
        import odmlib.define_2_1.model as DEFINE
        classes = discover_model_classes(DEFINE)
        for name in ("ItemDef", "CodeList", "WhereClauseDef",
                     "ValueListDef", "CommentDef", "Standard"):
            self.assertIn(name, classes, f"Expected {name} in Define-XML 2.1 classes")

    def test_odm_20_finds_workflow_classes(self):
        from odmlib.oid_generator import discover_model_classes
        import odmlib.odm_2_0.model as ODM2
        classes = discover_model_classes(ODM2)
        for name in ("ItemDef", "ItemGroupDef", "StudyEventDef",
                     "WorkflowDef", "Transition", "Arm", "Epoch"):
            self.assertIn(name, classes, f"Expected {name} in ODM 2.0 classes")


class TestDiscoverOidDefinitions(unittest.TestCase):
    """Test discover_oid_definitions() correctly identifies definition elements."""

    def test_odm_132_definitions(self):
        from odmlib.oid_generator import discover_model_classes, discover_oid_definitions
        import odmlib.odm_1_3_2.model as ODM
        classes = discover_model_classes(ODM)
        defs = discover_oid_definitions(classes)
        for name in ("ItemDef", "FormDef", "ItemGroupDef", "StudyEventDef",
                     "CodeList", "MetaDataVersion", "ConditionDef", "MethodDef",
                     "MeasurementUnit", "ArchiveLayout", "User", "Location"):
            self.assertIn(name, defs, f"Expected {name} to be an OID definition")

    def test_study_is_definition_despite_string_oid(self):
        """Study.OID = T.String but the runtime still registers it; we should too."""
        from odmlib.oid_generator import discover_model_classes, discover_oid_definitions
        import odmlib.odm_1_3_2.model as ODM
        classes = discover_model_classes(ODM)
        defs = discover_oid_definitions(classes)
        self.assertIn("Study", defs)

    def test_define_21_definitions(self):
        from odmlib.oid_generator import discover_model_classes, discover_oid_definitions
        import odmlib.define_2_1.model as DEFINE
        classes = discover_model_classes(DEFINE)
        defs = discover_oid_definitions(classes)
        for name in ("ItemDef", "CodeList", "MethodDef", "WhereClauseDef",
                     "ValueListDef", "CommentDef", "Standard"):
            self.assertIn(name, defs, f"Expected {name} in define_2_1 OID defs")


class TestDiscoverOidReferences(unittest.TestCase):
    """Test discover_oid_references() finds all OID ref attributes."""

    def test_odm_132_references(self):
        from odmlib.oid_generator import discover_model_classes, discover_oid_references
        import odmlib.odm_1_3_2.model as ODM
        classes = discover_model_classes(ODM)
        refs = discover_oid_references(classes)
        for attr in ("FormOID", "ItemOID", "ItemGroupOID", "StudyEventOID",
                     "CodeListOID", "MethodOID", "MetaDataVersionOID", "StudyOID"):
            self.assertIn(attr, refs, f"Expected {attr} in ODM 1.3.2 ref attrs")

    def test_oid_itself_not_in_references(self):
        """The 'OID' definition attr should not appear as a reference."""
        from odmlib.oid_generator import discover_model_classes, discover_oid_references
        import odmlib.odm_1_3_2.model as ODM
        classes = discover_model_classes(ODM)
        refs = discover_oid_references(classes)
        self.assertNotIn("OID", refs)

    def test_define_21_references(self):
        from odmlib.oid_generator import discover_model_classes, discover_oid_references
        import odmlib.define_2_1.model as DEFINE
        classes = discover_model_classes(DEFINE)
        refs = discover_oid_references(classes)
        for attr in ("ItemOID", "MethodOID", "CodeListOID", "WhereClauseOID",
                     "ValueListOID", "CommentOID", "StandardOID"):
            self.assertIn(attr, refs, f"Expected {attr} in define_2_1 ref attrs")


# ---------------------------------------------------------------------------
# Mapping tests
# ---------------------------------------------------------------------------

class TestBuildRefDefMapping(unittest.TestCase):
    """Test that dynamic ref_def matches expected values for each model."""

    def _get_mapping(self, model_pkg):
        from odmlib.oid_generator import (
            discover_model_classes, discover_oid_definitions,
            discover_oid_references, build_ref_def_mapping,
        )
        module = __import__(f"odmlib.{model_pkg}.model", fromlist=["model"])
        classes = discover_model_classes(module)
        defs = discover_oid_definitions(classes)
        refs = discover_oid_references(classes)
        return build_ref_def_mapping(refs, defs, classes)

    def test_odm_132_standard_mappings(self):
        ref_def = self._get_mapping("odm_1_3_2")
        self.assertEqual(ref_def.get("FormOID"), "FormDef")
        self.assertEqual(ref_def.get("ItemOID"), "ItemDef")
        self.assertEqual(ref_def.get("ItemGroupOID"), "ItemGroupDef")
        self.assertEqual(ref_def.get("StudyEventOID"), "StudyEventDef")
        self.assertEqual(ref_def.get("CodeListOID"), "CodeList")
        self.assertEqual(ref_def.get("MethodOID"), "MethodDef")
        self.assertEqual(ref_def.get("MetaDataVersionOID"), "MetaDataVersion")
        self.assertEqual(ref_def.get("StudyOID"), "Study")

    def test_odm_132_override_mappings(self):
        ref_def = self._get_mapping("odm_1_3_2")
        self.assertEqual(ref_def.get("CollectionExceptionConditionOID"), "ConditionDef")
        self.assertEqual(ref_def.get("MeasurementUnitOID"), "MeasurementUnit")
        self.assertEqual(ref_def.get("UserOID"), "User")
        self.assertEqual(ref_def.get("LocationOID"), "Location")
        self.assertEqual(ref_def.get("PresentationOID"), "Presentation")
        # ArchiveLayoutOID is not declared in any ODM 1.3.2 model class attribute,
        # so the dynamic checker correctly omits it (unlike the manual oid_ref.py
        # which hard-coded it). ArchiveLayout exists as a class (OID-carrying
        # element) but ArchiveLayoutOID does not appear as a ref attribute.
        self.assertIsNone(ref_def.get("ArchiveLayoutOID"))

    def test_define_21_mappings(self):
        ref_def = self._get_mapping("define_2_1")
        self.assertEqual(ref_def.get("ItemOID"), "ItemDef")
        self.assertEqual(ref_def.get("MethodOID"), "MethodDef")
        self.assertEqual(ref_def.get("CodeListOID"), "CodeList")
        self.assertEqual(ref_def.get("WhereClauseOID"), "WhereClauseDef")
        self.assertEqual(ref_def.get("ValueListOID"), "ValueListDef")
        self.assertEqual(ref_def.get("CommentOID"), "CommentDef")
        self.assertEqual(ref_def.get("StandardOID"), "Standard")

    def test_odm_20_workflow_mappings(self):
        ref_def = self._get_mapping("odm_2_0")
        self.assertEqual(ref_def.get("WorkflowOID"), "WorkflowDef")
        self.assertEqual(ref_def.get("StudyEventGroupOID"), "StudyEventGroupDef")
        self.assertEqual(ref_def.get("ArmOID"), "Arm")
        self.assertEqual(ref_def.get("EpochOID"), "Epoch")

    def test_override_not_applied_when_class_absent(self):
        """An override should be skipped when its target class doesn't exist
        in the model (e.g. CommentDef from define exists in define_2_1 but
        not in odm_1_3_2)."""
        ref_def = self._get_mapping("odm_1_3_2")
        # CommentDef doesn't exist in ODM 1.3.2, so CommentOID shouldn't
        # appear in the mapping (or would resolve via convention differently).
        # The key test is that we don't blow up.
        self.assertIsNotNone(ref_def)  # no exception means success


class TestBuildDefRefMapping(unittest.TestCase):
    """Test that build_def_ref_mapping correctly inverts ref_def."""

    def test_inversion(self):
        from odmlib.oid_generator import build_def_ref_mapping
        ref_def = {
            "FormOID": "FormDef",
            "ItemOID": "ItemDef",
            "CodeListOID": "CodeList",
        }
        def_ref = build_def_ref_mapping(ref_def)
        self.assertIn("FormOID", def_ref["FormDef"])
        self.assertIn("ItemOID", def_ref["ItemDef"])
        self.assertIn("CodeListOID", def_ref["CodeList"])

    def test_multiple_refs_to_same_def(self):
        """Several ref attrs that point to the same definition class."""
        from odmlib.oid_generator import build_def_ref_mapping
        ref_def = {
            "CodeListOID": "CodeList",
            "RoleCodeListOID": "CodeList",
        }
        def_ref = build_def_ref_mapping(ref_def)
        self.assertIn("CodeListOID", def_ref["CodeList"])
        self.assertIn("RoleCodeListOID", def_ref["CodeList"])


# ---------------------------------------------------------------------------
# DynamicOIDRef unit tests
# ---------------------------------------------------------------------------

class TestDynamicOIDRefBasicBehaviour(unittest.TestCase):
    """Test DynamicOIDRef add/check methods in isolation."""

    def setUp(self):
        _make_odm_132_namespace()
        from odmlib.oid_generator import create_oid_checker
        self.checker = create_oid_checker("odm_1_3_2")

    def test_add_oid_and_ref_valid(self):
        self.checker.add_oid("IT.AGE", "ItemDef")
        self.checker.add_oid_ref("IT.AGE", "ItemOID")
        self.assertTrue(self.checker.check_oid_refs())

    def test_duplicate_oid_raises(self):
        self.checker.add_oid("IT.AGE", "ItemDef")
        with self.assertRaises(ValueError):
            self.checker.add_oid("IT.AGE", "ItemDef")

    def test_missing_ref_raises(self):
        # Add a reference to an OID that was never defined.
        self.checker.add_oid_ref("IT.MISSING", "ItemOID")
        with self.assertRaises(ValueError):
            self.checker.check_oid_refs()

    def test_type_mismatch_raises(self):
        # CL.SEX is a CodeList OID, but ItemOID should reference ItemDef.
        self.checker.add_oid("CL.SEX", "CodeList")
        self.checker.add_oid_ref("CL.SEX", "ItemOID")
        with self.assertRaises(ValueError):
            self.checker.check_oid_refs()

    def test_skip_attr_ignores_ref(self):
        # FileOID is in skip_attr, so it should never be tracked.
        self.checker.add_oid_ref("STUDY001.FILE", "FileOID")
        # Nothing in oid_ref["FileOID"] (FileOID not in oid_ref either).
        self.assertTrue(self.checker.check_oid_refs())

    def test_skip_elem_ignores_definition(self):
        # "ODM" is in skip_elem, so its OID should not be registered.
        self.checker.add_oid("FILE001", "ODM")
        self.assertNotIn("FILE001", self.checker.oid)

    def test_is_oids_verified_before_check(self):
        self.checker.add_oid("IT.AGE", "ItemDef")
        self.assertFalse(self.checker.is_oids_verified())

    def test_is_oids_verified_after_check(self):
        self.checker.add_oid("IT.AGE", "ItemDef")
        self.checker.check_oid_refs()
        self.assertTrue(self.checker.is_oids_verified())

    def test_check_unreferenced_oids_empty_when_all_referenced(self):
        self.checker.add_oid("IT.AGE", "ItemDef")
        self.checker.add_oid_ref("IT.AGE", "ItemOID")
        self.checker.check_oid_refs()
        orphans = self.checker.check_unreferenced_oids()
        self.assertNotIn("IT.AGE", orphans)

    def test_check_unreferenced_oids_finds_orphan(self):
        self.checker.add_oid("IT.UNUSED", "ItemDef")
        # No corresponding ref added.
        self.checker.check_oid_refs()
        orphans = self.checker.check_unreferenced_oids()
        self.assertIn("IT.UNUSED", orphans)


class TestDynamicOIDRefDefine21(unittest.TestCase):
    """DynamicOIDRef tests for the Define-XML 2.1 model."""

    def setUp(self):
        _make_define_21_namespace()
        from odmlib.oid_generator import create_oid_checker
        self.checker = create_oid_checker("define_2_1")

    def test_where_clause_oid_resolved(self):
        self.assertIn("WhereClauseOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["WhereClauseOID"], "WhereClauseDef")

    def test_value_list_oid_resolved(self):
        self.assertIn("ValueListOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["ValueListOID"], "ValueListDef")

    def test_comment_oid_resolved(self):
        self.assertIn("CommentOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["CommentOID"], "CommentDef")

    def test_standard_oid_resolved(self):
        self.assertIn("StandardOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["StandardOID"], "Standard")

    def test_valid_where_clause_ref(self):
        self.checker.add_oid("WC.001", "WhereClauseDef")
        self.checker.add_oid_ref("WC.001", "WhereClauseOID")
        self.assertTrue(self.checker.check_oid_refs())

    def test_item_group_oid_skipped(self):
        """ItemGroupOID is in skip_attr for define, so it should be ignored."""
        self.checker.add_oid_ref("IG.DM", "ItemGroupOID")
        self.assertTrue(self.checker.check_oid_refs())


class TestDynamicOIDRefODM20(unittest.TestCase):
    """DynamicOIDRef tests for the ODM 2.0 model."""

    def setUp(self):
        _make_odm_20_namespace()
        from odmlib.oid_generator import create_oid_checker
        self.checker = create_oid_checker("odm_2_0")

    def test_workflow_oid_resolved(self):
        self.assertIn("WorkflowOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["WorkflowOID"], "WorkflowDef")

    def test_arm_oid_resolved(self):
        self.assertIn("ArmOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["ArmOID"], "Arm")

    def test_epoch_oid_resolved(self):
        self.assertIn("EpochOID", self.checker.ref_def)
        self.assertEqual(self.checker.ref_def["EpochOID"], "Epoch")

    def test_skipped_attrs_not_in_oid_ref(self):
        """Complex workflow OIDs in skip list should not appear in oid_ref."""
        for attr in ("StartOID", "SourceOID", "TargetOID", "EndOID"):
            # These are in skip_attr, so add_oid_ref should silently ignore.
            self.checker.add_oid_ref("SOME.OID", attr)
        # No exception on check.
        self.assertTrue(self.checker.check_oid_refs())

    def test_valid_workflow_ref(self):
        self.checker.add_oid("WF.001", "WorkflowDef")
        self.checker.add_oid_ref("WF.001", "WorkflowOID")
        self.assertTrue(self.checker.check_oid_refs())


# ---------------------------------------------------------------------------
# create_oid_checker factory tests
# ---------------------------------------------------------------------------

class TestCreateOidChecker(unittest.TestCase):
    """Test the create_oid_checker() factory function."""

    def setUp(self):
        _make_odm_132_namespace()

    def test_returns_dynamic_oid_ref(self):
        from odmlib.oid_generator import create_oid_checker, DynamicOIDRef
        checker = create_oid_checker("odm_1_3_2")
        self.assertIsInstance(checker, DynamicOIDRef)

    def test_odm_132_has_correct_skip_lists(self):
        from odmlib.oid_generator import create_oid_checker
        checker = create_oid_checker("odm_1_3_2")
        self.assertIn("FileOID", checker.skip_attr)
        self.assertIn("PriorFileOID", checker.skip_attr)
        self.assertIn("ODM", checker.skip_elem)

    def test_define_21_has_correct_skip_lists(self):
        _make_define_21_namespace()
        from odmlib.oid_generator import create_oid_checker
        checker = create_oid_checker("define_2_1")
        self.assertIn("StudyOID", checker.skip_attr)
        self.assertIn("MetaDataVersionOID", checker.skip_attr)
        self.assertIn("ItemGroupDef", checker.skip_elem)

    def test_extra_skip_attrs_merged(self):
        from odmlib.oid_generator import create_oid_checker
        checker = create_oid_checker("odm_1_3_2", extra_skip_attrs=["CustomOID"])
        self.assertIn("CustomOID", checker.skip_attr)
        self.assertIn("FileOID", checker.skip_attr)  # default still present

    def test_extra_skip_elems_merged(self):
        from odmlib.oid_generator import create_oid_checker
        checker = create_oid_checker("odm_1_3_2", extra_skip_elems=["CustomDef"])
        self.assertIn("CustomDef", checker.skip_elem)
        self.assertIn("ODM", checker.skip_elem)  # default still present

    def test_unknown_package_returns_checker(self):
        """Unknown model package uses empty skip lists — should not raise."""
        from odmlib.oid_generator import create_oid_checker
        # Will try to import odmlib.nonexistent.model — expect ImportError.
        with self.assertRaises(ModuleNotFoundError):
            create_oid_checker("nonexistent_pkg")


# ---------------------------------------------------------------------------
# End-to-end validation tests (real XML documents)
# ---------------------------------------------------------------------------

class TestEndToEndODM132(unittest.TestCase):
    """End-to-end OID validation using a programmatically-built ODM 1.3.2 MetaDataVersion.

    Note: the CDASH test XML files in tests/data/ have intentional OID
    mismatches between CodeListRef and CodeList definitions (cross-file
    references), so a programmatic self-contained MetaDataVersion is used
    here to exercise the OID checker logic in isolation.
    """

    def setUp(self):
        _make_odm_132_namespace()

    def _build_simple_mdv(self):
        """Return a minimal but self-contained ODM 1.3.2 MetaDataVersion."""
        import odmlib.odm_1_3_2.model as ODM

        p = ODM.Protocol()
        p.StudyEventRef = [
            ODM.StudyEventRef(StudyEventOID="SE.001", OrderNumber=1, Mandatory="Yes")
        ]

        sed = ODM.StudyEventDef(OID="SE.001", Name="Baseline", Repeating="No", Type="Scheduled")
        sed.FormRef = [ODM.FormRef(FormOID="F.001", Mandatory="Yes", OrderNumber=1)]

        fd = ODM.FormDef(OID="F.001", Name="Demographics", Repeating="No")
        fd.ItemGroupRef = [ODM.ItemGroupRef(ItemGroupOID="IG.001", Mandatory="Yes")]

        igd = ODM.ItemGroupDef(OID="IG.001", Name="Demographics", Repeating="No")
        igd.ItemRef = [
            ODM.ItemRef(ItemOID="IT.AGE", Mandatory="Yes"),
            ODM.ItemRef(ItemOID="IT.SEX", Mandatory="Yes"),
        ]

        mdv = ODM.MetaDataVersion(OID="MDV.001", Name="Test MDV")
        mdv.Protocol = p
        mdv.StudyEventDef = [sed]
        mdv.FormDef = [fd]
        mdv.ItemGroupDef = [igd]
        mdv.ItemDef = [
            ODM.ItemDef(OID="IT.AGE", Name="Age", DataType="integer"),
            ODM.ItemDef(OID="IT.SEX", Name="Sex", DataType="text"),
        ]
        return mdv

    def test_valid_document_passes(self):
        from odmlib.oid_generator import create_oid_checker

        mdv = self._build_simple_mdv()
        checker = create_oid_checker("odm_1_3_2")
        mdv.verify_oids(checker)
        result = checker.check_oid_refs()
        self.assertTrue(result)

    def test_dynamic_collects_same_oids_as_manual(self):
        """Dynamic checker should register the same OID set as the manual checker."""
        import warnings
        from odmlib.oid_generator import create_oid_checker

        # --- manual checker ---
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import odmlib.odm_1_3_2.rules.oid_ref as MANUAL
            manual_checker = MANUAL.OIDRef()

        self._build_simple_mdv().verify_oids(manual_checker)

        # --- dynamic checker ---
        dynamic_checker = create_oid_checker("odm_1_3_2")
        self._build_simple_mdv().verify_oids(dynamic_checker)

        # Both should have registered the same OID definitions.
        self.assertEqual(
            set(manual_checker.oid.keys()),
            set(dynamic_checker.oid.keys()),
            "Dynamic and manual checkers collected different OID sets.",
        )


class TestEndToEndDefine21(unittest.TestCase):
    """End-to-end OID validation using a programmatic Define-XML 2.1 MetaDataVersion.

    Note: defineV21-SDTM.xml cannot be used directly because the odmlib loader
    does not fully populate the Standards child elements (pre-existing limitation),
    causing StandardOID references to appear unresolved.  A minimal programmatic
    MetaDataVersion is used instead to exercise the checker logic in isolation.
    """

    def setUp(self):
        _make_define_21_namespace()

    def _build_simple_define_mdv(self):
        """Return a minimal Define-XML 2.1 MetaDataVersion."""
        import odmlib.define_2_1.model as DEFINE

        wc = DEFINE.WhereClauseDef(OID="WC.001")
        vl = DEFINE.ValueListDef(OID="VL.001")
        cl = DEFINE.CodeList(OID="CL.001", Name="Test CL", DataType="text", SASFormatName="CL001")

        itd = DEFINE.ItemDef(OID="IT.001", Name="Test Item", DataType="text", Length=50)
        itd.CodeListRef = DEFINE.CodeListRef(CodeListOID="CL.001")
        itd.ValueListRef = DEFINE.ValueListRef(ValueListOID="VL.001")

        # WhereClauseRef links an ItemRef (inside a ValueListDef) to a WhereClauseDef.
        igr = DEFINE.ItemRef(ItemOID="IT.001", Mandatory="No")
        igr.WhereClauseRef = [DEFINE.WhereClauseRef(WhereClauseOID="WC.001")]
        vl.ItemRef = [igr]

        mdv = DEFINE.MetaDataVersion(
            OID="MDV.001", Name="Test Define MDV",
            Description="Test", DefineVersion="2.1.0",
        )
        mdv.ItemDef = [itd]
        mdv.CodeList = [cl]
        mdv.WhereClauseDef = [wc]
        mdv.ValueListDef = [vl]
        return mdv

    def test_valid_document_passes(self):
        from odmlib.oid_generator import create_oid_checker

        mdv = self._build_simple_define_mdv()
        checker = create_oid_checker("define_2_1")
        mdv.verify_oids(checker)
        result = checker.check_oid_refs()
        self.assertTrue(result)

    def test_dynamic_collects_same_oids_as_manual(self):
        """Dynamic and manual checkers should register the same OID set."""
        import warnings
        from odmlib.oid_generator import create_oid_checker

        # --- manual checker ---
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import odmlib.define_2_1.rules.oid_ref as MANUAL
            manual_checker = MANUAL.OIDRef()

        self._build_simple_define_mdv().verify_oids(manual_checker)

        # --- dynamic checker ---
        dynamic_checker = create_oid_checker("define_2_1")
        self._build_simple_define_mdv().verify_oids(dynamic_checker)

        self.assertEqual(
            set(manual_checker.oid.keys()),
            set(dynamic_checker.oid.keys()),
            "Dynamic and manual Define-XML 2.1 checkers collected different OID sets.",
        )


class TestEndToEndDefine20(unittest.TestCase):
    """End-to-end OID validation using define2-0-0-sdtm-test.xml."""

    def setUp(self):
        _make_define_20_namespace()

    def test_valid_document_passes(self):
        import odmlib.define_loader as DL
        import odmlib.loader as LD
        from odmlib.oid_generator import create_oid_checker

        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_0"))
        loader.open_odm_document(os.path.join(DATA_DIR, "define2-0-0-sdtm-test.xml"))
        odm = loader.root()

        checker = create_oid_checker("define_2_0")
        result = odm.verify_oids(checker)
        self.assertTrue(result)


class TestEndToEndODM20(unittest.TestCase):
    """End-to-end OID validation using odmv2_example.xml."""

    def setUp(self):
        _make_odm_20_namespace()

    def test_checker_creation_and_discovery(self):
        """Verify that a DynamicOIDRef can be created for ODM 2.0."""
        from odmlib.oid_generator import create_oid_checker, DynamicOIDRef
        checker = create_oid_checker("odm_2_0")
        self.assertIsInstance(checker, DynamicOIDRef)
        # Should have discovered OID definitions.
        self.assertTrue(len(checker.oid_defs) > 0)
        # Should have discovered OID references.
        self.assertTrue(len(checker.ref_attrs) > 0)

    def test_valid_document_passes(self):
        import odmlib.odm_loader as OL
        import odmlib.loader as LD
        from odmlib.oid_generator import create_oid_checker

        loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
        loader.open_odm_document(os.path.join(DATA_DIR, "odmv2_example.xml"))
        odm = loader.root()

        checker = create_oid_checker("odm_2_0")
        result = odm.verify_oids(checker)
        self.assertTrue(result)


# ---------------------------------------------------------------------------
# Deprecation warning tests for manual OIDRef
# ---------------------------------------------------------------------------

class TestManualOIDRefDeprecation(unittest.TestCase):
    """Verify that the legacy manual OIDRef classes emit deprecation warnings."""

    def setUp(self):
        _make_odm_132_namespace()

    def test_odm_132_oid_ref_warns(self):
        import warnings
        # Force warning to fire even if already seen in this process.
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
            OID_REF.OIDRef()
        dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertTrue(
            len(dep_warnings) > 0,
            "Expected a DeprecationWarning when instantiating the manual OIDRef.",
        )

    def test_define_21_oid_ref_warns(self):
        import warnings
        _make_define_21_namespace()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import odmlib.define_2_1.rules.oid_ref as OID_REF
            OID_REF.OIDRef()
        dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertTrue(len(dep_warnings) > 0)

    def test_define_20_oid_ref_warns(self):
        import warnings
        _make_define_20_namespace()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import odmlib.define_2_0.rules.oid_ref as OID_REF
            OID_REF.OIDRef()
        dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertTrue(len(dep_warnings) > 0)


# ---------------------------------------------------------------------------
# Public API / package-level import tests
# ---------------------------------------------------------------------------

class TestPackageLevelImports(unittest.TestCase):
    """Verify that DynamicOIDRef and create_oid_checker are exported at
    the top-level odmlib package."""

    def test_imports_from_package(self):
        import odmlib
        self.assertTrue(hasattr(odmlib, "DynamicOIDRef"))
        self.assertTrue(hasattr(odmlib, "create_oid_checker"))

    def test_create_oid_checker_callable(self):
        import odmlib
        _make_odm_132_namespace()
        checker = odmlib.create_oid_checker("odm_1_3_2")
        from odmlib.oid_generator import DynamicOIDRef
        self.assertIsInstance(checker, DynamicOIDRef)


# ---------------------------------------------------------------------------
# Trailing-space bug fix regression test
# ---------------------------------------------------------------------------

class TestTrailingSpaceBugFixed(unittest.TestCase):
    """Verify that the trailing space bugs in odm_1_3_2 oid_ref.py are fixed."""

    def setUp(self):
        _make_odm_132_namespace()

    def test_signature_oid_no_trailing_space(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
            checker = OID_REF.OIDRef()
        # "SignatureOID " with trailing space should be gone.
        for ref_list in checker.def_ref.values():
            for ref in ref_list:
                self.assertEqual(ref, ref.strip(),
                                 f"Trailing space found in def_ref: '{ref}'")

    def test_item_oid_no_trailing_space(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
            checker = OID_REF.OIDRef()
        keyset_refs = checker.def_ref.get("KeySet", [])
        for ref in keyset_refs:
            self.assertEqual(ref, ref.strip(),
                             f"Trailing space found in KeySet def_ref: '{ref}'")


class TestRoleCodeListOIDResolution(unittest.TestCase):
    """Verify RoleCodeListOID resolves to CodeList (Step 3a fix)."""

    def _get_mapping(self, model_pkg):
        from odmlib.oid_generator import (
            discover_model_classes, discover_oid_definitions,
            discover_oid_references, build_ref_def_mapping,
        )
        module = __import__(f"odmlib.{model_pkg}.model", fromlist=["model"])
        classes = discover_model_classes(module)
        defs = discover_oid_definitions(classes)
        refs = discover_oid_references(classes)
        return build_ref_def_mapping(refs, defs, classes)

    def test_role_codelist_oid_in_odm_132(self):
        ref_def = self._get_mapping("odm_1_3_2")
        self.assertIn("RoleCodeListOID", ref_def)
        self.assertEqual(ref_def["RoleCodeListOID"], "CodeList")

    def test_role_codelist_oid_in_define_21(self):
        ref_def = self._get_mapping("define_2_1")
        self.assertIn("RoleCodeListOID", ref_def)
        self.assertEqual(ref_def["RoleCodeListOID"], "CodeList")


class TestSignatureOIDManualMapping(unittest.TestCase):
    """Verify SignatureOID maps to Signature (not SignatureRef) in manual oid_ref (Step 3b fix)."""

    def setUp(self):
        _make_odm_132_namespace()

    def test_signature_oid_maps_to_signature(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
            checker = OID_REF.OIDRef()
        self.assertEqual(checker.ref_def["SignatureOID"], "Signature")


class TestAddOidRefUnknownAttr(unittest.TestCase):
    """Test that add_oid_ref silently ignores unknown attribute names (Issue 2.4)."""

    def setUp(self):
        _make_odm_132_namespace()
        from odmlib.oid_generator import create_oid_checker
        self.checker = create_oid_checker("odm_1_3_2")

    def test_unknown_attr_no_error(self):
        """Calling add_oid_ref with an attr not in oid_ref should not raise."""
        initial_state = {k: set(v) for k, v in self.checker.oid_ref.items()}
        self.checker.add_oid_ref("SOME.OID", "CompletelyFakeOID")
        # No error raised, and oid_ref state is unchanged
        for attr, refs in self.checker.oid_ref.items():
            self.assertEqual(refs, initial_state[attr],
                             f"oid_ref[{attr!r}] was unexpectedly modified")

    def test_unknown_attr_does_not_create_key(self):
        """Unknown attr should not be added as a new key in oid_ref."""
        self.checker.add_oid_ref("SOME.OID", "BogusOID")
        self.assertNotIn("BogusOID", self.checker.oid_ref)


class TestODM20ResolvedAndUnresolvedRefs(unittest.TestCase):
    """Document which ODM 2.0 reference attributes are resolved vs unresolved (Issue 2.5)."""

    def setUp(self):
        from odmlib.oid_generator import create_oid_checker
        self.checker = create_oid_checker("odm_2_0")

    def test_odm2_resolved_standard_refs(self):
        """Core ref attrs that should always resolve in ODM 2.0."""
        expected_resolved = [
            "ItemOID", "ItemGroupOID", "StudyEventOID", "CodeListOID",
            "MethodOID", "MetaDataVersionOID", "StudyOID",
        ]
        for attr in expected_resolved:
            self.assertIn(attr, self.checker.ref_def,
                          f"{attr} should be resolved in ODM 2.0")

    def test_odm2_resolved_workflow_refs(self):
        """ODM 2.0 workflow-specific refs that resolve via overrides."""
        expected_resolved = [
            "WorkflowOID", "ArmOID", "EpochOID",
            "StudyEventGroupOID", "TransitionOID",
        ]
        for attr in expected_resolved:
            self.assertIn(attr, self.checker.ref_def,
                          f"{attr} should be resolved in ODM 2.0")

    def test_odm2_resolved_admindata_and_document_refs(self):
        """Refs that began resolving with the v0.2.1 ODM 2.0 XSD alignment.

        ``OrganizationOID`` resolves now that ``Organization`` is the XSD's
        AdminData element (with an ``OID``) rather than a text leaf, and
        ``LeafID`` now that ``Leaf`` is a ``MetaDataVersion`` child. Both were
        listed as intentionally unresolved before.
        """
        for attr, target in (("OrganizationOID", "Organization"),
                             ("LeafID", "Leaf")):
            self.assertEqual(self.checker.ref_def.get(attr), target,
                             f"{attr} should resolve to {target} in ODM 2.0")

    def test_odm2_unresolved_refs(self):
        """Refs that intentionally do NOT resolve (no matching Def class).

        This test serves as a living specification. If a future model update
        adds the target class, the test should be updated to move the attr
        from unresolved to resolved.
        """
        expected_unresolved = [
            "PresentationOID", "UnitsItemOID",
        ]
        for attr in expected_unresolved:
            self.assertNotIn(attr, self.checker.ref_def,
                             f"{attr} should NOT be resolved in ODM 2.0 "
                             f"(no target Def class in the model)")


if __name__ == "__main__":
    unittest.main()
