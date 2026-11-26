"""Property-based tests using Hypothesis for odmlib validation logic.

These tests generate random but structured inputs to exercise edge cases in
type validation, OID handling, and element construction.  They complement
the deterministic unit tests by systematically exploring the input space
that manual tests may miss.

Requires hypothesis>=6.0 (installed via ``pip install odmlib[test]`` or
``pip install odmlib[dev]``).
"""
import json
import re
import pytest

# The class bodies below evaluate @given(...) and st.* at import time, so the
# module must be skipped before they run. A try/except with a skipif marker is
# not enough: without hypothesis, ``given`` is undefined and the module fails
# to import, which is a collection error rather than a skip.
pytest.importorskip(
    "hypothesis", reason="hypothesis not installed — install with pip install odmlib[test]")

from hypothesis import given, strategies as st, assume, settings, HealthCheck  # noqa: E402

import odmlib.odm_1_3_2.model as ODM  # noqa: E402
from odmlib.exceptions import OdmlibTypeError, OdmlibValidationError  # noqa: E402
import odmlib.ns_registry as NS  # noqa: E402


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

_XS_INTEGER = re.compile(r"[+-]?[0-9]+")
_XML_WHITESPACE = " \t\n\r"

# Valid OID: starts with a letter, then alphanumeric / dot / underscore
oid_strategy = st.from_regex(r"[A-Za-z][A-Za-z0-9._]{0,63}", fullmatch=True)

# Valid Name: non-empty printable text, stripped of leading/trailing whitespace
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Pd", "Pc")),
    min_size=1,
    max_size=64,
).filter(lambda s: s.strip() == s and len(s) > 0)

# Valid DataType values for ItemDef in ODM 1.3.2
data_type_strategy = st.sampled_from([
    "text", "integer", "float", "date", "time", "datetime",
    "string", "boolean",
])


# ---------------------------------------------------------------------------
# OID round-trips
# ---------------------------------------------------------------------------

