"""Type-validated descriptors for ODM element attributes.

This module defines descriptor classes that enforce type validation
on ODM element attributes at assignment time. Each descriptor validates
the type, format, or enumerated values of the assigned value.

The descriptor hierarchy:
    - :class:`Typed` -- base type-checking descriptor
    - :class:`String`, :class:`OID`, :class:`OIDRef`, :class:`Name`, :class:`ID` -- string types
    - :class:`Integer`, :class:`Float` -- numeric types with string coercion
    - :class:`Positive`, :class:`NonNegative` -- numeric constraint mixins
    - :class:`PositiveInteger`, :class:`NonNegativeInteger` -- combined
    - :class:`Sized`, :class:`SizedString` -- length-constrained strings
    - :class:`Regex`, :class:`SizedRegexString` -- pattern-matching
    - :class:`DateTimeString`, :class:`DateString`, :class:`PartialDateTimeString`,
      :class:`PartialDateString`, :class:`PartialTimeString`,
      :class:`IncompleteDateTimeString`, :class:`IncompleteDateString`,
      :class:`IncompleteTimeString`, :class:`DurationDateTimeString`,
      :class:`TimepointString` -- temporal types
    - :class:`Language` -- ``xs:language`` codes (``xml:lang``)
    - :class:`SASName`, :class:`SASFormat` -- SAS naming constraints
    - :class:`Email`, :class:`Url`, :class:`FileName` -- format validators
    - :class:`ValidValues`, :class:`ExtendedValidValues` -- enumerated value validators
    - :class:`ValueSetString` -- combined enumerated + string validator
    - :class:`XHTMLDiv` -- an ``xhtml:div`` child carried as markup text
    - :class:`ODMObject` -- single child ODM element container
    - :class:`ODMListObject` -- list of child ODM elements container
"""
import odmlib.descriptor as DESC
import re
import math
import odmlib.valueset as VS
import odmlib.interleave as IL
import odmlib.xhtml as XH
import datetime
from validators import email as valid_email, url as valid_url
from pathvalidate import is_valid_filename
from odmlib.exceptions import OdmlibTypeError, OdmlibValidationError
import odmlib.mode as _mode


class Typed(DESC.Descriptor):
    """Base descriptor that validates value type on assignment.

    Subclasses set ``odm_type`` to the expected Python type.
    Raises :exc:`~odmlib.exceptions.OdmlibTypeError` on type mismatch.

    Attributes:
        odm_type (type): The expected Python type (default: object).
    """

    odm_type = object

    def __set__(self, instance, value):
        if (value is not None) and not isinstance(value, self.odm_type):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected type {str(self.odm_type)} for {self.name} with value {str(value)}",
                    attribute=self.name,
                    expected_type=str(self.odm_type),
                    actual_value=value,
                    hint=f"Provide a value of type {self.odm_type.__name__}",
                )
        # often does not call parent, calls next on __mro__ which maybe influenced by multiple inheritance
        super().__set__(instance, value)


class Integer(DESC.Descriptor):
    """Descriptor for integer-valued ODM attributes.

    Accepts int values and strings that convert to int (e.g., "42").
    Used for OrderNumber, KeySequence, and similar integer attributes.
    """

    def __set__(self, instance, value):
        # in XML integers are presented as strings e.g. OrderNumber="1"
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                    raise OdmlibTypeError(
                        f"Expected string to convert to integer for {self.name} with a value {str(value)}",
                        attribute=self.name,
                        actual_value=value,
                        hint="Provide a string that represents a valid integer, e.g., '42'",
                    )
                # permissive: fall through — store the string as-is
        odm_type = int
        if (value is not None) and not isinstance(value, odm_type):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected type {str(odm_type)} for {self.name} with value {str(value)}",
                    attribute=self.name,
                    expected_type=str(odm_type),
                    actual_value=value,
                    hint="Provide an integer or a string that can be converted to an integer",
                )
        super().__set__(instance, value)


