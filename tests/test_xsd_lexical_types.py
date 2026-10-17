"""Typed descriptors accept exactly what the XSD types they model accept.

Each descriptor is compared with xmlschema's own validation of the matching type in
the bundled ODM 2.0 schema, over a generated corpus of valid, invalid and edge-case
values. A value either side accepts that the other rejects is a failure: odmlib must
not refuse a schema-valid document, nor build one the schema rejects.

Covers the crfutils plan §4A items:

- O2: ``TimepointString`` (``AbsoluteTimingConstraint/@TimepointTarget``);
- O9: ``DateTimeString`` (xs:dateTime edge cases), the ``Incomplete*`` unions,
  ``DurationDateTimeString`` (whitespace), ``Float`` (xs:decimal), ``ID``/``IDRef``
  (NCName), ``Language`` (xs:language) and the non-empty ``OID``/``OIDRef``/``Name``.

The comparison runs in strict mode, where each descriptor raises a ``ValueError`` or
``TypeError`` subclass for a value it rejects.
"""
import itertools
import unittest

import odmlib.odm_element as OE
import odmlib.typed as T
from odmlib.odm_parser import ODMSchemaValidator

ODM = "{http://www.cdisc.org/ns/odm/v2.0}"
XS = "{http://www.w3.org/2001/XMLSchema}"


def _temporal_corpus():
    """Dates, times, datetimes, partial and incomplete forms, durations and junk."""
    years = ["2021", "2020", "1900", "2000", "0000", "0001", "-0001", "-0004", "-0005",
             "10000", "02021", "999", "-10000"]
    months = ["01", "02", "04", "12", "13", "00", "1"]
    days = ["01", "28", "29", "30", "31", "32", "00", "1"]
    clocks = ["00:00:00", "23:59:59", "24:00:00", "24:00:00.000", "24:00:00.5",
              "24:00:01", "12:30:00.25", "12:30:00.", "12:60:00", "25:00:00", "12:30",
              "12", "-:05:-", "12:-:-"]
    zones = ["", "Z", "+05:30", "-14:00", "+14:00", "+14:01", "+15:00", "+23:59",
             "-24:00", "05:00", "z"]
    corpus = set()
    for year, month, day in itertools.product(years, months, days):
        corpus.add(f"{year}-{month}-{day}")
    for year, month in itertools.product(years, months):
        corpus.add(f"{year}-{month}")
    corpus.update(years)
    for clock, zone in itertools.product(clocks, zones):
        corpus.add(clock + zone)
    dates = ["2021-02-28", "2021-02-29", "2020-02-29", "2021-04-31", "2021-01-15"]
    for year, date, clock, zone in itertools.product(
            ["2021", "2020", "0000", "-0001", "10000"], dates, clocks, zones):
        corpus.add(date.replace("2021", year, 1) + "T" + clock + zone)
    for value in ["2021-01-15", "2021-01", "2021", "12:30:00", "2021-01-15T12:30:00Z",
                  "P3D", "P2W", "PT1H"]:
        for wrap in [" {}", "{} ", " {} ", "\n{}", "{}\n", "\t{}\t"]:
            corpus.add(wrap.format(value))
    for year, month, day in [("2021", "-", "15"), ("-", "-", "-"), ("2021", "12", "-"),
                             ("-", "02", "29")]:
        corpus.add(f"{year}-{month}-{day}")
        corpus.add(f"{year}-{month}-{day}T-:05:-")
        corpus.add(f"{year}-{month}-{day}T12:30:15.5Z")
    corpus.update({
        "", " ", "  ", "\n", "\t", "abc", "2021-1-1", "T12:00:00", "2021-01-01T",
        "P", "PT", "P1D", "-P1D", "+P1D", "P1W", "+P1W", "-P1W", "P1Y2W",
        "P1Y2M3DT4H5M6.7S", "P1.5D", "PT.5S", "P1DT", "P\u0663D", "PT1H30M", "P0D",
        "--01", "---01", "2021-01-01Z", "2021-01-01+14:00", "2021-01-01-05:00",
    })
    return sorted(corpus)


TEMPORAL_CORPUS = _temporal_corpus()


