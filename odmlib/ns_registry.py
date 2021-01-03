import validators


class Borg:
    """ borg provides a set of global attributes for the Namespace Registry singleton """
    namespaces = {}
    default_namespace = {}

    @classmethod
    def reset(cls):
        cls.namespaces = {}
        cls.default_namespace = {}


class NamespaceRegistry(Borg):
    def __init__(self, prefix=None, uri=None, is_default=False, is_reset=False):
        if is_reset:
            super().reset()
        if prefix is not None and uri is not None:
            if validators.url(uri):
                self._update_registry(prefix, uri, is_default)
            else:
                raise ValueError(f"Namespace uri is not a valid url: {uri}")

    def get_odm_namespace_entries(self):
        entries = ["xmlns=" + list(self.default_namespace.values())[0]]
        for prefix, uri in self.namespaces.items():
            if prefix != list(self.default_namespace.keys())[0]:
                entries.append("xmlns:" + prefix + "=" + uri)
        return entries

    def get_ns_entry_dict(self, prefix):
        if prefix in self.namespaces:
            return {prefix: self.namespaces[prefix]}
        else:
            return {}

    def get_ns_attribute_name(self, name, prefix):
        if prefix in self.namespaces:
            if prefix in self.default_namespace:
                return name
            else:
                return "{" + self.namespaces[prefix] + "}" + name
        else:
            raise ValueError(f"Error: Namespace with prefix {prefix} has not been registered")

    def get_prefix_ns_from_uri(self, uri):
        for prefix, ns_uri in self.namespaces.items():
            if uri.lower() == uri.lower():
                return prefix + ":", self.get_ns_entry_dict(prefix)
        raise ValueError(f"Error: Namespace with URI {uri} has not been registered")

    def set_odm_namespace_attributes(self, odm_elem):
        """ add NS attributes to the ODM XML element object """
        odm_elem.attrib["xmlns"] = list(self.default_namespace.values())[0]
        for prefix, uri in self.namespaces.items():
            if prefix != list(self.default_namespace.keys())[0]:
                odm_elem.attrib["xmlns:" + prefix] = uri

    def _update_registry(self, prefix, uri, is_default):
        self.namespaces[prefix] = uri
        if is_default:
            self.default_namespace[prefix] = uri

    def remove_registry_entry(self, prefix):
        if prefix in self.namespaces:
            self.namespaces.pop(prefix)
        if prefix in self.default_namespace:
            self.default_namespace.pop(prefix)