class Float(DESC.Descriptor):
    """Descriptor for decimal-valued ODM attributes, stored as ``float``.

    Accepts float, int, and strings in the ``xs:decimal`` lexical space (``"1"``,
    ``"-2.5"``, ``".5"``; surrounding whitespace is ignored). Every attribute that uses
    it -- ``Rank`` on CodeListItem and EnumeratedItem, and ODM 2.0's GeoPosition
    coordinates -- is ``xs:decimal`` in its schema.

    .. versionchanged:: 0.3.0
       Strings are checked against ``xs:decimal`` before conversion. ``float()`` also
       accepts ``"1e3"``, ``"nan"``, ``"inf"`` and ``"1_000"``, none of which the XSD
       allows, and non-finite floats are now rejected too.
    """

    def __set__(self, instance, value):
        # in XML floats are presented as strings
        if isinstance(value, str):
            if _XS_DECIMAL_PAT.fullmatch(_xsd_collapse(value)):
                value = float(value)
            elif not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected string to convert to float for {self.name} with a value {str(value)}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide an xs:decimal string, e.g., '3.14' (no exponent, NaN or INF)",
                )
            # permissive: fall through — store the string as-is
        # convert integer into a float (e.g. 1 to 1.0)
        elif isinstance(value, int):
            value = float(value)
        if isinstance(value, float) and not math.isfinite(value):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected a finite decimal for {self.name}, found {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="xs:decimal has no NaN or infinity",
                )
        if (value is not None) and not isinstance(value, float):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected type float for {self.name} with value {str(value)}",
                    attribute=self.name,
                    expected_type="float",
                    actual_value=value,
                    hint="Provide a float, integer, or a string convertible to a float",
                )
        super().__set__(instance, value)


class String(Typed):
    """Descriptor for string-valued ODM attributes."""

    odm_type = str


class NonEmptyString(Typed):
    """String descriptor that rejects the empty string.

    Base of :class:`OID`, :class:`OIDRef` and :class:`Name`: the ODM ``oid``,
    ``oidref`` and ``name`` types are ``xs:string`` with ``minLength 1`` in ODM 1.3.2,
    ODM 2.0 and the Define-XML schemas built on them.

    .. versionadded:: 0.3.0
    """

    odm_type = str

    def __set__(self, instance, value):
        if value == "":
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} must not be an empty string",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Provide a non-empty value for {self.name}, or omit it if optional",
                )
        super().__set__(instance, value)


class OID(NonEmptyString):
    """Descriptor for OID (Object Identifier) attributes.

    OIDs uniquely identify definition elements within a MetaDataVersion.
    Used on the ``OID`` attribute of *Def elements (e.g., ``ItemDef.OID``).

    .. versionchanged:: 0.3.0
       The empty string is rejected (``minLength 1`` in the XSD).
    """


class OIDRef(NonEmptyString):
    """Descriptor for OID reference attributes.

    References the OID of a definition element.
    Used on reference elements (e.g., ``ItemRef.ItemOID`` references ``ItemDef.OID``).

    .. versionchanged:: 0.3.0
       The empty string is rejected (``minLength 1`` in the XSD).
    """


class Name(NonEmptyString):
    """Descriptor for the Name attribute of ODM elements.

    .. versionchanged:: 0.3.0
       The empty string is rejected (``minLength 1`` in the XSD).
    """


# XML 1.0 (Fifth Edition) NameStartChar and NameChar, without the colon: an NCName,
# the lexical space of xs:ID and xs:IDREF.
_NCNAME_START = ("A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D"
                 "\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF"
                 "\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF")
_NCNAME_PAT = re.compile(
    f"[{_NCNAME_START}][{_NCNAME_START}\\-.0-9\u00B7\u0300-\u036F\u203F-\u2040]*")


