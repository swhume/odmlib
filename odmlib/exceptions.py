"""
odmlib exception hierarchy.

All odmlib-specific exceptions inherit from OdmlibError, which itself
inherits from Exception. During the v0.2.x transition period, validation
and type exceptions also inherit from ValueError/TypeError respectively
so that existing except clauses continue to work.

Deprecation schedule:
    v0.2.x: New exceptions dual-inherit from ValueError/TypeError.
            All existing ``except ValueError`` and ``except TypeError``
            clauses continue to work unchanged.
    v0.3.0: Remove the ValueError/TypeError base classes.
            Update ``except ValueError`` → ``except OdmlibValidationError``
            and ``except TypeError`` → ``except OdmlibTypeError``.
"""
import contextlib
import warnings


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class OdmlibError(Exception):
    """Base exception for all odmlib errors."""


class _ErrorLimitReached(Exception):
    """Internal sentinel: a collector hit its ``max_errors`` cap.

    Deliberately **not** an :class:`OdmlibError`, so ``except OdmlibError``
    clauses inside the validation layers (and in user code) cannot swallow it
    and it can never end up in the list returned by
    :meth:`~odmlib.odm_element.ODMElement.validate`.
    """


# ---------------------------------------------------------------------------
# Validation errors (currently raised as ValueError)
# ---------------------------------------------------------------------------

class OdmlibValidationError(OdmlibError, ValueError):
    """Raised when an element fails conformance, OID, or schema validation.

    Attributes:
        element_path: Dot-separated path from root to the failing element,
            e.g. "ODM > Study > MetaDataVersion > ItemGroupDef(OID='IG.VS')"
        hint: Optional human-readable suggestion for fixing the problem.
        attribute: The attribute name that caused the error (if applicable).
        element_type: The class name of the element that failed validation.
    """

    def __init__(self, message, *, element_path=None, hint=None,
                 attribute=None, element_type=None, actual_value=None):
        self.element_path = element_path
        self.hint = hint
        self.attribute = attribute
        self.element_type = element_type
        self.actual_value = actual_value
        self._raw_message = message
        super().__init__(self._format())

    def _format(self):
        parts = [self._raw_message]
        if self.element_path:
            parts.append(f"  Context: {self.element_path}")
        if self.hint:
            parts.append(f"  Hint: {self.hint}")
        return "\n".join(parts)


class OdmlibRequiredAttributeError(OdmlibValidationError):
    """Raised when a required attribute is missing during construction."""


class OdmlibOIDError(OdmlibValidationError):
    """Raised for OID uniqueness or ref/def integrity failures."""


def flatten_cerberus_errors(errors, prefix=""):
    """Flatten a nested Cerberus error dict into ``(dotted_path, message)`` pairs.

    Cerberus reports ``{field: [msg | {subkey: [...]}, ...]}`` where *subkey*
    is a nested field name or, for sequences, the integer index of the
    offending list item::

        {'ItemGroupDef': [{0: [{'Name': ['required field']}]}]}
        -> [('ItemGroupDef.0.Name', 'required field')]

    Args:
        errors: A Cerberus error dict (typically
            ``OdmlibConformanceError.cerberus_errors``). Anything that is not
            a dict yields an empty list.
        prefix: Dotted path accumulated so far; used by the recursion.

    Returns:
        list: ``(path, message)`` tuples in Cerberus' own document order,
        which is deterministic — no sets are involved.
    """
    flattened = []
    if not isinstance(errors, dict):
        return flattened
    for field, issues in errors.items():
        path = f"{prefix}.{field}" if prefix else str(field)
        if not isinstance(issues, (list, tuple)):
            issues = [issues]
        for issue in issues:
            if isinstance(issue, dict):
                flattened.extend(flatten_cerberus_errors(issue, path))
            else:
                flattened.append((path, str(issue)))
    return flattened


class OdmlibConformanceError(OdmlibValidationError):
    """Raised when Cerberus conformance validation fails.

    A single instance normally bundles *every* violation Cerberus found, so
    :meth:`~odmlib.odm_element.ODMElement.validate` calls :meth:`expand` in
    collect mode to turn it into one error per failing field.

    Attributes:
        cerberus_errors: The raw Cerberus error dict for programmatic access.
            On errors produced by :meth:`expand` this remains the **complete**
            dict for the document, shared by reference with its siblings.
        field_path: Dotted path to the single failing field
            (e.g. ``"ItemGroupDef.0.Name"``). Set only on errors produced by
            :meth:`expand`; ``None`` on the bundled error.
    """

    def __init__(self, message, *, cerberus_errors=None, field_path=None, **kwargs):
        self.cerberus_errors = cerberus_errors or {}
        self.field_path = field_path
        super().__init__(message, **kwargs)

    def expand(self):
        """Split this bundled error into one error per failing leaf field.

        Returns:
            list: One :class:`OdmlibConformanceError` per Cerberus leaf
            message, each carrying ``field_path``, ``attribute`` (the leaf
            name) and ``element_path`` (the containing path). Returns
            ``[self]`` when there is no Cerberus payload to split — e.g. the
            "No conformance schema registered" error — so nothing is lost.
        """
        leaves = flatten_cerberus_errors(self.cerberus_errors)
        if not leaves:
            return [self]
        expanded = []
        for path, message in leaves:
            container, _, leaf = path.rpartition(".")
            expanded.append(OdmlibConformanceError(
                f"{path}: {message}",
                cerberus_errors=self.cerberus_errors,
                field_path=path,
                attribute=leaf,
                element_path=container or None,
                element_type=self.element_type,
                hint=self.hint,
            ))
        return expanded


