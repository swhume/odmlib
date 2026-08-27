"""Global registry for XML namespace prefix-to-URI mappings.

This module provides :class:`Borg` and :class:`NamespaceRegistry` for
managing XML namespace declarations used in ODM and Define-XML documents.

The Borg pattern ensures that all instances of :class:`NamespaceRegistry`
share the same state, providing a convenient global registry without
requiring a strict singleton or global variable.

Example::

    import odmlib.ns_registry as NS

    NS.NamespaceRegistry(prefix="odm",
        uri="http://www.cdisc.org/ns/odm/v1.3",
        is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="def",
        uri="http://www.cdisc.org/ns/def/v2.1")
"""
import validators
import warnings
import weakref
from odmlib.exceptions import OdmlibDeprecationWarning, OdmlibNamespaceError


# Side table associating loaded document roots with the namespace state in
# effect when they were loaded.  Because NamespaceRegistry state is shared
# process-wide (Borg), loading a second document can change the registry;
# serialization consults this table first so a document is always written
# with the namespaces it was loaded under.
_DOCUMENT_NAMESPACES: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _is_odm_element(obj):
    """True for odmlib model objects, without importing them.

    ``odm_element`` imports this module, so a real isinstance check would be circular.
    Every model class gets ``_elems`` from ``ODMMeta``, which makes it a reliable marker.
    """
    return hasattr(obj, "_elems") and hasattr(obj, "__dict__")


def _bind_one(odm_obj, snapshot):
    try:
        _DOCUMENT_NAMESPACES[odm_obj] = snapshot
    except TypeError:
        pass  # objects that do not support weak references fall back to global state


def bind_document_namespaces(odm_obj, snapshot=None, recursive=False):
    """Associate *odm_obj* with a namespace snapshot for serialization.

    Args:
        odm_obj: A loaded odmlib element (typically the document root).
        snapshot: A dict as returned by :meth:`NamespaceRegistry.snapshot`.
            When ``None``, the registry's current state is captured.
        recursive: When True, also bind every descendant element, so that
            serializing a child reached by walking the tree
            (``define.Study.MetaDataVersion``) uses the same namespaces as its
            root instead of falling back to current global registry state.
    """
    # Resolve the snapshot exactly once so the whole walk shares one dict. Resolving
    # per node would mint a fresh dict each time and defeat any identity-based guard.
    if snapshot is None:
        snapshot = NamespaceRegistry().snapshot()
    if not recursive:
        _bind_one(odm_obj, snapshot)
        return

    # Guard on id(), not on "already mapped to this snapshot" - the latter cannot
    # distinguish a revisit from a legitimate rebind and degenerates on cycles.
    # Every object here stays reachable from odm_obj for the duration, so ids are stable.
    visited = set()
    stack = [odm_obj]
    while stack:
        obj = stack.pop()
        if obj is None or id(obj) in visited:
            continue
        visited.add(id(obj))
        _bind_one(obj, snapshot)
        children = getattr(obj, "__dict__", None)
        if not children:
            continue
        for value in children.values():
            if isinstance(value, list):
                stack.extend(item for item in value if _is_odm_element(item))
            elif _is_odm_element(value):
                stack.append(value)


def get_document_namespaces(odm_obj):
    """Return the namespace snapshot bound to *odm_obj*, or ``None``."""
    try:
        return _DOCUMENT_NAMESPACES.get(odm_obj)
    except TypeError:
        return None


class Borg:
    """Borg pattern base class providing shared state across instances.

    All instances of subclasses share the same ``namespaces`` and
    ``default_namespace`` dictionaries, enabling a singleton-like
    namespace registry without requiring a true singleton.

    Class Attributes:
        namespaces (dict): Maps prefix to URI for all registered namespaces.
        default_namespace (dict): Maps the default namespace prefix to URI.
    """

    namespaces = {}
    default_namespace = {}

    @classmethod
    def reset(cls):
        """Reset all shared namespace state to empty dicts.

        Should be called between tests or when reinitializing the registry
        from scratch to prevent cross-test state leakage.
        """
        cls.namespaces = {}
        cls.default_namespace = {}