class _NCNameString(Typed):
    """String descriptor restricted to the NCName lexical space (whitespace collapsed)."""

    odm_type = str
    _xsd_type = "NCName"

    def __set__(self, instance, value):
        if isinstance(value, str) and not _NCNAME_PAT.fullmatch(_xsd_collapse(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid {self._xsd_type} value of {value!r}",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"An {self._xsd_type} starts with a letter or underscore and contains "
                         "only letters, digits, '.', '-' and '_' (no spaces or colons)",
                )
        super().__set__(instance, value)


class ID(_NCNameString):
    """Descriptor for XML ID attributes (``xs:ID``).

    .. versionchanged:: 0.3.0
       Values must be NCNames, as ``xs:ID`` requires.
    """

    _xsd_type = "xs:ID"


class IDRef(_NCNameString):
    """Descriptor for XML IDREF attributes (``xs:IDREF``).

    .. versionchanged:: 0.3.0
       Values must be NCNames, as ``xs:IDREF`` requires.
    """

    _xsd_type = "xs:IDREF"


class Language(Typed):
    """Descriptor for ``xs:language`` values, such as ``xml:lang`` (``en``, ``en-US``).

    .. versionadded:: 0.3.0
    """

    odm_type = str

    def __set__(self, instance, value):
        if isinstance(value, str) and not _XS_LANGUAGE_PAT.fullmatch(_xsd_collapse(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid language code of {value!r}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use a BCP 47 language tag, e.g. 'en' or 'en-US'",
                )
        super().__set__(instance, value)


class List(Typed):
    """Descriptor for list-valued attributes."""

    odm_type = list


class Dictionary(Typed):
    """Descriptor for dictionary-valued attributes."""

    odm_type = dict


class Positive(DESC.Descriptor):
    """Mixin descriptor that enforces value > 0.

    Raises :exc:`~odmlib.exceptions.OdmlibTypeError` if value is <= 0.
    """

    def __set__(self, instance, value):
        if (value is not None) and isinstance(value, (int, float)) and value <= 0:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected value > 0 for type Positive for {self.name}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a positive number (> 0)",
                )
        super().__set__(instance, value)


class NonNegative(DESC.Descriptor):
    """Mixin descriptor that enforces value >= 0.

    Raises :exc:`~odmlib.exceptions.OdmlibTypeError` if value is < 0.
    """

    def __set__(self, instance, value):
        if (value is not None) and isinstance(value, (int, float)) and value < 0:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"Expected value >= 0 for type Non-negative for {self.name}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a non-negative number (>= 0)",
                )
        super().__set__(instance, value)


class PositiveInteger(Integer, Positive):
    """Descriptor for positive integer attributes (value > 0).

    Combines integer type validation with positive value constraint.
    Used for Length, ItemGroupDataSeq, and similar attributes.
    """

    pass


class NonNegativeInteger(Integer, NonNegative):
    """Descriptor for non-negative integer attributes (value >= 0).

    Combines integer type validation with non-negative constraint.
    Used for SignificantDigits and similar attributes.
    """

    pass


class PositiveFloat(Float, Positive):
    """Descriptor for positive float attributes (value > 0)."""

    pass


class NonNegativeFloat(Float, NonNegative):
    """Descriptor for non-negative float attributes (value >= 0)."""

    pass


class Sized(DESC.Descriptor):
    """Mixin descriptor that enforces a maximum string length.

    Args:
        max_length (int): Maximum allowed length of the string value.
    """

    def __init__(self, *args, max_length, **kwargs):
        # pulls out named arg max_length and passes the remaining arguments along
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and (len(value) > self.max_length):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has a length of {len(value)} and exceeds the maximum length of "
                    f"{self.max_length}",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Shorten the value to {self.max_length} characters or fewer",
                )
        super().__set__(instance, value)


class SizedString(String, Sized):
    """String descriptor with a maximum length constraint."""

    pass


class Regex(DESC.Descriptor):
    """Descriptor that validates a string against a regular expression pattern.

    Args:
        pat (str): Regular expression pattern the value must match.
    """
    def __init__(self, *args, pat, **kwargs):
        # takes a pattern arg named pat and passes the remaining arguments along
        self.pat = re.compile(pat)
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and not self.pat.match(value):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid string of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Value must match pattern: {self.pat.pattern}",
                )
        super().__set__(instance, value)


class SizedRegexString(SizedString, Regex):
    """String descriptor with both size and regex constraints."""

    pass


