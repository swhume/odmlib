import odmlib.descriptor as DESC
import re
import odmlib.valueset as VS
import datetime
from validators import email as valid_email, url as valid_url
from pathvalidate import is_valid_filename


class Typed(DESC.Descriptor):
    odm_type = object

    def __set__(self, instance, value):
        if (value is not None) and not isinstance(value, self.odm_type):
            raise TypeError(f"Expected type {str(self.odm_type)} for {self.name} with value {str(value)}")
        # often does not call parent, calls next on __mro__ which maybe influenced by multiple inheritance
        super().__set__(instance, value)


class Integer(DESC.Descriptor):
    def __set__(self, instance, value):
        # in XML integers are presented as strings e.g. OrderNumber="1"
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise TypeError(f"Expected string to convert to integer for {self.name} with a value {str(value)}")
        odm_type = int
        if (value is not None) and not isinstance(value, odm_type):
            raise TypeError(f"Expected type {str(odm_type)} for {self.name} with value {str(value)}")
        super().__set__(instance, value)


class Float(DESC.Descriptor):
    def __set__(self, instance, value):
        # in XML floats are presented as strings
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                raise TypeError(f"Expected string to convert to float for {self.name} with a value {str(value)}")
        # convert integer into a float (e.g. 1 to 1.0)
        elif isinstance(value, int):
            value = float(value)
        if (value is not None) and not isinstance(value, float):
            raise TypeError(f"Expected type float for {self.name} with value {str(value)}")
        super().__set__(instance, value)


class String(Typed):
    odm_type = str


class OID(Typed):
    odm_type = str


class OIDRef(Typed):
    odm_type = str


class Name(Typed):
    odm_type = str


class ID(Typed):
    odm_type = str


class IDRef(Typed):
    odm_type = str


class List(Typed):
    odm_type = list


class Dictionary(Typed):
    odm_type = dict