class NamespaceRegistry(Borg):
    """Global registry for XML namespace prefix-to-URI mappings.

    Uses the Borg pattern so all instances share state. Manages namespace
    prefix registration and provides methods for XML serialization.

    Args:
        prefix (str): Namespace prefix (e.g., "odm", "def", "xs").
        uri (str): Namespace URI (must be a valid URL).
        is_default (bool): If True, this becomes the default namespace
            (used for xmlns= in XML output).
        is_reset (bool): If True, clears all existing entries first.

    Raises:
        OdmlibNamespaceError: If the URI is not a valid URL.

    Example::

        import odmlib.ns_registry as NS
        NS.NamespaceRegistry(prefix="odm",
            uri="http://www.cdisc.org/ns/odm/v1.3",
            is_default=True, is_reset=True)
    """

    def __init__(self, prefix=None, uri=None, is_default=False, is_reset=False):
        if is_reset:
            super().reset()
        if prefix is not None and uri is not None:
            if validators.url(uri):
                self._update_registry(prefix, uri, is_default)
            else:
                raise OdmlibNamespaceError(
                    f"Namespace uri is not a valid url: {uri}",
                    hint="Provide a valid URI, e.g., 'http://www.cdisc.org/ns/odm/v1.3'",
                )

    def snapshot(self):
        """Return a copy of the current registry state.

        Returns:
            dict: ``{"namespaces": {prefix: uri, ...}, "default": {prefix: uri}}``.
        """
        return {
            "namespaces": dict(self.namespaces),
            "default": dict(self.default_namespace),
        }

    def _require_default(self, default_map=None):
        """Return the default (prefix, uri) pair or raise a clear error."""
        default_map = self.default_namespace if default_map is None else default_map
        if not default_map:
            raise OdmlibNamespaceError(
                "No default namespace has been registered",
                hint="Register one first, e.g. NamespaceRegistry(prefix='odm', "
                     "uri='http://www.cdisc.org/ns/odm/v1.3', is_default=True)",
            )
        prefix = next(iter(default_map))
        return prefix, default_map[prefix]

    def get_odm_namespace_entries(self):
        """Return namespace entries as xmlns= strings for XML serialization.

        Returns:
            list[str]: A list of strings like ``["xmlns=http://...", "xmlns:def=http://..."]``.
                The first entry is always the default namespace.
        """
        default_prefix, default_uri = self._require_default()
        entries = ["xmlns=" + default_uri]
        for prefix, uri in self.namespaces.items():
            if prefix != default_prefix:
                entries.append("xmlns:" + prefix + "=" + uri)
        return entries

    def get_ns_entry_dict(self, prefix):
        """Return a ``{prefix: uri}`` dict for the given prefix, or ``{}`` if not found.

        Used by loaders to build the ``namespaces`` dict for ElementTree
        ``find`` and ``findall`` calls.

        Args:
            prefix (str): Namespace prefix to look up.

        Returns:
            dict: ``{prefix: uri}`` if registered, otherwise ``{}``.
        """
        if prefix in self.namespaces:
            return {prefix: self.namespaces[prefix]}
        else:
            return {}

    def get_ns_attribute_name(self, name, prefix):
        """Return the full ElementTree-style attribute name with namespace braces.

        For the default namespace, returns the bare ``name``. For
        non-default namespaces, returns ``{uri}name``.

        Args:
            name (str): The local attribute name.
            prefix (str): The namespace prefix.

        Returns:
            str: The qualified attribute name (e.g., ``"{http://...}lang"``
                or ``"lang"`` for the default namespace).

        Raises:
            OdmlibNamespaceError: If ``prefix`` has not been registered.
        """
        if prefix in self.namespaces:
            if prefix in self.default_namespace:
                return name
            else:
                return "{" + self.namespaces[prefix] + "}" + name
        else:
            raise OdmlibNamespaceError(
                f"Error: Namespace with prefix {prefix} has not been registered",
                hint=f"Register the namespace first: NamespaceRegistry(prefix='{prefix}', uri='...')",
            )

    def get_prefix_ns_from_uri(self, uri):
        """Return the prefix for a given namespace URI.

        Args:
            uri (str): The namespace URI to look up (case-insensitive match).

        Returns:
            str: The registered prefix for that URI.

        Raises:
            OdmlibNamespaceError: If no prefix is registered for ``uri``.
        """
        for prefix, ns_uri in self.namespaces.items():
            if uri.lower() == ns_uri.lower():
                return prefix
        raise OdmlibNamespaceError(
            f"Error: Namespace with URI {uri} has not been registered",
            hint="Register the namespace URI first via NamespaceRegistry(prefix=..., uri=...)",
        )

    @staticmethod
    def _used_prefixes(odm_elem):
        """Collect the namespace prefixes actually used in a serialized tree.

        odmlib emits prefixed tags and attribute names as literal
        ``prefix:name`` strings, so a simple scan finds every prefix the
        document actually needs a declaration for.
        """
        used = set()
        for elem in odm_elem.iter():
            if ":" in elem.tag:
                used.add(elem.tag.split(":", 1)[0])
            for attr_name in elem.attrib:
                if ":" in attr_name and not attr_name.startswith("xmlns"):
                    used.add(attr_name.split(":", 1)[0])
        return used

    def set_odm_namespace_attributes(self, odm_elem, namespaces=None, default=None):
        """Set xmlns attributes on an ElementTree root element.

        Adds ``xmlns`` for the default namespace and ``xmlns:prefix`` for
        each additional namespace that is actually used in the tree.  The
        reserved ``xml`` prefix is never declared (it is implicitly bound
        per the XML specification).

        Args:
            odm_elem (ET.Element): The root XML element to annotate.
            namespaces (dict): Optional ``{prefix: uri}`` map to use instead
                of the registry's shared state (e.g. a per-document snapshot).
            default (dict): Optional ``{prefix: uri}`` default-namespace map
                to use instead of the registry's shared state.

        Raises:
            OdmlibNamespaceError: If no default namespace is registered.
        """
        ns_map = self.namespaces if namespaces is None else namespaces
        default_prefix, default_uri = self._require_default(default)
        odm_elem.attrib["xmlns"] = default_uri
        used = self._used_prefixes(odm_elem)
        for prefix, uri in ns_map.items():
            if prefix in (default_prefix, "xml"):
                continue
            if prefix in used:
                odm_elem.attrib["xmlns:" + prefix] = uri

    def set_odm_namespace_attributes_string(self, odm_str):
        """Add xmlns attributes to an ODM XML string.

        .. deprecated:: 0.2.1
            :meth:`ODMElement.to_xml_string` has declared its own namespaces since
            0.2.1, so this string-patching helper is a no-op on any string it would
            normally be handed. It has no callers in odmlib and will be removed in
            0.3.0. Remove the call; no replacement is needed.

        Replaces the opening ``<ODM`` tag in ``odm_str`` with a version
        that includes all registered namespace declarations.

        Args:
            odm_str (str): An ODM XML string whose root element is ``<ODM>``.

        Returns:
            str: The modified XML string with xmlns attributes injected.
        """
        warnings.warn(
            "NamespaceRegistry.set_odm_namespace_attributes_string() is deprecated and "
            "will be removed in 0.3.0. to_xml_string() already emits its own xmlns "
            "declarations, so this call is a no-op for strings it produces.",
            OdmlibDeprecationWarning,
            stacklevel=2,
        )
        # no-op when the root element already declares a namespace (e.g. a
        # string produced by to_xml_string(), which is now self-contained)
        root_tag_end = odm_str.find(">", odm_str.find("<ODM"))
        if root_tag_end != -1 and "xmlns" in odm_str[:root_tag_end]:
            return odm_str
        default_prefix, default_uri = self._require_default()
        ns_str = "<ODM xmlns=\"" + default_uri + "\""
        for prefix, uri in self.namespaces.items():
            if prefix != default_prefix:
                ns_str += " xmlns:" + prefix + "=\"" + uri + "\""
        odm_ns_str = odm_str.replace("<ODM", ns_str)
        return odm_ns_str

    def _update_registry(self, prefix, uri, is_default):
        """Add or update an entry in the shared namespace registry.

        Only a single default namespace is kept: registering a new default
        replaces any previous one rather than accumulating alongside it
        (which made the effective default depend on registration order).

        Args:
            prefix (str): Namespace prefix.
            uri (str): Namespace URI.
            is_default (bool): If True, this becomes THE default namespace.
        """
        self.namespaces[prefix] = uri
        if is_default:
            self.default_namespace.clear()
            self.default_namespace[prefix] = uri

    def remove_registry_entry(self, prefix):
        """Remove a namespace entry by prefix.

        Removes the prefix from both ``namespaces`` and
        ``default_namespace`` (if present).

        Args:
            prefix (str): The namespace prefix to remove.
        """
        if prefix in self.namespaces:
            self.namespaces.pop(prefix)
        if prefix in self.default_namespace:
            self.default_namespace.pop(prefix)