# format patterns compiled once at import time — these run in __set__, which
# is a hot path when loading large documents
_PARTIAL_DATETIME_PAT = re.compile(r'^((([0-9][0-9][0-9][0-9])((-(([0][1-9])|([1][0-2])))((-(([0][1-9])|([1-2][0-9])|([3][0-1])))(T((([0-1][0-9])|([2][0-3]))((:([0-5][0-9]))(((:([0-5][0-9]))((\.[0-9]+)?))?)?)?((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z)))?))?)?)?))$')
_PARTIAL_DATE_PAT = re.compile(r'^(([0-9][0-9][0-9][0-9])(-(([0][1-9])|([1][0-2])))?)$')
_TIME_PAT = re.compile(r'^(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
_PARTIAL_TIME_PAT = re.compile(r'^((([0-1][0-9])|([2][0-3]))(:[0-5][0-9])?(((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z))?)$')
_INCOMPLETE_DATETIME_PAT = re.compile(r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-)T(((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$')
_INCOMPLETE_DATE_PAT = re.compile(r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-))$')
_INCOMPLETE_TIME_PAT = re.compile(r'^((((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$')
_SAS_NAME_PAT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
_SAS_FORMAT_PAT = re.compile(r"[A-Za-z_$][A-Za-z0-9_.]*$")


# ---------------------------------------------------------------------------
# XML Schema 1.0 lexical spaces
# ---------------------------------------------------------------------------
# The built-in date/time, duration, decimal and language types collapse whitespace
# before matching, so they are tested against _xsd_collapse(value). The ODM pattern
# types (emptyTag, tHour, tDatetime, tDuration, tIncomplete*) derive from xs:string,
# which preserves whitespace, so they are tested against the raw value. A union
# accepts a value that any one member accepts. Every pattern is applied with
# fullmatch(): a "$" anchor alone also matches before a trailing newline.

_XSD_WHITESPACE = " \t\n\r"
_YEAR = r"(?P<year>-?(?:[1-9][0-9]{4,}|[0-9]{4}))"
_MONTH = r"(?P<month>0[1-9]|1[0-2])"
_DAY = r"(?P<day>0[1-9]|[12][0-9]|3[01])"
_TZ = r"(?:Z|[+-](?:(?:0[0-9]|1[0-3]):[0-5][0-9]|14:00))"
_CLOCK = r"(?:(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?|24:00:00(?:\.0+)?)"
_XS_DATETIME_PAT = re.compile(rf"{_YEAR}-{_MONTH}-{_DAY}T{_CLOCK}{_TZ}?", re.ASCII)
_XS_DATE_PAT = re.compile(rf"{_YEAR}-{_MONTH}-{_DAY}{_TZ}?", re.ASCII)
_XS_TIME_PAT = re.compile(rf"{_CLOCK}{_TZ}?", re.ASCII)
_XS_GYEARMONTH_PAT = re.compile(rf"{_YEAR}-{_MONTH}{_TZ}?", re.ASCII)
_XS_GYEAR_PAT = re.compile(rf"{_YEAR}{_TZ}?", re.ASCII)
_XS_DURATION_PAT = re.compile(
    r"-?P(?=[0-9]|T[0-9])(?:[0-9]+Y)?(?:[0-9]+M)?(?:[0-9]+D)?"
    r"(?:T(?=[0-9])(?:[0-9]+H)?(?:[0-9]+M)?(?:[0-9]+(?:\.[0-9]+)?S)?)?", re.ASCII)
_XS_DECIMAL_PAT = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", re.ASCII)
_XS_LANGUAGE_PAT = re.compile(r"[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*", re.ASCII)
_EMPTY_TAG_PAT = re.compile(r"[ ]?")                       # emptyTag: "" or one space
_T_DURATION_PAT = re.compile(r"[+-]?P[0-9]+W", re.ASCII)   # tDuration (week form)
# tHour, tDatetime, tIncomplete, tIncompleteDate and tIncompleteTime are
# _PARTIAL_TIME_PAT, _PARTIAL_DATETIME_PAT, _INCOMPLETE_DATETIME_PAT,
# _INCOMPLETE_DATE_PAT and _INCOMPLETE_TIME_PAT above, copied from ODM-types.xsd.


def _xsd_collapse(value):
    """Strip the XML whitespace a collapsing XSD type ignores at either end."""
    return value.strip(_XSD_WHITESPACE)


def _calendar_ok(match):
    """Apply the value checks a date pattern cannot express.

    XML Schema 1.0 has no year 0000, and the day must exist in its month: 2021-02-29
    is rejected, 2020-02-29 accepted. The leap-year rule is applied to the year as
    written, negative years included, which is what xmlschema (the validator behind
    ODMSchemaValidator) does.
    """
    year = int(match.group("year"))
    if year == 0:
        return False
    day = match.groupdict().get("day")
    if day is None or int(day) <= 28:
        return True
    month = int(match.group("month"))
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return int(day) <= (29 if leap else 28)
    return int(day) <= (30 if month in (4, 6, 9, 11) else 31)


def _is_xs(pattern, value):
    """True when *value* is in the lexical space of a collapsing built-in type."""
    if not isinstance(value, str):
        return False
    match = pattern.fullmatch(_xsd_collapse(value))
    return match is not None and ("year" not in pattern.groupindex or _calendar_ok(match))


def _is_any(value, raw_patterns=(), xs_patterns=()):
    """True when any raw (string-derived) or built-in union member accepts *value*."""
    if not isinstance(value, str):
        return False
    return (any(p.fullmatch(value) for p in raw_patterns)
            or any(_is_xs(p, value) for p in xs_patterns))


class DateTimeString(DESC.Descriptor):
    """Descriptor for ``xs:dateTime`` strings.

    Validates format: ``YYYY-MM-DDTHH:MM:SS[.sss][Z|±HH:MM]``

    Used for ``CreationDateTime``, ``AsOfDateTime``, and similar attributes.

    .. versionchanged:: 0.3.0
       Follows the ``xs:dateTime`` lexical space exactly: days that do not exist
       (``2021-02-30``) and the year 0000 are rejected; ``24:00:00``, years beyond
       9999 and surrounding whitespace are accepted; time zone offsets are limited to
       ±14:00.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _is_xs(_XS_DATETIME_PAT, value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type datetime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use ISO 8601 datetime format: YYYY-MM-DDTHH:MM:SS[.sss][Z|±HH:MM]",
                )
        super().__set__(instance, value)


class PartialDateTimeString(DESC.Descriptor):
    """Descriptor for partial ISO 8601 datetime strings.

    Allows partial date/time values where some components may be omitted.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _PARTIAL_DATETIME_PAT.match(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type PartialDateTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use a valid partial datetime format per ISO 8601",
                )
        super().__set__(instance, value)


class PartialDateString(DESC.Descriptor):
    """Descriptor for partial ISO 8601 date strings.

    Accepts full ``YYYY-MM-DD``, year-month ``YYYY-MM``, or year-only ``YYYY``.
    """

    def __set__(self, instance, value):
        if value and value.count('-') == 2:
            try:
                datetime.datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                    raise OdmlibValidationError(
                        f"Expected type PartialDate for {self.name}, found value {value}",
                        attribute=self.name,
                        actual_value=value,
                        hint="Use YYYY-MM-DD date format",
                    )
        else:
            if (value is not None) and (not _PARTIAL_DATE_PAT.match(value)):
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                    raise OdmlibValidationError(
                        f"Expected type PartialDate for {self.name}, found value {value}",
                        attribute=self.name,
                        actual_value=value,
                        hint="Use YYYY or YYYY-MM format for partial dates",
                    )
        super().__set__(instance, value)


class PartialTimeString(DESC.Descriptor):
    """Descriptor for partial ISO 8601 time strings.

    Accepts full ``HH:MM:SS`` or partial time values.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not (_TIME_PAT.match(value) or _PARTIAL_TIME_PAT.match(value))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use a valid partial time format per ISO 8601",
                )
        super().__set__(instance, value)


class IncompleteDateTimeString(DESC.Descriptor):
    """Descriptor for incomplete ISO 8601 datetime strings (XSD ``incompleteDatetime``).

    Allows ``-`` as a placeholder for unknown date/time components.

    .. versionchanged:: 0.3.0
       Accepts the whole XSD union -- ``emptyTag | xs:dateTime | tDatetime |
       tIncomplete`` -- so partial datetimes such as ``2004-12`` and the empty tag are
       accepted. Previously only the ``tIncomplete`` member was checked.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _is_any(
                value, (_EMPTY_TAG_PAT, _PARTIAL_DATETIME_PAT, _INCOMPLETE_DATETIME_PAT),
                (_XS_DATETIME_PAT,))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteDateTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete datetime, replacing unknown parts with '-'",
                )
        super().__set__(instance, value)


class IncompleteDateString(DESC.Descriptor):
    """Descriptor for incomplete ISO 8601 date strings (XSD ``incompleteDate``).

    Allows ``-`` as a placeholder for unknown date components.

    .. versionchanged:: 0.3.0
       Accepts the whole XSD union -- ``emptyTag | xs:date | xs:gYearMonth |
       xs:gYear | tIncompleteDate`` -- where previously only ``tIncompleteDate`` was
       checked, so ``2004-12`` and ``2004`` were rejected.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _is_any(
                value, (_EMPTY_TAG_PAT, _INCOMPLETE_DATE_PAT),
                (_XS_DATE_PAT, _XS_GYEARMONTH_PAT, _XS_GYEAR_PAT))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteDate for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete date, e.g., 'YYYY--DD'",
                )
        super().__set__(instance, value)


class IncompleteTimeString(DESC.Descriptor):
    """Descriptor for incomplete ISO 8601 time strings (XSD ``incompleteTime``).

    Allows ``-`` as a placeholder for unknown time components.

    .. versionchanged:: 0.3.0
       Accepts the whole XSD union -- ``emptyTag | xs:time | tHour |
       tIncompleteTime`` -- where previously only ``tIncompleteTime`` was checked, so
       ``12`` and ``12:30`` were rejected.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _is_any(
                value, (_EMPTY_TAG_PAT, _PARTIAL_TIME_PAT, _INCOMPLETE_TIME_PAT),
                (_XS_TIME_PAT,))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete time, replacing unknown parts with '-'",
                )
        super().__set__(instance, value)


class DurationDateTimeString(DESC.Descriptor):
    '''Descriptor for ISO 8601 duration strings.

    Accepts the whole ``durationDatetime`` union the ODM 2.0 XSD defines:
    the week form (``P2W``, ``-P1W``), the general ISO 8601 form
    (``P3D``, ``P1Y2M``, ``PT1H30M``, ``P1DT2H3M4.5S``), and the empty tag.
    Used for timing window attributes in ODM 2.0.

    .. versionchanged:: 0.2.1
       Previously only ``[+-]P{n}W`` was accepted, rejecting XSD-valid values
       such as ``P3D`` and ``PT1H``.

    .. versionchanged:: 0.3.0
       Surrounding whitespace is accepted on the ``xs:duration`` form (``" P3D "``),
       which collapses whitespace; the week form and the empty tag derive from
       ``xs:string`` and still must match exactly.
    '''

    def __set__(self, instance, value):
        if (value is not None) and (not _is_any(
                value, (_EMPTY_TAG_PAT, _T_DURATION_PAT), (_XS_DURATION_PAT,))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type DurationDateTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 duration, e.g. 'P2W', 'P3D' or 'PT1H30M'",
                )
        super().__set__(instance, value)


class TimepointString(DESC.Descriptor):
    """Descriptor for a date, time or datetime that may be partial.

    The ODM 2.0 XSD types ``AbsoluteTimingConstraint/@TimepointTarget`` as an
    anonymous union of ``date time datetime partialDate partialTime partialDatetime``.
    Expanded, a value is accepted when it is any of:

    - empty, or a single space (``emptyTag``);
    - a full or partial date: ``2021-01-01``, ``2021-01``, ``2021`` (time zone allowed);
    - a full or partial time: ``14:30:00``, ``14:30``, ``14`` (time zone allowed);
    - a full or partial datetime: ``2021-01-01T14:30:00Z``, ``2021-01-01T14``.

    .. versionadded:: 0.3.0
       Replaces :class:`IncompleteDateTimeString` on ``TimepointTarget``, which checked
       only the dash-placeholder form and so rejected values such as ``2021-01-01``.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _is_any(
                value, (_EMPTY_TAG_PAT, _PARTIAL_TIME_PAT, _PARTIAL_DATETIME_PAT),
                (_XS_DATETIME_PAT, _XS_DATE_PAT, _XS_GYEARMONTH_PAT, _XS_GYEAR_PAT,
                 _XS_TIME_PAT))):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected a date, time or datetime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use e.g. '2021-01-01', '2021-01', '14:30', or '2021-01-01T14:30:00'",
                )
        super().__set__(instance, value)


class DateString(DESC.Descriptor):
    """Descriptor for ISO 8601 date strings (YYYY-MM-DD).

    Used for ``EffectiveDate`` in MetaDataVersionRef.
    """

    def __set__(self, instance, value):
        try:
            if value is not None:
                datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type date (YYYY-MM-DD) for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use YYYY-MM-DD date format",
                )
        super().__set__(instance, value)


class SASName(DESC.Descriptor):
    """Descriptor for SAS variable/dataset name attributes.

    Validates that the value starts with a letter or underscore,
    contains only alphanumerics and underscores, and is at most 8
    characters long. Used for SASFieldName, SASDatasetName, etc.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _SAS_NAME_PAT.match(value) or len(value) > 8):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid sasName of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="SAS names must start with a letter or underscore, contain only "
                         "alphanumerics/underscores, and be 8 characters or fewer",
                )
        super().__set__(instance, value)


