"""Tests for ODMElement.validate() with collect_errors=True.

The central guarantee under test: collect mode reports *every* problem each
validation layer can find, not just the first one per layer. Assertions use
exact counts — a `>=` bound cannot tell 1 error from N and would not catch a
regression to per-layer fail-fast.
"""
import os
import warnings
from collections import Counter
from unittest import TestCase

import odmlib.odm_1_3_2.model as ODM
import odmlib.odm_1_3_2.rules.metadata_schema as MS
import odmlib.odm_1_3_2.rules.oid_ref as OID_REF
from odmlib.mode import permissive, ValidationMode
from odmlib.oid_generator import create_oid_checker
from odmlib.exceptions import (
    OdmlibError,
    OdmlibElementOrderError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibErrorLimitError,
    OdmlibDeprecationWarning,
    OdmlibWarning,
    ErrorCollector,
    is_collecting_checker,
)

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _make_minimal_mdv():
    """Return a minimal but valid MetaDataVersion for testing."""
    ig_ref = ODM.ItemGroupRef(ItemGroupOID="IG.TEST", Mandatory="Yes")
    form_ref = ODM.FormRef(FormOID="F.TEST", Mandatory="Yes", OrderNumber=1)
    sed = ODM.StudyEventDef(OID="SE.TEST", Name="Test Event", Repeating="No", Type="Scheduled",
                            FormRef=[form_ref])

    item_ref = ODM.ItemRef(ItemOID="IT.TEST", Mandatory="No", OrderNumber=1)
    igd = ODM.ItemGroupDef(OID="IG.TEST", Name="Test Group", Repeating="No",
                           ItemRef=[item_ref])

    item = ODM.ItemDef(OID="IT.TEST", Name="Test Item", DataType="text")
    form = ODM.FormDef(OID="F.TEST", Name="Test Form", Repeating="No",
                       ItemGroupRef=[ig_ref])

    mdv = ODM.MetaDataVersion(OID="MDV.TEST", Name="Test MDV",
                              StudyEventDef=[sed],
                              FormDef=[form],
                              ItemGroupDef=[igd],
                              ItemDef=[item])
    return mdv


def _misordered_itemdef(oid):
    """ItemDef with Alias assigned before Description — out of model order.

    _elems requires Description first and Alias last, but __dict__ preserves
    assignment order, so this trips verify_order().
    """
    itd = ODM.ItemDef(OID=oid, Name="Test Item", DataType="text")
    itd.Alias = [ODM.Alias(Context="nci", Name="C12345")]
    description = ODM.Description()
    description.TranslatedText = [ODM.TranslatedText(_content="test", lang="en")]
    itd.Description = description
    return itd