class OdmlibElementOrderError(OdmlibValidationError):
    """Raised when child elements are not in the order required by the ODM spec."""


class OdmlibErrorLimitError(OdmlibValidationError):
    """Appended as the final entry when ``validate(max_errors=N)`` stops early.

    Its presence means validation was truncated and additional problems may
    exist. It is never raised — only collected.
    """


class OdmlibSchemaValidationError(OdmlibValidationError):
    """Raised when XSD/XML-Schema validation of an ODM document fails.

    Wraps the underlying ``xmlschema`` exception raised during XSD
    validation (e.g. by :meth:`ODMSchemaValidator.validate_file`). The
    wrapped exception is available at ``args[0]`` (for backward
    compatibility with callers that introspect ``ex.args[0].msg``) and
    via the ``wrapped`` attribute.
    """

    def __init__(self, wrapped_exception, *, hint=None):
        # Bypass OdmlibValidationError.__init__: it would replace args[0]
        # with a formatted string and would crash on a non-string message.
        # Preserve args[0] == wrapped exception for backward compatibility.
        self.wrapped = wrapped_exception
        self.element_path = None
        self.hint = hint
        self.attribute = None
        self.element_type = None
        self.actual_value = None
        self._raw_message = str(wrapped_exception)
        Exception.__init__(self, wrapped_exception)


# ---------------------------------------------------------------------------
# Type errors (currently raised as TypeError)
# ---------------------------------------------------------------------------

class OdmlibTypeError(OdmlibError, TypeError):
    """Raised when a value has the wrong type for an attribute.

    Attributes:
        attribute: The attribute name.
        expected_type: The expected type description.
        actual_value: The value that was provided.
        element_path: Path from root to the failing element (if known).
        hint: Optional human-readable suggestion for fixing the problem.
    """

    def __init__(self, message, *, attribute=None, expected_type=None,
                 actual_value=None, element_path=None, hint=None,
                 element_type=None):
        self.attribute = attribute
        self.expected_type = expected_type
        self.actual_value = actual_value
        self.element_path = element_path
        self.hint = hint
        self.element_type = element_type
        self._raw_message = message
        super().__init__(self._format())

    def _format(self):
        parts = [self._raw_message]
        if self.element_path:
            parts.append(f"  Context: {self.element_path}")
        if self.hint:
            parts.append(f"  Hint: {self.hint}")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Parsing errors
# ---------------------------------------------------------------------------

class OdmlibParsingError(OdmlibError):
    """Raised when an XML or JSON document cannot be parsed into the model."""

    def __init__(self, message, *, hint=None):
        self.hint = hint
        self._raw_message = message
        parts = [message]
        if hint:
            parts.append(f"  Hint: {hint}")
        super().__init__("\n".join(parts))


class OdmlibLoaderStateError(OdmlibParsingError, ValueError):
    """Raised when a loader method is called before the document is opened.

    Also inherits from ValueError for backward compatibility with code that
    catches ValueError from loader calls.
    """


# ---------------------------------------------------------------------------
# Serialization errors
# ---------------------------------------------------------------------------

class OdmlibSerializationError(OdmlibError):
    """Raised when an in-memory model cannot be written to XML or JSON."""


# ---------------------------------------------------------------------------
# Namespace errors
# ---------------------------------------------------------------------------

class OdmlibNamespaceError(OdmlibError, ValueError):
    """Raised for namespace registration or lookup failures."""

    def __init__(self, message, *, hint=None):
        self.hint = hint
        self._raw_message = message
        parts = [message]
        if hint:
            parts.append(f"  Hint: {hint}")
        super().__init__("\n".join(parts))


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------

class OdmlibWarning(UserWarning):
    """Base warning for all odmlib non-fatal issues."""


class OdmlibDeprecationWarning(OdmlibWarning, DeprecationWarning):
    """Issued when a deprecated odmlib feature is used."""


class OdmlibInteroperabilityWarning(OdmlibWarning):
    """Issued for constructs that are valid but may cause interoperability issues."""


# ---------------------------------------------------------------------------
# Error collector for collect-all-errors mode
# ---------------------------------------------------------------------------