class SASFormat(DESC.Descriptor):
    """Descriptor for SAS format name attributes.

    Validates that the value starts with a letter, underscore, or ``$``,
    contains only alphanumerics, underscores, and dots, and is at most
    8 characters long. Used for SASFormatName.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _SAS_FORMAT_PAT.match(value) or len(value) > 8):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid sasFormat of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="SAS formats must start with a letter, underscore, or '$', and be 8 characters or fewer",
                )
        super().__set__(instance, value)


class Email(DESC.Descriptor):
    """Descriptor for email address attributes.

    Validates using the ``validators.email`` function.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not valid_email(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid email format of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a valid email address, e.g., 'user@example.com'",
                )
        super().__set__(instance, value)


class Url(DESC.Descriptor):
    """Descriptor for URL attributes.

    Validates using the ``validators.url`` function.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not valid_url(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid url format of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a valid URL, e.g., 'https://example.com'",
                )
        super().__set__(instance, value)


class FileName(DESC.Descriptor):
    """Descriptor for file name attributes.

    Validates using ``pathvalidate.is_valid_filename``.
    Used for PdfFileName, PictureFileName, etc.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not is_valid_filename(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"{self.name} has an invalid fileName of {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Provide a valid filename without illegal characters",
                )
        super().__set__(instance, value)


