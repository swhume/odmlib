import os
from importlib import resources
from odmlib.exceptions import OdmlibValidationError

# Map main schema filenames by standard/version
_MAIN_SCHEMA = {
    ("odm", "1.3.2"): "ODM1-3-2.xsd",
    ("odm", "2.0"): "ODM.xsd",
    ("define", "2.0"): "define2-0-0.xsd",
    ("define", "2.1"): "define2-1-0.xsd",
    ("arm", "1.0"): "arm1-0-0.xsd",             # ARM 1.0 over Define-XML 2.0
    ("arm", "1.0-define2.1"): "arm1-0-0.xsd",   # ARM 1.0 over Define-XML 2.1
}


def get_schema_dir(standard: str, version: str) -> str:
    """Return absolute path to the directory that contains the schema files.

    This uses importlib.resources to resolve packaged data paths so that relative
    imports inside the XSD can be resolved by the schema processor.
    """
    try:
        # resources.files available in Python 3.9+
        files = resources.files("odmlib.schemas")  # type: ignore[attr-defined]
        return str(files / standard / version)
    except Exception:
        # Fallback: build path relative to this file
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, "schemas", standard, version)


def get_schema_path(standard: str, version: str, filename: str | None = None) -> str:
    """Return absolute path to the requested schema file.

    If filename is None, use the main/root schema file for the standard/version.
    """
    if filename is None:
        try:
            filename = _MAIN_SCHEMA[(standard, version)]
        except KeyError as ex:
            raise OdmlibValidationError(
                f"Unknown standard/version: {(standard, version)}",
                hint=f"Valid combinations are: {list(_MAIN_SCHEMA.keys())}",
            ) from ex

    package = f"odmlib.schemas.{standard}.{version}"
    try:
        with resources.as_file(resources.files(package) / filename) as p:  # type: ignore[attr-defined]
            return str(p)
    except Exception:
        # Fallback to a direct filesystem join
        return os.path.join(get_schema_dir(standard, version), filename)