class ErrorCollector:
    """Accumulates validation errors instead of raising immediately.

    Also serves as the *sink* for the collecting-checker protocol: a checker
    that mixes in :class:`ErrorReporting` hands its errors here instead of
    raising, so one pass surfaces every problem it can find.

    Example::

        errors = odm.validate(collect_errors=True, oid_checker=checker)
        for err in errors:
            print(err)

    Args:
        max_errors: Optional cap. Once this many errors are collected, the
            next :meth:`add_error` sets :attr:`truncated` and raises the
            internal ``_ErrorLimitReached`` sentinel to unwind the in-progress
            validation walk. ``None`` (the default) collects everything and
            never raises, so hand-built ``ErrorCollector()`` instances behave
            exactly as before.

    Attributes:
        errors: List of :class:`OdmlibError` instances collected so far.
        warnings: List of :class:`OdmlibWarning` instances collected so far.
        max_errors: The cap, or ``None`` for uncapped.
        truncated: True once the cap stopped collection short.
    """

    def __init__(self, max_errors=None):
        self.errors = []
        self.warnings = []
        self.max_errors = max_errors
        self.truncated = False

    @property
    def has_errors(self):
        """True if any errors have been collected."""
        return len(self.errors) > 0

    @property
    def is_full(self):
        """True when ``max_errors`` is set and that many errors are collected."""
        return self.max_errors is not None and len(self.errors) >= self.max_errors

    def add_error(self, error):
        """Add an :class:`OdmlibError` to the collection.

        Raises:
            _ErrorLimitReached: If the collector is already at ``max_errors``.
                Never raised when ``max_errors`` is ``None``.
        """
        # Check before appending so `truncated` only flips when a *further*
        # error was genuinely available — a run that finds exactly max_errors
        # problems gets no misleading "more may exist" marker.
        if self.is_full:
            self.truncated = True
            raise _ErrorLimitReached()
        self.errors.append(error)

    def add_warning(self, warning):
        """Add an :class:`OdmlibWarning` to the collection."""
        self.warnings.append(warning)

    def raise_if_errors(self):
        """Raise if any errors were collected.

        Raises the single collected error directly if only one exists, or a
        new :class:`OdmlibValidationError` summarising all errors otherwise.
        """
        if not self.has_errors:
            return
        if len(self.errors) == 1:
            raise self.errors[0]
        msg = f"{len(self.errors)} validation errors found:\n"
        msg += "\n".join(f"  {i + 1}. {err}" for i, err in enumerate(self.errors))
        raise OdmlibValidationError(msg)


# ---------------------------------------------------------------------------
# Collecting-checker protocol
# ---------------------------------------------------------------------------

class ErrorReporting:
    """Mixin giving a validation checker an optional error sink.

    A checker that mixes this in replaces ``raise SomeOdmlibError(...)`` with
    ``self.report(SomeOdmlibError(...))``. With no sink installed (the
    default) :meth:`report` re-raises, so fail-fast behaviour is identical to
    raising directly. Inside a :meth:`collecting` block the error is handed to
    the sink and the checker keeps going, so a single pass surfaces every
    problem rather than only the first.

    Third-party checkers may opt in by inheriting this mixin, or by
    duck-typing ``supports_error_collection = True`` plus :meth:`report` and
    :meth:`collecting`. Checkers that do neither still work — they simply
    contribute at most one error, exactly as before (see
    :func:`is_collecting_checker`).

    Note:
        Not thread-safe: the sink lives on the instance. Checkers are already
        stateful (they accumulate OIDs), so use one checker per document per
        thread.
    """

    supports_error_collection = True
    _error_sink = None                       # class-level default => fail-fast

    def report(self, error):
        """Raise *error* (fail-fast) or hand it to the installed sink.

        Args:
            error: The :class:`OdmlibError` describing the problem.

        Raises:
            OdmlibError: The error itself, when no sink is installed.
            _ErrorLimitReached: When the sink is full (see
                :class:`ErrorCollector`).
        """
        sink = self._error_sink
        if sink is None:
            raise error
        sink.add_error(error)

    @contextlib.contextmanager
    def collecting(self, sink):
        """Install *sink* for the duration of the block, then restore.

        Args:
            sink: Any object with an ``add_error(error)`` method — normally an
                :class:`ErrorCollector`.

        Example::

            collector = ErrorCollector()
            with checker.collecting(collector):
                odm.verify_oids(checker)
            for err in collector.errors:
                print(err)
        """
        previous = self.__dict__.get("_error_sink")
        self.__dict__["_error_sink"] = sink
        try:
            yield self
        finally:
            if previous is None:
                self.__dict__.pop("_error_sink", None)
            else:
                self.__dict__["_error_sink"] = previous


def is_collecting_checker(checker):
    """Return True if *checker* implements the collecting-checker protocol.

    Used by :meth:`~odmlib.odm_element.ODMElement.validate` to decide whether
    a checker can enumerate every problem or should fall back to fail-fast
    (one error for the whole layer). Duck-typed checkers qualify without
    inheriting :class:`ErrorReporting`.
    """
    return (
        bool(getattr(checker, "supports_error_collection", False))
        and callable(getattr(checker, "report", None))
        and callable(getattr(checker, "collecting", None))
    )