class ValidValues(DESC.Descriptor):
    """Descriptor that validates against a dynamically-loaded set of permitted values.

    Looks up valid values from the ValueSet registry using the element
    class name and attribute name (e.g., ``ODM.FileType``).
    """

    def _resolve_attr_key(self, instance):
        """Return the "ClassName.attr" valueset key, walking the MRO.

        Subclasses (e.g. custom extensions of a model class) have no
        valueset registered under their own name, so fall back to the
        first ancestor class that does.
        """
        for klass in type(instance).__mro__:
            candidate = klass.__name__ + "." + self.name
            if VS.ValueSet.value_set(candidate, instance=instance) is not VS.UNKNOWN_ATTRIBUTE:
                return candidate
        return type(instance).__name__ + "." + self.name

    def __set__(self, instance, value):
        if (value is not None):
            attr_key = self._resolve_attr_key(instance)
            if not VS.ValueSet.validate(attr_key, value, instance=instance):
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_VALUESET):
                    description = VS.ValueSet.describe(attr_key, instance=instance)
                    raise OdmlibTypeError(
                        f"Invalid value {value} for {self.name}. {description}",
                        attribute=self.name,
                        actual_value=value,
                        hint=description,
                    )
        super().__set__(instance, value)


class ExtendedValidValues(DESC.Descriptor):
    """Descriptor that validates against an explicit list of permitted values.

    Unlike ValidValues, the allowed values are provided at class definition
    time in the ``valid_values`` list argument.
    """

    def __set__(self, instance, value):
        if (value is not None) and value not in self.valid_values:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_VALUESET):
                raise OdmlibTypeError(
                    f"Invalid value {value} for {self.name}. Value must be one of "
                    f"{', '.join(self.valid_values)}",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Valid values are: {', '.join(self.valid_values)}",
                )
        super().__set__(instance, value)


