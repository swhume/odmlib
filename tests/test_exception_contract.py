"""odmlib raises its own exceptions, never a bare ``ValueError`` or ``TypeError``.

0.3.0 removed the ``ValueError``/``TypeError`` bases from ``OdmlibValidationError``,
``OdmlibTypeError``, ``OdmlibLoaderStateError`` and ``OdmlibNamespaceError``. Callers
are told to catch ``OdmlibError`` (or a subclass). A builtin raised directly from
library code escapes that handler, so this module scans the package source and
fails on any ``raise ValueError`` or ``raise TypeError`` outside the allowlist.

The allowlist holds modules whose builtin errors never reach a caller because
odmlib catches and wraps them. A test below proves each case.
"""
import ast
import os
from unittest import TestCase

from odmlib.exceptions import OdmlibValidationError

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_DIR = os.path.join(REPO_ROOT, "odmlib")
BUILTINS = ("ValueError", "TypeError")

#: Module (repo-relative, POSIX) -> why its builtin raises are acceptable.
ALLOWED = {
    "odmlib/xhtml.py": "internal helper: typed.XHTMLDiv and ODMElement.to_xml catch "
                       "its ValueError and re-raise an OdmlibValidationError or "
                       "OdmlibSerializationError",
}


def builtin_raises():
    """``{(module, line, name)}`` for every ``raise ValueError/TypeError`` in odmlib/."""
    found = set()
    for current, dirnames, filenames in os.walk(PACKAGE_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = os.path.join(current, filename)
            module = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Raise) or node.exc is None:
                    continue
                target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                name = (target.id if isinstance(target, ast.Name)
                        else target.attr if isinstance(target, ast.Attribute) else None)
                if name in BUILTINS:
                    found.add((module, node.lineno, name))
    return found


class TestNoBareBuiltinRaises(TestCase):

    def test_no_builtin_value_or_type_error_raised_outside_allowlist(self):
        offenders = sorted(f"{module}:{line}: raise {name}"
                           for module, line, name in builtin_raises()
                           if module not in ALLOWED)
        self.assertEqual(
            offenders, [],
            "raise an odmlib exception instead (OdmlibValidationError, OdmlibTypeError, "
            "OdmlibParsingError, ...), or add the module to ALLOWED with the reason "
            "its builtin errors never reach a caller")

    def test_allowlist_has_no_stale_entries(self):
        raising = {module for module, _, _ in builtin_raises()}
        self.assertEqual(sorted(set(ALLOWED) - raising), [])

    def test_scan_sees_raises(self):
        """Guard the guard: the scan finds the allowlisted module's raises."""
        self.assertGreaterEqual(
            len([r for r in builtin_raises() if r[0] == "odmlib/xhtml.py"]), 3)


class TestAllowlistedErrorsAreWrapped(TestCase):
    """Each allowlisted module's builtin errors reach callers as odmlib errors."""

    def test_invalid_xhtml_is_reported_as_validation_error(self):
        import odmlib.odm_2_0.model as ODM2
        with self.assertRaises(OdmlibValidationError) as ctx:
            ODM2.TranslatedText(_content="x", lang="en", Type="application/xhtml+xml",
                                div="<p>not a div</p>")
        self.assertIsInstance(ctx.exception.__cause__ or ctx.exception.__context__,
                              ValueError)