class Positive(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value <= 0:
            raise TypeError(f"Expected value > 0 for type Positive for {self.name}")
        super().__set__(instance, value)


class NonNegative(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value < 0:
            raise TypeError(f"Expected value >= 0 for type Non-negative for {self.name}")
        super().__set__(instance, value)


class PositiveInteger(Integer, Positive):
    pass


class NonNegativeInteger(Integer, NonNegative):
    pass


class PositiveFloat(Float, Positive):
    pass


class NonNegativeFloat(Float, NonNegative):
    pass


class Sized(DESC.Descriptor):
    def __init__(self, *args, max_length, **kwargs):
        # pulls out named arg max_length and passes the remaining arguments along
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and (len(value) > self.max_length):
            raise ValueError(f"{self.name} has a length of {len(value)} and exceeds the maximum length of "
                             f"{self.max_length}")
        super().__set__(instance, value)


class SizedString(String, Sized):
    pass


class Regex(DESC.Descriptor):
    """ pattern matching """
    def __init__(self, *args, pat, **kwargs):
        # takes a pattern arg named pat and passes the remaining arguments along
        self.pat = re.compile(pat)
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if (value is not None) and not self.pat.match(value):
            raise ValueError(f"{self.name} has an invalid string of {value}")
        super().__set__(instance, value)


class SizedRegexString(SizedString, Regex):
    pass


class DateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        iso_pat = r'^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
        pat = re.compile(iso_pat)
        if (value is not None) and (not pat.match(value)):
            raise ValueError(f"Expected type datetime for {self.name}, found value {value}")
        super().__set__(instance, value)


class PartialDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        part_pat = r'^((([0-9][0-9][0-9][0-9])((-(([0][1-9])|([1][0-2])))((-(([0][1-9])|([1-2][0-9])|([3][0-1])))(T((([0-1][0-9])|([2][0-3]))((:([0-5][0-9]))(((:([0-5][0-9]))((\.[0-9]+)?))?)?)?((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z)))?))?)?)?))$'
        compiled_part_pat = re.compile(part_pat)
        if (value is not None) and (not compiled_part_pat.match(value)):
            raise ValueError(f"Expected type PartialDateTime for {self.name}, found value {value}")
        super().__set__(instance, value)


class PartialDateString(DESC.Descriptor):
    def __set__(self, instance, value):
        if value and value.count('-') == 2:
            try:
                datetime.datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Expected type PartialDate for {self.name}, found value {value}")
        else:
            part_pat = r'^(([0-9][0-9][0-9][0-9])(-(([0][1-9])|([1][0-2])))?)$'
            compiled_part_pat = re.compile(part_pat)
            if (value is not None) and (not compiled_part_pat.match(value)):
                raise ValueError(f"Expected type PartialDate for {self.name}, found value {value}")
        super().__set__(instance, value)


class PartialTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        time_pat = r'^(2[0-3]|[01][0-9]):([0-5][0-9]):([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$'
        compiled_time_pat = re.compile(time_pat)
        part_pat = r'^((([0-1][0-9])|([2][0-3]))(:[0-5][0-9])?(((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|(Z))?)$'
        compiled_part_pat = re.compile(part_pat)
        if (value is not None) and (not (compiled_time_pat.match(value) or compiled_part_pat.match(value))):
            raise ValueError(f"Expected type IncompleteTime for {self.name}, found value {value}")
        super().__set__(instance, value)


class IncompleteDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-)T(((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise ValueError(f"Expected type IncompleteDateTime for {self.name}, found value {value}")
        super().__set__(instance, value)


class IncompleteDateString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^(((([0-9][0-9][0-9][0-9]))|-)-(((([0][1-9])|([1][0-2])))|-)-(((([0][1-9])|([1-2][0-9])|([3][0-1])))|-))$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise ValueError(f"Expected type IncompleteDate for {self.name}, found value {value}")
        super().__set__(instance, value)


class IncompleteTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        inc_pat = r'^((((([0-1][0-9])|([2][0-3])))|-):((([0-5][0-9]))|-):((([0-5][0-9](\.[0-9]+)?))|-)((((\+|-)(([0-1][0-9])|([2][0-3])):[0-5][0-9])|Z|-))?)$'
        compiled_inc_pat = re.compile(inc_pat)
        if (value is not None) and (not compiled_inc_pat.match(value)):
            raise ValueError(f"Expected type IncompleteTime for {self.name}, found value {value}")
        super().__set__(instance, value)


class DurationDateTimeString(DESC.Descriptor):
    def __set__(self, instance, value):
        dur_pat = r'^((\+ | -)?P([0-9]([0-9]+)?)W)$'
        pat = re.compile(dur_pat)
        if (value is not None) and (not pat.match(value)):
            raise ValueError(f"Expected type DurationDateTime for {self.name}, found value {value}")
        super().__set__(instance, value)


class DateString(DESC.Descriptor):
    def __set__(self, instance, value):
        try:
            if value is not None:
                datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Expected type date (YYYY-MM-DD) for {self.name}, found value {value}")
        super().__set__(instance, value)


class SASName(DESC.Descriptor):
    def __set__(self, instance, value):
        pat = re.compile("[A-Za-z_][A-Za-z0-9_]*$")
        if (value is not None) and (not pat.match(value) or len(value) > 8):
            raise ValueError(f"{self.name} has an invalid sasName of {value}")
        super().__set__(instance, value)


class SASFormat(DESC.Descriptor):
    def __set__(self, instance, value):
        # is_valid = True
        pat = re.compile("[A-Za-z_$][A-Za-z0-9_.]*$")
        if (value is not None) and (not pat.match(value) or len(value) > 8):
            raise ValueError(f"{self.name} has an invalid sasFormat of {value}")
        super().__set__(instance, value)


class Email(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not valid_email(value)):
            raise ValueError(f"{self.name} has an invalid email format of {value}")
        super().__set__(instance, value)


class Url(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not valid_url(value)):
            raise ValueError(f"{self.name} has an invalid url format of {value}")
        super().__set__(instance, value)


class FileName(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and (not is_valid_filename(value)):
            raise ValueError(f"{self.name} has an invalid fileName of {value}")
        super().__set__(instance, value)


class ValidValues(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value not in VS.ValueSet.value_set(type(instance).__name__ + "." + self.name):
            raise TypeError(f"Invalid value {value} for {self.name}. Value must be one of "
                            f"{', '.join(VS.ValueSet.value_set(self.name))}")
        super().__set__(instance, value)


class ExtendedValidValues(DESC.Descriptor):
    def __set__(self, instance, value):
        if (value is not None) and value not in self.valid_values:
            raise TypeError(f"Invalid value {value} for {self.name}. Value must be one of "
                            f"{', '.join(self.valid_values)}")
        super().__set__(instance, value)


class ValueSetString(ValidValues, String):
    pass


class ODMObject(DESC.Descriptor):
    def __init__(self, *args, element_class,  **kwargs):
        self.obj_type = element_class
        kwargs["element_class"] = element_class
        self.namespace = kwargs.get("namespace", "")
        super().__init__(*args, **kwargs)

    def __set__(self, instance, value):
        if not isinstance(value, self.obj_type) and not isinstance(value, list):
            raise TypeError(f"The {self.name} object must be of type {self.obj_type}")
        super().__set__(instance, value)


class ODMListObject(ODMObject, list):
    def __set__(self, instance, value):
        if isinstance(value, list):
            for obj in value:
                if not isinstance(obj, self.obj_type):
                    raise TypeError(f"Every {self.name} object in the list must be of type {self.obj_type}")
        else:
            raise TypeError(f"The {self.name} object must be a list")
        super().__set__(instance, value)