class ValueSetString(ValidValues, String):
    """String descriptor that validates against a dynamically-loaded set of permitted values.

    Combines string type validation with value set membership checking.
    Used for attributes like FileType, Repeating, Mandatory, DataType, etc.
    """

    pass


class XHTMLDiv(DESC.Descriptor):
    """An ``xhtml:div`` child element carried as a markup string.

    ODM 2.0 ``TranslatedText`` is mixed content with an optional ``xhtml:div`` child.
    Rather than model the XHTML element set, the descriptor holds the serialized
    ``div`` (plus any text following it inside the parent) as a string, which the XML
    loader fills from the source document and ``to_xml()`` writes back as a real
    subtree. The string declares its own XHTML namespace, so it serializes correctly
    regardless of :class:`~odmlib.ns_registry.NamespaceRegistry` state, and it
    survives ``to_dict()``/JSON unchanged.

    Assigned markup is normalized: elements written without a namespace are placed
    in the XHTML namespace, so ``"<div><p>Hi</p></div>"`` is accepted. Anything other
    than a single well-formed ``div``, optionally followed by text, raises
    :class:`~odmlib.exceptions.OdmlibValidationError`.

    .. versionadded:: 0.3.0
    """

    #: Marks the descriptor for ODMMeta, which lists it in ``_markup``. Markup is
    #: stored like an attribute but serialized as a child element.
    is_markup = True
    #: Clark-notation tag of the element carried, used by the XML loader.
    tag = XH.XHTML_DIV
    #: The element's reference in the XSD content model.
    xsd_ref = "xhtml:div"

    def __set__(self, instance, value):
        if value is not None:
            if not isinstance(value, str):
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                    raise OdmlibTypeError(
                        f"Expected XHTML markup as a string for {self.name}",
                        attribute=self.name,
                        expected_type="str",
                        actual_value=value,
                        hint='Assign markup text, e.g. \'<div xmlns="http://www.w3.org/1999/xhtml">'
                             '<p>Text</p></div>\'',
                    )
            else:
                try:
                    value = XH.normalize(value)
                except ValueError as ex:
                    if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                        raise OdmlibValidationError(
                            f"Invalid XHTML markup for {self.name}: {ex}",
                            attribute=self.name,
                            actual_value=value,
                            hint="Provide a single well-formed xhtml:div element",
                        ) from ex
        super().__set__(instance, value)