class TestDescriptorsMatchXSD(unittest.TestCase):
    """Descriptor acceptance equals xmlschema acceptance, value for value."""

    @classmethod
    def setUpClass(cls):
        cls.schema = ODMSchemaValidator(standard="odm", version="2.0").xsd

    def _type(self, name):
        return self.schema.maps.types[name if name.startswith("{") else ODM + name]

    def _assert_matches(self, descriptor_name, xsd_type, values):
        model = type(f"Probe{descriptor_name}", (OE.ODMElement,),
                     {"V": getattr(T, descriptor_name)()})
        mismatches = []
        for value in values:
            try:
                model(V=value)
                accepted = True
            except (ValueError, TypeError):
                accepted = False
            if accepted != xsd_type.is_valid(value):
                mismatches.append(f"{value!r}: odmlib {'accepts' if accepted else 'rejects'}")
        self.assertEqual(mismatches, [], f"{descriptor_name} disagrees with the XSD")

    def test_timepoint_target(self):
        """O2: the anonymous union on AbsoluteTimingConstraint/@TimepointTarget."""
        xsd_type = self.schema.elements["AbsoluteTimingConstraint"].type \
            .attributes["TimepointTarget"].type
        self._assert_matches("TimepointString", xsd_type, TEMPORAL_CORPUS)

    def test_datetime(self):
        self._assert_matches("DateTimeString", self._type("datetime"), TEMPORAL_CORPUS)

    def test_incomplete_datetime(self):
        self._assert_matches("IncompleteDateTimeString", self._type("incompleteDatetime"),
                             TEMPORAL_CORPUS)

    def test_incomplete_date(self):
        self._assert_matches("IncompleteDateString", self._type("incompleteDate"),
                             TEMPORAL_CORPUS)

    def test_incomplete_time(self):
        self._assert_matches("IncompleteTimeString", self._type("incompleteTime"),
                             TEMPORAL_CORPUS)

    def test_duration(self):
        self._assert_matches("DurationDateTimeString", self._type("durationDatetime"),
                             TEMPORAL_CORPUS)

    def test_decimal(self):
        self._assert_matches("Float", self._type("decimal"), [
            "1", "1.0", "-1", "+1", ".5", "5.", "-.5", "1.10", " 2.5 ", "\n3\n",
            "00012.5000", "1e3", "1E3", "nan", "NaN", "inf", "INF", "-inf", "1_000", "",
            " ", "abc", "0x10", "1,5", "--1", "+-1", "1.2.3", "\u0663"])

    def test_id_and_idref(self):
        values = ["LF.1", "_x", "a-b.c", "1", "1A", "-a", ".a", "a b", "a:b", "", " ",
                  " LF.1 ", "\u00E9", "\u00DCn\u00EFcode", "a\u00B7b", "x\u0301",
                  "\u0300x", "a$"]
        self._assert_matches("ID", self.schema.maps.types[XS + "ID"], values)
        self._assert_matches("IDRef", self.schema.maps.types[XS + "IDREF"], values)

    def test_language(self):
        self._assert_matches("Language", self.schema.maps.types[XS + "language"], [
            "en", "en-US", "EN", "zh-Hant-TW", "x-klingon", "en_US", "", " en ",
            "abcdefghi", "en-abcdefghi", "e1", "1en", "de-1996", "-en", "en-"])

    def test_oid_oidref_name_are_non_empty(self):
        values = ["IT.1", "", " ", "a b"]
        self._assert_matches("OID", self._type("oid"), values)
        self._assert_matches("OIDRef", self._type("oidref"), values)
        self._assert_matches("Name", self._type("name"), values)


class TestDescriptorBehaviour(unittest.TestCase):
    """Details the XSD comparison does not show."""

    def test_float_stores_a_float(self):
        model = type("FloatProbe", (OE.ODMElement,), {"V": T.Float()})
        self.assertEqual(model(V=" 2.50 ").V, 2.5)
        self.assertEqual(model(V=3).V, 3.0)
        with self.assertRaises(TypeError):
            model(V=float("nan"))
        with self.assertRaises(TypeError):
            model(V=float("inf"))

    def test_values_are_stored_as_given(self):
        """Validation collapses whitespace; the stored value keeps it."""
        model = type("TimepointProbe", (OE.ODMElement,), {"V": T.TimepointString()})
        self.assertEqual(model(V=" 2021-01-01 ").V, " 2021-01-01 ")

    def test_non_string_temporal_value_is_a_validation_error(self):
        model = type("DateTimeProbe", (OE.ODMElement,), {"V": T.DateTimeString()})
        with self.assertRaises(ValueError):
            model(V=20210101)

    def test_permissive_mode_skips_format_checks(self):
        from odmlib.mode import permissive, ValidationMode
        model = type("NameProbe", (OE.ODMElement,),
                     {"N": T.Name(), "I": T.ID(), "D": T.DateTimeString()})
        with permissive(ValidationMode.SKIP_FORMAT):
            obj = model(N="", I="1 2", D="yesterday")
        self.assertEqual((obj.N, obj.I, obj.D), ("", "1 2", "yesterday"))


if __name__ == "__main__":
    unittest.main()
