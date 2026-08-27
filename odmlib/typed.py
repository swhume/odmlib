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
      :class:`IncompleteTimeString`, :class:`DurationDateTimeString` -- temporal types
    - :class:`SASName`, :class:`SASFormat` -- SAS naming constraints
    - :class:`Email`, :class:`Url`, :class:`FileName` -- format validators
    - :class:`ValidValues`, :class:`ExtendedValidValues` -- enumerated value validators
    - :class:`ValueSetString` -- combined enumerated + string validator
    - :class:`ODMObject` -- single child ODM element container
    - :class:`ODMListObject` -- list of child ODM elements container
"""
import odmlib.descriptor as DESC
import re
import odmlib.valueset as VS
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
    """Descriptor for float-valued ODM attributes.

    Accepts float, int, and string values that convert to float.
    Used for Rank attributes in CodeListItem and EnumeratedItem.
    """

    def __set__(self, instance, value):
        # in XML floats are presented as strings
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                    raise OdmlibTypeError(
                        f"Expected string to convert to float for {self.name} with a value {str(value)}",
                        attribute=self.name,
                        actual_value=value,
                        hint="Provide a string that represents a valid float, e.g., '3.14'",
                    )
                # permissive: fall through — store the string as-is
        # convert integer into a float (e.g. 1 to 1.0)
        elif isinstance(value, int):
            value = float(value)
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


class OID(Typed):
    """Descriptor for OID (Object Identifier) attributes.

    OIDs uniquely identify definition elements within a MetaDataVersion.
    Used on the ``OID`` attribute of *Def elements (e.g., ``ItemDef.OID``).
    """

    odm_type = str


class OIDRef(Typed):
    """Descriptor for OID reference attributes.

    References the OID of a definition element.
    Used on reference elements (e.g., ``ItemRef.ItemOID`` references ``ItemDef.OID``).
    """

    odm_type = str


class Name(Typed):
    """Descriptor for the Name attribute of ODM elements."""

    odm_type = str


class ID(Typed):
    """Descriptor for XML ID attributes."""

    odm_type = str


class IDRef(Typed):
    """Descriptor for XML IDREF attributes."""

    odm_type = str


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
_DATETIME_PAT = re.compile(r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
_PARTIAL_DATETIME_PAT = re.compile(r'^((([0-9][0-9][0-9][0-9])((-(([0][1-9])|([1][0-2])))((-(([0][1-9])|([1-2][0-9])|([3][0-1])))(T((([0-1][0-9])|([2][0-3]))((:([0-5][0-9]))(((:([0-5][0-9]))((\.[0-9]+)?))?)?)?((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z)))?))?)?)?))$')
_PARTIAL_DATE_PAT = re.compile(r'^(([0-9][0-9][0-9][0-9])(-(([0][1-9])|([1][0-2])))?)$')
_TIME_PAT = re.compile(r'^(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$')
_PARTIAL_TIME_PAT = re.compile(r'^((([0-1][0-9])|([2][0-3]))(:[0-5][0-9])?(((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z))?)$')
_INCOMPLETE_DATETIME_PAT = re.compile(r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-)T(((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$')
_INCOMPLETE_DATE_PAT = re.compile(r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-))$')
_INCOMPLETE_TIME_PAT = re.compile(r'^((((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$')
_SAS_NAME_PAT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")
_SAS_FORMAT_PAT = re.compile(r"[A-Za-z_$][A-Za-z0-9_.]*$")


class DateTimeString(DESC.Descriptor):
    """Descriptor for ISO 8601 datetime strings.

    Validates format: ``YYYY-MM-DDTHH:MM:SS[.sss][Z|±HH:MM]``

    Used for ``CreationDateTime``, ``AsOfDateTime``, and similar attributes.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _DATETIME_PAT.match(value)):
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
    """Descriptor for incomplete ISO 8601 datetime strings.

    Allows ``-`` as a placeholder for unknown date/time components.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _INCOMPLETE_DATETIME_PAT.match(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteDateTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete datetime, replacing unknown parts with '-'",
                )
        super().__set__(instance, value)


class IncompleteDateString(DESC.Descriptor):
    """Descriptor for incomplete ISO 8601 date strings.

    Allows ``-`` as a placeholder for unknown date components.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _INCOMPLETE_DATE_PAT.match(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteDate for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete date, e.g., 'YYYY--DD'",
                )
        super().__set__(instance, value)


class IncompleteTimeString(DESC.Descriptor):
    """Descriptor for incomplete ISO 8601 time strings.

    Allows ``-`` as a placeholder for unknown time components.
    """

    def __set__(self, instance, value):
        if (value is not None) and (not _INCOMPLETE_TIME_PAT.match(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type IncompleteTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 incomplete time, replacing unknown parts with '-'",
                )
        super().__set__(instance, value)


# The ODM 2.0 XSD types these attributes as ``durationDatetime``, a union of
# ``emptyTag`` (empty or a single space), ``xs:duration`` (the full ISO 8601
# form) and ``tDuration`` (the week-based form, which xs:duration disallows).
_DURATION_PAT = re.compile(
    r'^(?:'
    r'[ ]?'                                                   # emptyTag
    r'|[+-]?P\d+W'                                            # tDuration
    r'|-?P(?=\d|T\d)(?:\d+Y)?(?:\d+M)?(?:\d+D)?'              # xs:duration
    r'(?:T(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?'
    r')$'
)


class DurationDateTimeString(DESC.Descriptor):
    '''Descriptor for ISO 8601 duration strings.

    Accepts the whole ``durationDatetime`` union the ODM 2.0 XSD defines:
    the week form (``P2W``, ``-P1W``), the general ISO 8601 form
    (``P3D``, ``P1Y2M``, ``PT1H30M``, ``P1DT2H3M4.5S``), and the empty tag.
    Used for timing window attributes in ODM 2.0.

    .. versionchanged:: 0.2.1
       Previously only ``[+-]P{n}W`` was accepted, rejecting XSD-valid values
       such as ``P3D`` and ``PT1H``.
    '''

    def __set__(self, instance, value):
        if (value is not None) and (not _DURATION_PAT.match(value)):
            if not _mode.is_permissive(_mode.ValidationMode.SKIP_FORMAT):
                raise OdmlibValidationError(
                    f"Expected type DurationDateTime for {self.name}, found value {value}",
                    attribute=self.name,
                    actual_value=value,
                    hint="Use an ISO 8601 duration, e.g. 'P2W', 'P3D' or 'PT1H30M'",
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
    """

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
        super().__set__(instance, value)