class ODMObject(DESC.Descriptor):
    """Descriptor for a single child ODM element.

    Stores a reference to the element class and validates type on
    assignment. When accessed on an unset optional attribute, instantiates
    the element class with no arguments.

    Args:
        element_class (type): The expected child element class.
        namespace (str): XML namespace prefix (default: "odm").
    """

    def __init__(self, *args, element_class,  **kwargs):
        self.obj_type = element_class
        kwargs["element_class"] = element_class
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if isinstance(value, list):
            # historically tolerated; every item must still be the right type
            for obj in value:
                if not isinstance(obj, self.obj_type):
                    if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                        raise OdmlibTypeError(
                            f"Every {self.name} object in the list must be of type {self.obj_type}",
                            attribute=self.name,
                            expected_type=str(self.obj_type),
                            actual_value=obj,
                            hint=f"Each element in {self.name} must be of type {self.obj_type.__name__}",
                        )
        elif not isinstance(value, self.obj_type):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"The {self.name} object must be of type {self.obj_type}",
                    attribute=self.name,
                    expected_type=str(self.obj_type),
                    actual_value=value,
                    hint=f"Assign an instance of {self.obj_type.__name__}",
                )
        super().__set__(instance, value)


class ODMListObject(ODMObject, list):
    """Descriptor for a list of child ODM elements.

    Validates that all items assigned to the list are instances of
    the expected element class. Stored as a plain list in the instance.

    Args:
        element_class (type): The class that all list items must be.
        namespace (str): XML namespace prefix (default: "odm").
        group (str): Optional name of an XSD repeating group whose members may
            interleave (e.g. ``ItemGroupDef``'s ``ItemGroupRef``/``ItemRef``). Every
            member descriptor of a class that shares a ``group`` name stores its list as
            a :class:`~odmlib.interleave.GroupMemberList` view onto one ordered
            sequence, so the document order of the group is kept on load and written
            back on serialization. See :mod:`odmlib.interleave`.

    .. versionchanged:: 0.3.0
       Added ``group``.
    """

    def __init__(self, *args, group=None, **kwargs):
        self.group = group
        super().__init__(*args, **kwargs)

    def __delete__(self, instance):
        IL.detach(instance.__dict__.get(self.name))
        super().__delete__(instance)

    def __set__(self, instance, value):
        if isinstance(value, list):
            for obj in value:
                if not isinstance(obj, self.obj_type):
                    if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                        raise OdmlibTypeError(
                            f"Every {self.name} object in the list must be of type {self.obj_type}",
                            attribute=self.name,
                            expected_type=str(self.obj_type),
                            actual_value=obj,
                            hint=f"Each element in {self.name} must be of type {self.obj_type.__name__}",
                        )
        else:
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                raise OdmlibTypeError(
                    f"The {self.name} object must be a list",
                    attribute=self.name,
                    actual_value=value,
                    hint=f"Assign a list of {self.obj_type.__name__} objects",
                )
        if self.group is not None and isinstance(value, list):
            names = getattr(type(instance), "_groups", {}).get(self.group)
            if names:
                value = IL.attach(instance, self.name, names, value)
        super().__set__(instance, value)
