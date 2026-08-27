import json
import re
from pathlib import Path
from odmlib.exceptions import OdmlibValidationError


class _UnknownAttribute:
    """Sentinel returned by :meth:`ValueSet.value_set` when an attribute key
    is absent from the resolved version *and* every fallback version.

    Distinct from an unknown *version*, which still raises
    ``OdmlibValidationError``. Returning a sentinel (rather than raising)
    lets ``validate()`` report ``False`` so the ``SKIP_VALUESET`` permissive
    guard in ``ValidValues.__set__`` can take effect for unregistered keys.
    """

    __slots__ = ()

    def __repr__(self):
        return "<ValueSet.UNKNOWN_ATTRIBUTE>"


UNKNOWN_ATTRIBUTE = _UnknownAttribute()


class ValueSetLoader:
    """Loads and caches valueset data from JSON file"""
    _cache = None  # Class variable for singleton cache
    _version_map = None  # Maps module paths to versions

    @classmethod
    def load_valuesets(cls):
        """Load JSON once, cache in memory (lazy loading)"""
        if cls._cache is None:
            data_dir = Path(__file__).parent / 'data'
            json_path = data_dir / 'valuesets.json'
            with open(json_path, 'r', encoding='utf-8') as f:
                cls._cache = json.load(f)
            cls._build_version_map()
        return cls._cache

    @classmethod
    def _build_version_map(cls):
        """Map module paths to version keys"""
        cls._version_map = {
            'odmlib.odm_1_3_2.model': 'odm_1_3_2',
            'odmlib.odm_2_0.model': 'odm_2_0',
            'odmlib.define_2_0.model': 'define_2_0',
            'odmlib.define_2_1.model': 'define_2_1',
            'odmlib.arm_1_0.model': 'define_2_1',      # ARM extends Define-XML 2.1
            'odmlib.ct_1_1_1.model': 'ct_1_1_1',
            'odmlib.dataset_1_0_1.model': 'dataset_1_0_1',
            # Add test models
            'tests.model_extended': 'odm_1_3_2',  # Test extension uses base
        }

    # Pattern markers checked against unknown module paths, in priority order.
    # Order matters: 'odm_2_0' must be tried before 'odm_1_3_2' substrings, etc.
    _MODULE_PATTERNS = (
        ('odm_2_0', 'odm_2_0'),
        ('define_2_1', 'define_2_1'),
        ('arm_1_0', 'define_2_1'),
        ('define_2_0', 'define_2_0'),
        ('ct_1_1_1', 'ct_1_1_1'),
        ('dataset_1_0_1', 'dataset_1_0_1'),
    )

    @classmethod
    def get_version_for_module(cls, module_path, instance_class=None):
        """Determine the valueset version for a module path.

        Resolution order:
        1. Exact match in the version map.
        2. Substring marker match against the module path.
        3. If ``instance_class`` is provided, walk its MRO and recurse on each
           base class's module — this lets local models that subclass a shipped
           odmlib model inherit the correct version.
        4. Fallback: ``odm_1_3_2`` for backward compatibility.
        """
        if cls._version_map is None:
            cls.load_valuesets()

        if module_path in cls._version_map:
            return cls._version_map[module_path]

        for marker, version in cls._MODULE_PATTERNS:
            if marker in module_path:
                return version

        if instance_class is not None:
            for base in instance_class.__mro__[1:]:
                base_module = getattr(base, '__module__', '')
                if not base_module or base_module == 'builtins':
                    continue
                if base_module in cls._version_map:
                    return cls._version_map[base_module]
                for marker, version in cls._MODULE_PATTERNS:
                    if marker in base_module:
                        return version

        return 'odm_1_3_2'


