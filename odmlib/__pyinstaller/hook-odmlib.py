"""PyInstaller hook for odmlib (GitHub issue #37).

Collects the data odmlib reads at run time and the modules it imports by name.
Collecting only the data is not enough: the loaders import model modules with
``importlib.import_module(f"odmlib.{model_package}.model")``, which PyInstaller's
analysis cannot see, so a build made with ``--collect-data odmlib`` alone still fails
on the first load.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files("odmlib", includes=["data/**/*.json", "schemas/**/*.xsd"])

# odmlib.schemas holds data, not code, and its version directories ("1.3.2") are not
# importable names; the hook package itself is never imported by odmlib.
hiddenimports = collect_submodules(
    "odmlib",
    filter=lambda name: not name.startswith(("odmlib.__pyinstaller", "odmlib.schemas")),
)