def _deprecated_checker():
    """Build a deprecated manual OIDRef without polluting the warning log."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OdmlibDeprecationWarning)
        return OID_REF.OIDRef()


class TestValidateFailFast(TestCase):
    """validate() without collect_errors raises on the first error (default behaviour)."""

    def test_validate_returns_true_for_valid_object(self):
        mdv = _make_minimal_mdv()
        result = mdv.validate()
        self.assertTrue(result)

    def test_validate_raises_on_order_error(self):
        item = _misordered_itemdef("IT.TEST")
        with self.assertRaises(OdmlibElementOrderError):
            item.verify_order()

    def test_fail_fast_order_message_unchanged(self):
        """The collect-mode refactor must not alter the fail-fast message."""
        with self.assertRaises(OdmlibElementOrderError) as ctx:
            _misordered_itemdef("IT.TEST").verify_order()
        self.assertEqual(
            str(ctx.exception),
            "The order of elements in ItemDef should be Description, Question, "
            "ExternalQuestion, MeasurementUnitRef, RangeCheck, CodeListRef, Alias\n"
            "  Hint: Use reorder_object() to fix element ordering automatically",
        )

    def test_fail_fast_raises_on_first_of_many_order_errors(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.1"), _misordered_itemdef("IT.2")]
        with self.assertRaises(OdmlibElementOrderError):
            mdv.validate()

    def test_fail_fast_raises_on_first_duplicate_oid(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="c", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="d", DataType="text")]
        with self.assertRaises(OdmlibOIDError):
            mdv.validate(oid_checker=create_oid_checker("odm_1_3_2"))

    def test_fail_fast_conformance_raises_single_bundled_error(self):
        with permissive(ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET):
            igd1 = ODM.ItemGroupDef(OID="IG.1", Repeating="No")
            igd2 = ODM.ItemGroupDef(OID="IG.2", Name="g2", Repeating="Maybe")
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemGroupDef = [igd1, igd2]
        with self.assertRaises(OdmlibConformanceError) as ctx:
            mdv.validate(conformance_checker=MS.MetadataSchema())
        # Bundled, not expanded: every violation lives in one error.
        self.assertIsNone(ctx.exception.field_path)
        self.assertIn("ItemGroupDef", ctx.exception.cerberus_errors)

    def test_fail_fast_ignores_max_errors(self):
        self.assertTrue(_make_minimal_mdv().validate(max_errors=1))


class TestValidateCollectErrors(TestCase):
    """validate(collect_errors=True) returns a list of all errors."""

    def test_collect_returns_empty_list_for_valid_object(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True)
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 0)

    def test_collect_errors_true_returns_list_not_bool(self):
        mdv = _make_minimal_mdv()
        result = mdv.validate(collect_errors=True)
        # Even when valid, returns a list (not True)
        self.assertIsInstance(result, list)

    def test_collect_errors_skips_oid_check_when_no_checker(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, oid_checker=None)
        self.assertEqual(errors, [])

    def test_collect_errors_skips_conformance_when_no_checker(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, conformance_checker=None)
        self.assertEqual(errors, [])

    def test_collect_errors_with_conformance(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True, conformance_checker=MS.MetadataSchema())
        self.assertEqual(errors, [])


class TestCollectEveryOrderError(TestCase):
    """The order layer enumerates every misordered element, not just the first."""

    def test_collect_reports_every_misordered_element(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.1"), _misordered_itemdef("IT.2")]
        errors = mdv.validate(collect_errors=True)
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(isinstance(e, OdmlibElementOrderError) for e in errors))
        self.assertEqual([e.element_path for e in errors],
                         ["ItemDef(OID=IT.1)", "ItemDef(OID=IT.2)"])

    def test_collect_recurses_into_misordered_parent(self):
        """A misordered parent must not stop the walk into its children."""
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        # ItemDef assigned before ItemGroupDef => MDV itself is misordered
        mdv.ItemDef = [_misordered_itemdef("IT.1")]
        mdv.ItemGroupDef = [ODM.ItemGroupDef(OID="IG.1", Name="g", Repeating="No")]
        errors = mdv.validate(collect_errors=True)
        self.assertEqual(len(errors), 2)
        self.assertEqual([e.element_type for e in errors], ["MetaDataVersion", "ItemDef"])

    def test_collected_order_error_message_matches_fail_fast(self):
        """element_path is stamped after construction, so str() is unchanged."""
        item = _misordered_itemdef("IT.1")
        collected = item.validate(collect_errors=True)[0]
        with self.assertRaises(OdmlibElementOrderError) as ctx:
            item.verify_order()
        self.assertEqual(str(collected), str(ctx.exception))


class TestCollectEveryOIDError(TestCase):
    """The OID layer enumerates every duplicate and every bad reference."""

    def test_collect_reports_every_duplicate_oid(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="c", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="d", DataType="text")]
        errors = mdv.validate(collect_errors=True,
                              oid_checker=create_oid_checker("odm_1_3_2"))
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(isinstance(e, OdmlibOIDError) for e in errors))

    def test_duplicate_oid_keeps_first_definition(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="X.DUP", Name="a", DataType="text")]
        mdv.CodeList = [ODM.CodeList(OID="X.DUP", Name="c", DataType="text")]
        checker = create_oid_checker("odm_1_3_2")
        errors = mdv.validate(collect_errors=True, oid_checker=checker)
        self.assertEqual(len(errors), 1)
        self.assertEqual(checker.oid["X.DUP"], "ItemDef")
        self.assertEqual(checker.unique_oids["X.DUP"], "ItemDef")

    def test_duplicate_oid_does_not_abort_reference_checks(self):
        """Regression: add_oid used to abort the walk so check_oid_refs never ran."""
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        igd = ODM.ItemGroupDef(OID="IG.1", Name="g", Repeating="No")
        igd.ItemRef = [ODM.ItemRef(ItemOID="IT.MISSING", Mandatory="Yes")]
        mdv.ItemGroupDef = [igd]
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text")]
        errors = mdv.validate(collect_errors=True,
                              oid_checker=create_oid_checker("odm_1_3_2"))
        messages = " ".join(str(e) for e in errors)
        self.assertEqual(len(errors), 2)
        self.assertIn("is not unique", messages)
        self.assertIn("IT.MISSING", messages)

    def test_collect_reports_dangling_and_mistyped_refs_together(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        igd = ODM.ItemGroupDef(OID="IG.1", Name="g", Repeating="No")
        igd.ItemRef = [ODM.ItemRef(ItemOID="IT.MISSING", Mandatory="Yes"),
                       ODM.ItemRef(ItemOID="CL.SEX", Mandatory="Yes")]  # a CodeList
        mdv.ItemGroupDef = [igd]
        mdv.CodeList = [ODM.CodeList(OID="CL.SEX", Name="Sex", DataType="text")]
        errors = mdv.validate(collect_errors=True,
                              oid_checker=create_oid_checker("odm_1_3_2"))
        self.assertEqual(len(errors), 2)
        # sorted(oid_set) pins the order: "CL.SEX" < "IT.MISSING"
        self.assertIn("element types do not match", str(errors[0]))
        self.assertIn("IT.MISSING", str(errors[1]))

    def test_reference_errors_are_deterministically_ordered(self):
        """check_oid_refs sorts its set, so repeated runs agree."""
        def run():
            mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
            igd = ODM.ItemGroupDef(OID="IG.1", Name="g", Repeating="No")
            igd.ItemRef = [ODM.ItemRef(ItemOID=f"IT.MISSING{i}", Mandatory="Yes")
                           for i in range(6)]
            mdv.ItemGroupDef = [igd]
            return [str(e) for e in mdv.validate(
                collect_errors=True, oid_checker=create_oid_checker("odm_1_3_2"))]

        first = run()
        self.assertEqual(len(first), 6)
        self.assertEqual(first, run())


class TestCollectEveryConformanceError(TestCase):
    """The conformance layer expands the bundled cerberus result."""

    def _mdv_with_two_violations(self):
        with permissive(ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET):
            igd1 = ODM.ItemGroupDef(OID="IG.1", Repeating="No")               # no Name
            igd2 = ODM.ItemGroupDef(OID="IG.2", Name="g2", Repeating="Maybe")  # bad enum
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemGroupDef = [igd1, igd2]
        return mdv

    def test_conformance_errors_expand_one_per_field(self):
        errors = self._mdv_with_two_violations().validate(
            collect_errors=True, conformance_checker=MS.MetadataSchema())
        self.assertEqual(len(errors), 2)
        self.assertEqual([e.field_path for e in errors],
                         ["ItemGroupDef.0.Name", "ItemGroupDef.1.Repeating"])
        self.assertEqual(errors[0].attribute, "Name")
        self.assertEqual(errors[0].element_path, "ItemGroupDef.0")
        self.assertIn("required field", str(errors[0]))

    def test_expanded_errors_share_the_full_cerberus_dict(self):
        errors = self._mdv_with_two_violations().validate(
            collect_errors=True, conformance_checker=MS.MetadataSchema())
        self.assertIs(errors[0].cerberus_errors, errors[1].cerberus_errors)
        self.assertIn("ItemGroupDef", errors[0].cerberus_errors)


class TestCollectAcrossLayers(TestCase):
    """All three layers contribute in one pass."""

    def test_collect_reports_all_three_layers(self):
        with permissive(ValidationMode.SKIP_REQUIRED):
            bad_igd = ODM.ItemGroupDef(OID="IG.1", Repeating="No")     # conformance
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemGroupDef = [bad_igd]
        mdv.ItemDef = [_misordered_itemdef("IT.DUP"),                  # order
                       _misordered_itemdef("IT.DUP")]                  # order + dup OID
        errors = mdv.validate(collect_errors=True,
                              oid_checker=create_oid_checker("odm_1_3_2"),
                              conformance_checker=MS.MetadataSchema())
        kinds = Counter(type(e).__name__ for e in errors)
        self.assertEqual(kinds["OdmlibElementOrderError"], 2)
        self.assertEqual(kinds["OdmlibOIDError"], 1)
        self.assertEqual(kinds["OdmlibConformanceError"], 1)
        self.assertEqual(len(errors), 4)


class TestMaxErrors(TestCase):
    """max_errors caps collection and marks the result as truncated."""

    def _mdv_with_ten_order_errors(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef(f"IT.{i}") for i in range(10)]
        return mdv

    def test_max_errors_caps_collection(self):
        errors = self._mdv_with_ten_order_errors().validate(collect_errors=True, max_errors=3)
        self.assertEqual(len(errors), 4)  # 3 errors + truncation marker
        self.assertIsInstance(errors[-1], OdmlibErrorLimitError)
        self.assertTrue(all(isinstance(e, OdmlibElementOrderError) for e in errors[:3]))
        self.assertIn("max_errors=3", str(errors[-1]))

    def test_max_errors_none_collects_everything(self):
        errors = self._mdv_with_ten_order_errors().validate(collect_errors=True)
        self.assertEqual(len(errors), 10)
        self.assertFalse(any(isinstance(e, OdmlibErrorLimitError) for e in errors))

    def test_max_errors_not_reached_adds_no_marker(self):
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.1"), _misordered_itemdef("IT.2")]
        errors = mdv.validate(collect_errors=True, max_errors=5)
        self.assertEqual(len(errors), 2)
        self.assertFalse(any(isinstance(e, OdmlibErrorLimitError) for e in errors))

    def test_max_errors_exactly_reached_adds_no_marker(self):
        """Finding exactly max_errors problems is not a truncation."""
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.1"), _misordered_itemdef("IT.2")]
        errors = mdv.validate(collect_errors=True, max_errors=2)
        self.assertEqual(len(errors), 2)
        self.assertFalse(any(isinstance(e, OdmlibErrorLimitError) for e in errors))

    def test_max_errors_zero_validates_nothing(self):
        """Degenerate but honest: nothing is checked, so nothing is known."""
        errors = _make_minimal_mdv().validate(collect_errors=True, max_errors=0)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], OdmlibErrorLimitError)

    def test_max_errors_stops_later_layers(self):
        """The cap is enforced inside the walk, not by slicing afterwards."""
        checker = create_oid_checker("odm_1_3_2")
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.DUP"), _misordered_itemdef("IT.DUP")]
        errors = mdv.validate(collect_errors=True, oid_checker=checker, max_errors=1)
        self.assertEqual(len(errors), 2)  # 1 order error + marker
        self.assertIsInstance(errors[-1], OdmlibErrorLimitError)
        # The OID layer never ran — proof the cap short-circuits rather than slices.
        self.assertEqual(checker.unique_oids, {})


class TestCheckerProtocol(TestCase):
    """Checkers without the collecting protocol still work, degraded."""

    def test_dynamic_checker_supports_protocol(self):
        self.assertTrue(is_collecting_checker(create_oid_checker("odm_1_3_2")))

    def test_deprecated_oidref_does_not_support_protocol(self):
        self.assertFalse(is_collecting_checker(_deprecated_checker()))

    def test_deprecated_oidref_degrades_to_single_error(self):
        checker = _deprecated_checker()
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="c", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="d", DataType="text")]
        errors = mdv.validate(collect_errors=True, oid_checker=checker)
        self.assertEqual(len(errors), 1)   # documented degradation
        self.assertIsInstance(errors[0], OdmlibOIDError)

    def test_duck_typed_checker_without_protocol_degrades(self):
        class MinimalChecker:
            def add_oid(self, oid, element):
                pass

            def add_oid_ref(self, oid, attr):
                pass

            def check_oid_refs(self):
                raise OdmlibOIDError("boom")

        errors = _make_minimal_mdv().validate(collect_errors=True,
                                              oid_checker=MinimalChecker())
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], OdmlibOIDError)

    def test_non_odmlib_exception_propagates(self):
        """A bug in a checker is not a document defect — it must not be collected."""
        class Boom:
            def add_oid(self, oid, element):
                raise RuntimeError("boom")

            def add_oid_ref(self, oid, attr):
                pass

            def check_oid_refs(self):
                return True

        with self.assertRaises(RuntimeError):
            _make_minimal_mdv().validate(collect_errors=True, oid_checker=Boom())

    def test_collect_includes_oid_error_deprecated_checker(self):
        checker = _deprecated_checker()
        # Deliberately pre-seed a bad ref/def mapping to force a check failure
        checker.oid["IT.MISSING"] = "WRONG_TYPE"
        checker.oid_ref["ItemOID"].add("IT.MISSING")

        mdv = _make_minimal_mdv()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", OdmlibWarning)
            errors = mdv.validate(collect_errors=True, oid_checker=checker)
        self.assertEqual(len(errors), 1)
        self.assertTrue(all(isinstance(e, OdmlibError) for e in errors))
        self.assertIn("element types do not match", str(errors[0]))

    def test_dirty_checker_warns(self):
        checker = create_oid_checker("odm_1_3_2")
        _make_minimal_mdv().validate(collect_errors=True, oid_checker=checker)
        with self.assertWarns(OdmlibWarning):
            _make_minimal_mdv().validate(collect_errors=True, oid_checker=checker)

    def test_checker_reset_clears_state(self):
        checker = create_oid_checker("odm_1_3_2")
        mdv = _make_minimal_mdv()
        self.assertEqual(mdv.validate(collect_errors=True, oid_checker=checker), [])
        checker.reset()
        self.assertEqual(checker.oid, {})
        self.assertEqual(checker.unique_oids, {})
        self.assertFalse(checker.is_verified)
        # A reset checker validates the same document cleanly a second time.
        self.assertEqual(mdv.validate(collect_errors=True, oid_checker=checker), [])

    def test_verify_oids_collects_when_sink_installed(self):
        """The public verify_oids() collects inside a collecting() block."""
        checker = create_oid_checker("odm_1_3_2")
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="c", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="d", DataType="text")]
        collector = ErrorCollector()
        with checker.collecting(collector):
            mdv.verify_oids(checker)
        self.assertEqual(len(collector.errors), 2)

    def test_sink_restored_after_collecting_block(self):
        checker = create_oid_checker("odm_1_3_2")
        with checker.collecting(ErrorCollector()):
            pass
        self.assertIsNone(checker._error_sink)
        # Back to fail-fast
        checker.add_oid("A", "ItemDef")
        with self.assertRaises(OdmlibOIDError):
            checker.add_oid("A", "CodeList")

    def test_sink_restored_when_limit_unwinds_layer(self):
        """The max_errors sentinel must not leave a sink installed."""
        checker = create_oid_checker("odm_1_3_2")
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [ODM.ItemDef(OID="IT.DUP", Name="a", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP", Name="b", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="c", DataType="text"),
                       ODM.ItemDef(OID="IT.DUP2", Name="d", DataType="text")]
        errors = mdv.validate(collect_errors=True, oid_checker=checker, max_errors=1)
        self.assertIsInstance(errors[-1], OdmlibErrorLimitError)
        self.assertIsNone(checker._error_sink)


class TestErrorCollectorWithValidate(TestCase):
    """ErrorCollector can be used alongside validate() results."""

    def test_collect_then_raise_if_errors(self):
        """Collect all errors then raise summary."""
        mdv = ODM.MetaDataVersion(OID="MDV.1", Name="M")
        mdv.ItemDef = [_misordered_itemdef("IT.1"), _misordered_itemdef("IT.2")]
        errors = mdv.validate(collect_errors=True)

        collector = ErrorCollector()
        for err in errors:
            collector.add_error(err)
        self.assertTrue(collector.has_errors)
        with self.assertRaises(OdmlibError) as ctx:
            collector.raise_if_errors()
        self.assertIn("2 validation errors found", str(ctx.exception))

    def test_empty_results_means_valid(self):
        mdv = _make_minimal_mdv()
        errors = mdv.validate(collect_errors=True)
        collector = ErrorCollector()
        for err in errors:
            collector.add_error(err)
        self.assertFalse(collector.has_errors)
        collector.raise_if_errors()  # should not raise
