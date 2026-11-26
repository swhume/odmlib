import os
from odmlib.exceptions import OdmlibValidationError

# The bundled XSDs live beside this module, as ordinary files, in every way odmlib is
# installed: a wheel, a source checkout, and PyInstaller's onedir and onefile builds
# (onefile unpacks data files to a temporary directory and points __file__ there).
# xmlschema needs those real paths so a root schema's xs:include/xs:import resolve.
_SCHEMA_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")

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
    """Return the absolute path of the directory holding a standard's schema files.

    The path is a real directory, so the schema processor can resolve the relative
    ``xs:include``/``xs:import`` locations inside the XSDs.

    .. versionchanged:: 0.3.0
       Resolved from this module's location only. An ``importlib.resources`` lookup
       was tried first but added nothing for an on-disk package.
    """
    return os.path.join(_SCHEMA_ROOT, standard, version)


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

    # 0.3.0: no importlib.resources lookup. It asked for the package
    # "odmlib.schemas.odm.1.3.2", which can never be imported (a version directory is
    # not a valid package name), so it always fell through to this join -- and had it
    # worked, it would have returned a path from an as_file() context already closed.
    return os.path.join(get_schema_dir(standard, version), filename)