class ValueSet:
    """Backward-compatible interface to valueset data.

    Supports three entry types in valuesets.json:
    - **list**: A closed set of allowed string values (e.g., ``["Yes", "No"]``)
    - **regex dict**: A dict with ``_regex`` key and optional ``_description``
      (e.g., ``{"_regex": "^2\\\\.[01](\\\\.\\\\d+)?$", "_description": "..."}``).
    - **open dict**: A dict with ``_values`` and ``_open: true`` for an
      *extensible* vocabulary — the XSD models these as a union of an
      enumeration with bare ``xs:string``, so any value is permitted while the
      listed terms remain the documented ones
      (e.g., ``{"_values": ["Form", "Dataset"], "_open": true}``).

    .. versionadded:: 0.2.1
       The open-dict form. ODM 2.0 uses extensible unions for
       ``ItemGroupDef/@Type``, ``TrialPhase/@Value`` and ``Standard/@Status``;
       enforcing them as closed lists rejected schema-valid documents.
    """

    #: Sentinel returned by :meth:`value_set` for an unknown attribute key
    #: (see :class:`_UnknownAttribute`). Exposed for callers/tests.
    UNKNOWN_ATTRIBUTE = UNKNOWN_ATTRIBUTE

    _compiled_regex_cache = {}  # (version, attribute) -> compiled re.Pattern

    # Versions tried (in order) when an attribute is missing from the resolved
    # version. Hybrid local models (e.g. an ODM 1.3.2 base extended with
    # Define-XML 2.x attributes) need this to find Define-only keys.
    _FALLBACK_VERSIONS = (
        'define_2_1', 'define_2_0', 'odm_2_0', 'odm_1_3_2',
        'ct_1_1_1', 'dataset_1_0_1',
    )

    @classmethod
    def _resolve_version(cls, version, instance):
        """Resolve the version string from explicit value or instance."""
        if version is None and instance is not None:
            instance_class = type(instance)
            module_path = instance_class.__module__
            return ValueSetLoader.get_version_for_module(
                module_path, instance_class=instance_class,
            )
        elif version is None:
            return 'odm_1_3_2'
        return version

    @classmethod
    def value_set(cls, attribute, version=None, instance=None):
        """
        Get the raw valueset entry for an attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            list or dict: A list of valid values, or a dict with ``_regex``
            key for pattern-based validation. Returns the
            :data:`UNKNOWN_ATTRIBUTE` sentinel if the attribute key is not
            registered for the resolved version or any fallback version.

        Raises:
            OdmlibValidationError: If the *version* is not found in the
            valueset. An unknown *attribute* no longer raises — it returns
            the :data:`UNKNOWN_ATTRIBUTE` sentinel instead.
        """
        version = cls._resolve_version(version, instance)

        # Load valuesets (cached)
        valuesets = ValueSetLoader.load_valuesets()

        # Get version-specific valueset
        if version not in valuesets:
            raise OdmlibValidationError(
                f"Unknown version {version} in ValueSet",
                hint=f"Valid versions are: {list(valuesets.keys())}",
            )

        version_valueset = valuesets[version]

        # Get attribute values
        if attribute in version_valueset:
            return version_valueset[attribute]

        # Cross-version fallback: hybrid local models (e.g. an ODM 1.3.2 base
        # extended with def: attributes) may carry attribute keys that only
        # exist in another shipped version's valueset. Search the others.
        for other in cls._FALLBACK_VERSIONS:
            if other == version:
                continue
            other_valueset = valuesets.get(other)
            if other_valueset is not None and attribute in other_valueset:
                return other_valueset[attribute]

        # Unknown *attribute* (absent here and in every fallback version):
        # return a sentinel rather than raising, so validate() can report
        # False and the SKIP_VALUESET permissive guard can take effect.
        # (Unknown *version* still raises, above.)
        return UNKNOWN_ATTRIBUTE

    @classmethod
    def validate(cls, attribute, value, version=None, instance=None):
        """
        Check whether a value is valid for the given attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            value: The string value to validate
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            bool: True if the value is valid, False otherwise.
        """
        version = cls._resolve_version(version, instance)
        entry = cls.value_set(attribute, version=version)

        if entry is UNKNOWN_ATTRIBUTE:
            # No registered value set for this attribute: not provably
            # valid -> False. This lets ValidValues.__set__ reach the
            # SKIP_VALUESET permissive guard instead of the old raise
            # propagating out of value_set().
            return False

        if isinstance(entry, list):
            return value in entry

        # Open (extensible) vocabulary: the listed values are documentation,
        # any string is permitted.
        if isinstance(entry, dict) and entry.get("_open"):
            return isinstance(value, str)

        # Regex dict entry
        if isinstance(entry, dict) and "_regex" in entry:
            cache_key = (version, attribute)
            if cache_key not in cls._compiled_regex_cache:
                cls._compiled_regex_cache[cache_key] = re.compile(entry["_regex"])
            pattern = cls._compiled_regex_cache[cache_key]
            return pattern.fullmatch(value) is not None

        return False

    @classmethod
    def describe(cls, attribute, version=None, instance=None):
        """
        Return a human-readable description of valid values for an attribute.

        Args:
            attribute: "ClassName.AttributeName" format
            version: Explicit version (e.g., "odm_2_0") - optional
            instance: ODMElement instance for automatic version detection - optional

        Returns:
            str: Description suitable for error messages.
        """
        version = cls._resolve_version(version, instance)
        entry = cls.value_set(attribute, version=version)

        if entry is UNKNOWN_ATTRIBUTE:
            return f"No registered value set for {attribute}"

        if isinstance(entry, list):
            return f"Value must be one of: {', '.join(entry)}"

        if isinstance(entry, dict) and entry.get("_open"):
            if "_description" in entry:
                return entry["_description"]
            listed = ", ".join(entry.get("_values", []))
            return (f"Extensible value set — the defined terms are: {listed}. "
                    f"Other values are permitted.")

        if isinstance(entry, dict) and "_regex" in entry:
            if "_description" in entry:
                return entry["_description"]
            return f"Value must match pattern: {entry['_regex']}"

        return "Unknown valueset format"
