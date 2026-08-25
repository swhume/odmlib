from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("odmlib")
except PackageNotFoundError:
    __version__ = "0.2.1"

from odmlib.exceptions import (
    OdmlibError,
    OdmlibValidationError,
    OdmlibRequiredAttributeError,
    OdmlibOIDError,
    OdmlibConformanceError,
    OdmlibElementOrderError,
    OdmlibErrorLimitError,
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
    ErrorReporting,
    is_collecting_checker,
    flatten_cerberus_errors,
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


__all__ = [
    "__version__",
    # builder and context-manager facades
    "ODMBuilder",
    "open_odm",
    "open_define",
    # validation modes
    "ValidationMode",
    "permissive",
    "get_mode",
    "set_mode",
    # OID integrity checking
    "DynamicOIDRef",
    "create_oid_checker",
    # exception hierarchy
    "OdmlibError",
    "OdmlibValidationError",
    "OdmlibRequiredAttributeError",
    "OdmlibOIDError",
    "OdmlibConformanceError",
    "OdmlibElementOrderError",
    "OdmlibErrorLimitError",
    "OdmlibSchemaValidationError",
    "OdmlibTypeError",
    "OdmlibParsingError",
    "OdmlibLoaderStateError",
    "OdmlibSerializationError",
    "OdmlibNamespaceError",
    "OdmlibWarning",
    "OdmlibDeprecationWarning",
    "OdmlibInteroperabilityWarning",
    "ErrorCollector",
    "ErrorReporting",
    "is_collecting_checker",
    "flatten_cerberus_errors",
    # lazily imported on first access (see _LAZY / __getattr__)
    *_LAZY,
]


def __getattr__(name):
    if name in _LAZY:
        import importlib
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module 'odmlib' has no attribute {name!r}")


def __dir__():
    """Include the lazily-exported names in ``dir(odmlib)`` and tab-completion.

    Module-level ``__getattr__`` (PEP 562) makes the ``_LAZY`` names reachable
    but leaves them out of the module ``__dict__`` until first access, so
    without this they would be invisible to introspection.
    """
    return sorted(__all__)