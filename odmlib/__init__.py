from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("odmlib")
except PackageNotFoundError:
    __version__ = "0.2.0"

from odmlib.exceptions import (
    OdmlibError,
    OdmlibValidationError,
    OdmlibRequiredAttributeError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibElementOrderError,
    OdmlibSchemaValidationError,
    OdmlibTypeError,
    OdmlibParsingError,
    OdmlibLoaderStateError,
    OdmlibSerializationError,
    OdmlibNamespaceError,
    OdmlibWarning,
    OdmlibDeprecationWarning,
    OdmlibInteroperabilityWarning,
    ErrorCollector,
)
from odmlib.mode import ValidationMode, permissive, get_mode, set_mode
from odmlib.context import open_odm, open_define
from odmlib.builder import ODMBuilder
from odmlib.oid_generator import DynamicOIDRef, create_oid_checker
_LAZY = {
    "DatasetJSON": "odmlib.dataset_json_1_1.model",
    "Column": "odmlib.dataset_json_1_1.model",
    "SourceSystem": "odmlib.dataset_json_1_1.model",
    "DefineFlattener": "odmlib.dataset_json_1_1.define_flattener",
    "DefineBuilder": "odmlib.dataset_json_1_1.define_builder",
    "dataset_xml_to_dataset_json": "odmlib.dataset_json_1_1.converter",
    "dataset_json_to_dataset_xml": "odmlib.dataset_json_1_1.converter",
}


def __getattr__(name):
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'odmlib' has no attribute {name!r}")