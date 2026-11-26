"""PyInstaller support for odmlib.

An application frozen with PyInstaller needs two things from odmlib that static
analysis cannot find:

* the data files -- ``odmlib/data/valuesets.json`` and the bundled XSDs under
  ``odmlib/schemas/``;
* the model modules, which the loaders import by name at run time
  (``importlib.import_module(f"odmlib.{model_package}.model")``).

``hook-odmlib.py`` in this package supplies both. PyInstaller finds it through the
``pyinstaller40`` entry point declared in ``pyproject.toml``, so no ``--collect-data``
or ``--hidden-import`` flags are needed. Nothing here imports PyInstaller, and odmlib
does not depend on it.

.. versionadded:: 0.3.0
"""
import os


def get_hook_dirs():
    """Return the directories holding odmlib's PyInstaller hooks (entry point target)."""
    return [os.path.dirname(os.path.abspath(__file__))]