class TestOIDRoundTrips:
    """OID values must survive serialisation round-trips without mutation."""

    @given(oid=oid_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_def_oid_survives_to_dict(self, oid):
        """OID set on ItemDef must equal the OID in to_dict() output."""
        item = ODM.ItemDef(OID=oid, Name="Test", DataType="text")
        d = item.to_dict()
        assert d["OID"] == oid

    @given(oid=oid_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_def_oid_survives_to_json(self, oid):
        """OID set on ItemDef must equal the OID in the JSON output."""
        item = ODM.ItemDef(OID=oid, Name="Test", DataType="text")
        data = json.loads(item.to_json())
        assert data["OID"] == oid

    @given(oid=oid_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_def_oid_survives_to_xml(self, oid):
        """OID set on ItemDef must equal the OID in the XML element."""
        item = ODM.ItemDef(OID=oid, Name="Test", DataType="text")
        elem = item.to_xml()
        assert elem.attrib["OID"] == oid

    @given(oid=oid_strategy, name=name_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_def_creation_with_valid_inputs(self, oid, name):
        """ItemDef should accept any valid OID and Name without raising."""
        item = ODM.ItemDef(OID=oid, Name=name, DataType="text")
        assert item.OID == oid
        assert item.Name == name

    @given(oid=oid_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_codelist_oid_survives_json(self, oid):
        """CodeList OID must round-trip through JSON."""
        cl = ODM.CodeList(OID=oid, Name="Test", DataType="text")
        data = json.loads(cl.to_json())
        assert data["OID"] == oid

    @given(oid=oid_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_group_def_oid_survives_dict(self, oid):
        """ItemGroupDef OID must round-trip through to_dict()."""
        igd = ODM.ItemGroupDef(OID=oid, Name="Test", Repeating="No", SASDatasetName="TEST")
        d = igd.to_dict()
        assert d["OID"] == oid


# ---------------------------------------------------------------------------
# Integer descriptor
# ---------------------------------------------------------------------------

class TestIntegerDescriptor:
    """The Integer descriptor should accept ints and int-convertible strings."""

    @given(value=st.integers(min_value=1, max_value=99999))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_positive_integers_accepted(self, value):
        """Any positive integer should be accepted for OrderNumber."""
        ir = ODM.ItemRef(ItemOID="IT.TEST", OrderNumber=value, Mandatory="Yes")
        assert ir.OrderNumber == value

    @given(value=st.integers(min_value=1, max_value=99999))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_integer_as_string_accepted(self, value):
        """Integer values provided as strings are auto-converted."""
        ir = ODM.ItemRef(ItemOID="IT.TEST", OrderNumber=str(value), Mandatory="Yes")
        assert ir.OrderNumber == value

    @given(value=st.text(min_size=1, max_size=10).filter(
        # Keep only strings outside the xs:integer lexical space: an optional
        # sign and ASCII digits, after stripping XML whitespace. str.isdigit()
        # is the wrong test -- it is true for Arabic-Indic digits and
        # superscripts, which the XSD rejects -- and int() also accepts "1_0".
        lambda s: not _XS_INTEGER.fullmatch(s.strip(_XML_WHITESPACE))
    ))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_non_numeric_string_raises(self, value):
        """Strings outside xs:integer must raise OdmlibTypeError for integer fields."""
        with pytest.raises(OdmlibTypeError):
            ODM.ItemRef(ItemOID="IT.TEST", OrderNumber=value, Mandatory="Yes")

    @given(value=st.floats(allow_nan=False, allow_infinity=False).filter(
        lambda x: x != int(x)  # must NOT be a whole number (e.g. 3.5, not 3.0)
    ))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_non_integer_float_raises(self, value):
        """Float values that are not whole numbers must raise OdmlibTypeError."""
        with pytest.raises(OdmlibTypeError):
            ODM.ItemRef(ItemOID="IT.TEST", OrderNumber=value, Mandatory="Yes")


# ---------------------------------------------------------------------------
# ValueSetString descriptor
# ---------------------------------------------------------------------------

class TestValueSetStringDescriptor:
    """ValueSetString rejects values not in the declared valueset."""

    @given(value=st.sampled_from(["Yes", "No"]))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mandatory_accepts_yes_no(self, value):
        """Mandatory accepts 'Yes' and 'No'."""
        ir = ODM.ItemRef(ItemOID="IT.TEST", Mandatory=value)
        assert ir.Mandatory == value

    @given(value=st.text(min_size=1, max_size=20))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mandatory_rejects_arbitrary_strings(self, value):
        """Mandatory rejects values other than 'Yes'/'No'."""
        assume(value not in ("Yes", "No"))
        with pytest.raises((OdmlibTypeError, OdmlibValidationError)):
            ODM.ItemRef(ItemOID="IT.TEST", Mandatory=value)

    @given(value=st.sampled_from(["text", "integer", "float", "date", "time", "datetime"]))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_data_type_accepts_valid_values(self, value):
        """DataType accepts standard ODM data type strings."""
        item = ODM.ItemDef(OID="IT.TEST", Name="Test", DataType=value)
        assert item.DataType == value

    @given(value=st.text(min_size=1, max_size=20))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_data_type_raises(self, value):
        """DataType rejects arbitrary strings not in the valueset."""
        from odmlib.valueset import ValueSet
        valid = ValueSet.value_set("ItemDef.DataType", version="odm_1_3_2")
        assume(value not in valid)
        with pytest.raises((OdmlibTypeError, OdmlibValidationError)):
            ODM.ItemDef(OID="IT.TEST", Name="Test", DataType=value)

    @given(value=st.sampled_from(["Snapshot", "Transactional"]))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_file_type_accepts_valid_values(self, value):
        """ODM.FileType accepts 'Snapshot' and 'Transactional'."""
        odm = ODM.ODM(
            FileOID="F.TEST", FileType=value,
            CreationDateTime="2024-01-01T00:00:00",
        )
        assert odm.FileType == value


# ---------------------------------------------------------------------------
# String descriptor
# ---------------------------------------------------------------------------

class TestStringDescriptor:
    """String descriptors accept any str and reject non-str values."""

    @given(value=st.text(min_size=0, max_size=256))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_any_string_accepted_for_name(self, value):
        """Name descriptor accepts any Python str (including empty)."""
        tt = ODM.TranslatedText(_content=value, lang="en")
        assert tt._content == value

    @given(value=st.one_of(st.integers(), st.floats(allow_nan=False)))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_non_string_raises_for_string_field(self, value):
        """Numeric values must be rejected for String descriptor fields."""
        with pytest.raises(OdmlibTypeError):
            ODM.TranslatedText(_content=value, lang="en")


# ---------------------------------------------------------------------------
# Structural invariants
# ---------------------------------------------------------------------------

class TestStructuralInvariants:
    """Structural properties that must hold for any valid odmlib object."""

    @given(oid=oid_strategy)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_def_to_dict_keys(self, oid):
        """to_dict() on ItemDef always contains OID, Name, DataType."""
        item = ODM.ItemDef(OID=oid, Name="Test Item", DataType="text")
        d = item.to_dict()
        assert "OID"      in d
        assert "Name"     in d
        assert "DataType" in d

    @given(oid=oid_strategy)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_to_json_is_valid_json(self, oid):
        """to_json() must always produce parseable JSON."""
        item = ODM.ItemDef(OID=oid, Name="Test", DataType="text")
        raw = item.to_json()
        parsed = json.loads(raw)   # raises ValueError if not valid JSON
        assert isinstance(parsed, dict)

    @given(oid=oid_strategy, name=name_strategy)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_to_xml_tag_equals_class_name(self, oid, name):
        """to_xml() root tag always matches the Python class name."""
        item = ODM.ItemDef(OID=oid, Name=name, DataType="text")
        elem = item.to_xml()
        assert elem.tag == "ItemDef"

    @given(n=st.integers(min_value=0, max_value=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_item_group_def_len_equals_item_ref_count(self, n):
        """len(ItemGroupDef) == number of ItemRef children appended."""
        igd = ODM.ItemGroupDef(OID="IG.TEST", Name="Test IG", Repeating="No",
                               SASDatasetName="TEST")
        for i in range(n):
            igd.ItemRef.append(ODM.ItemRef(ItemOID=f"IT.ITEM{i}", Mandatory="Yes"))
        assert len(igd) == n
