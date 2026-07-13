"""Core metaclass, writer, and base element class for odmlib ODM models.

This module provides three central components:

- :class:`ODMMeta` -- metaclass that processes descriptor-based class definitions
- :class:`ODMWriter` -- utility class for writing ElementTree XML to file
- :class:`ODMElement` -- base class for all ODM element model objects

All model classes (e.g., ``Study``, ``ItemDef``, ``MetaDataVersion``) inherit
from :class:`ODMElement` and use descriptors from :mod:`odmlib.typed` to define
their attributes and child elements.
"""
from __future__ import annotations
from typing import Any, Optional, List
import odmlib.descriptor as DESC
import odmlib.typed as T
import odmlib.ns_registry as NS
import odmlib.oid_index as IDX
from collections import OrderedDict
import json
import warnings
import xml.etree.ElementTree as ET
from odmlib.exceptions import (
    OdmlibError,
    OdmlibTypeError,
    OdmlibRequiredAttributeError,
    OdmlibElementOrderError,
    OdmlibWarning,
    ErrorCollector,
)
import odmlib.mode as _mode


class ODMMeta(type):
    """Metaclass for all ODM element classes.

    Processes class definitions to:

    - Preserve attribute declaration order (using OrderedDict)
    - Separate XML attributes (``_attrs``) from child elements (``_elems``)
    - Track non-default namespace prefixes (``_attr_ns``)
    - Build the ``_fields`` list of all declared properties
    - Set the default ``namespace`` to "odm" if not specified
    """

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        """ preserves the order of declarations in each class """
        return OrderedDict()

    def __init__(cls, clsname, bases, clsdict, merge_fields=False):
        super().__init__(clsname, bases, dict(clsdict))

    def __new__(cls, clsname, bases, clsdict, merge_fields=False):
        """Create a new ODM element class.

        Scans ``clsdict`` for :class:`~odmlib.typed.ODMObject`,
        :class:`~odmlib.typed.ODMListObject`, and other
        :class:`~odmlib.descriptor.Descriptor` instances. Populates
        ``_fields``, ``_elems``, ``_attrs``, and ``_attr_ns`` on the
        new class. Sets ``namespace`` to ``"odm"`` if not declared.

        Args:
            clsname (str): Name of the class being created.
            bases (tuple): Base classes.
            clsdict (OrderedDict): Class namespace dictionary (ordered).
            merge_fields (bool): When True, seed ``_fields``/``_elems``/
                ``_attrs``/``_attr_ns`` from the base classes so the
                subclass inherits every declared field without having to
                redeclare it (redeclaring a field moves it to the
                subclass's declared position).  The default (False) keeps
                the historical behaviour where a subclass declares its
                effective field set from scratch — the mechanism the
                Define-XML models use to *restrict* inherited ODM fields.

        Returns:
            type: The newly constructed class object.
        """
        # variables created in classes become the class attributes
        fields = []
        elems = {}
        attrs = {}
        attr_ns = {}
        if merge_fields:
            # seed from the bases (reversed so the first base wins conflicts)
            for base in reversed(bases):
                for name in getattr(base, "_fields", []):
                    if name in fields:
                        fields.remove(name)
                    fields.append(name)
                elems.update(getattr(base, "_elems", {}))
                attrs.update(getattr(base, "_attrs", {}))
                attr_ns.update(getattr(base, "_attr_ns", {}))
        clsdict["_fields"] = fields
        clsdict["_elems"] = elems
        clsdict["_attrs"] = attrs
        clsdict["_attr_ns"] = attr_ns
        for key, val in clsdict.items():
            if isinstance(val, (T.ODMObject, T.ODMListObject)):
                if key in fields:
                    fields.remove(key)
                attrs.pop(key, None)
                elems[key] = val
                clsdict[key].name = key
                fields.append(key)
            elif isinstance(val, (DESC.Descriptor, ODMMeta)):
                if key in fields:
                    fields.remove(key)
                elems.pop(key, None)
                attrs[key] = val
                clsdict[key].name = key
                fields.append(key)
                if val.namespace != "odm":
                    attr_ns[key] = val.namespace
                else:
                    attr_ns.pop(key, None)

        # the default class namespace is odm (merged subclasses inherit theirs)
        if "namespace" not in clsdict:
            if not (merge_fields and any(hasattr(base, "namespace") for base in bases)):
                clsdict["namespace"] = "odm"

        clsobj = super().__new__(cls, clsname, bases, dict(clsdict))
        return clsobj


class ODMWriter:
    """Writes an odmlib ElementTree hierarchy to an XML file.

    Handles namespace registration and XML declaration.
    """

    @staticmethod
    def write_odm(odm_file, odm_elem, ns_snapshot=None):
        """
        after converting ODMLIB to ElementTree, write the ElementTree to an ODM file
        :param odm_file: path and file to write the ODM XML
        :param odm_elem: Element object to write to ODM (presumably an ODM root)
        :param ns_snapshot: optional per-document namespace snapshot (as returned
            by NamespaceRegistry.snapshot()); when omitted, the shared registry
            state is used
        """
        tree = ET.ElementTree(odm_elem)
        root = tree.getroot()
        nsr = NS.NamespaceRegistry()
        if ns_snapshot:
            nsr.set_odm_namespace_attributes(
                root, namespaces=ns_snapshot["namespaces"], default=ns_snapshot["default"])
        else:
            nsr.set_odm_namespace_attributes(root)
        tree.write(odm_file, xml_declaration=True, encoding='UTF-8', method='xml', short_empty_elements=True)


class ODMElement(metaclass=ODMMeta):
    """Base class for all ODM element model objects.

    Provides XML and JSON serialization, OID validation, conformance
    checking, and element ordering verification. All model classes
    (e.g., Study, ItemDef, MetaDataVersion) inherit from this class.

    Serialization:
        - :meth:`to_xml` -- generate ElementTree XML
        - :meth:`to_xml_string` -- XML as a string
        - :meth:`to_dict` -- Python dict (namespace info stripped)
        - :meth:`to_json` -- JSON string
        - :meth:`write_xml` -- write XML to file
        - :meth:`write_json` -- write JSON to file

    Validation:
        - :meth:`verify_oids` -- OID uniqueness and ref/def integrity
        - :meth:`verify_conformance` -- Cerberus schema conformance
        - :meth:`verify_order` -- element order per ODM spec
        - :meth:`validate` -- combined validation with error collection

    Finding elements:
        - :meth:`find` -- find first child element by attribute value
        - :meth:`find_all` -- find all matching child elements
        - :meth:`find_by` -- find by multiple attribute criteria
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize an ODM element with keyword arguments.

        Sets attributes and child elements on the instance using the
        provided keyword arguments. Validates that all required attributes
        are present after construction.

        Args:
            **kwargs: Attribute names and values for this element.
                Names must match declared descriptors on the class.

        Raises:
            OdmlibTypeError: If an unknown keyword argument is provided.
            OdmlibRequiredAttributeError: If a required attribute is missing.
        """
        for name, val in kwargs.items():
            if name not in self._fields and name not in self.__class__.__dict__:
                # strip out non-default elementtree namespaces from the XML to work with just the name e.g. xml:lang
                if "}" in name:
                    name = name[name.find('}') + 1:]
                else:
                    if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
                        raise OdmlibTypeError(
                            f"Unknown keyword argument {name} in {self.__class__.__name__}",
                            attribute=name,
                            element_type=self.__class__.__name__,
                            hint=f"Valid attributes for {self.__class__.__name__}: "
                                 f"{', '.join(k for k in self._fields if not k.startswith('_'))}",
                        )
                    continue
            setattr(self, name, val)
        if not _mode.is_permissive(_mode.ValidationMode.SKIP_REQUIRED):
            for attr, obj in self._attrs.items():
                if isinstance(obj, DESC.Descriptor) and (not isinstance(obj, T.ODMObject)) and (attr not in self.__dict__) and obj.required:
                    raise OdmlibRequiredAttributeError(
                        f"Missing required keyword argument {attr} in {self.__class__.__name__}",
                        attribute=attr,
                        element_type=self.__class__.__name__,
                        hint=f"Attribute '{attr}' is required when constructing {self.__class__.__name__}",
                    )

    def __setattr__(self, key, value):
        """Set an attribute, validating it belongs to this class.

        Delegates to the descriptor protocol after confirming ``key``
        is a declared field on this class.

        Args:
            key (str): Attribute name.
            value: Value to assign.

        Raises:
            OdmlibTypeError: If ``key`` is not a declared attribute on this class.
        """
        """ ensure the object being added is a type that belongs to the class """
        if key in self._fields:
            super().__setattr__(key, value)
            return
        # non-descriptor class attributes keep the historical MRO lookup, but
        # a descriptor deliberately dropped by a restricted subclass (e.g. the
        # Define-XML models omitting ODM-only children) must not be assignable
        # — previously such assignments succeeded and then serialized
        # inconsistently or not at all
        if any(key in cls.__dict__ for cls in type(self).__mro__) \
                and not isinstance(getattr(type(self), key, None), DESC.Descriptor):
            super().__setattr__(key, value)
            return
        if not _mode.is_permissive(_mode.ValidationMode.SKIP_TYPE):
            raise OdmlibTypeError(
                f"Assignment error: {self.__class__.__name__} does not have a defined attribute {key}",
                attribute=key,
                element_type=self.__class__.__name__,
            )
        else:
            self.__dict__[key] = value

    def to_json(self) -> str:
        """
        transforms odmlib hierarchy into a dict and converts that to JSON and returns it

        :return: JSON representation of odmlib hierarchy
        """
        return json.dumps(self.to_dict())

    def to_xml(self, parent_elem: Optional[ET.Element] = None, top_elem: Optional[ET.Element] = None) -> Optional[ET.Element]:
        """Generate ElementTree XML from the odmlib object hierarchy.

        Children are emitted in the model declaration order recorded in
        ``_elems`` by :class:`ODMMeta` (i.e. the order in which descriptors
        appear in the class body of the relevant model module). Attribute
        insertion order on the instance does not affect the output, so users
        do not need to call :meth:`reorder_object` before serializing.

        Optional children that were never assigned are silently skipped.

        :param parent_elem: (obj) Element that is the parent of the element to be created
        :param top_elem: (obj) Topmost element that has been created
        :return: top_elem: (obj) Topmost element created during the recursive calls
        """
        # create attributes
        attrs = {}
        for attr, obj in self.__dict__.items():
            if not isinstance(obj, (ODMElement, list)) and attr != "_content" and obj is not None:
                # add namespace if not the default namespace
                if attr in self.__class__.__dict__["_attr_ns"]:
                    attrs[self.__class__.__dict__["_attr_ns"][attr] + ":" + attr] = str(obj)
                else:
                    attrs[attr] = str(obj)

        # create element
        if isinstance(parent_elem, ET.Element):
            odm_elem = ET.SubElement(parent_elem, self.__class__.__name__ if self.namespace == "odm" else self.namespace + ":" + self.__class__.__name__, attrs)
        else:
            odm_elem = ET.Element(self.__class__.__name__ if self.namespace == "odm" else self.namespace + ":" + self.__class__.__name__, attrs)
            top_elem = odm_elem
        # add text to element if it exists
        if "_content" in self.__dict__:
            odm_elem.text = self.__dict__["_content"]
        # emit children in model declaration order (driven by _elems), not __dict__ insertion order,
        # so the schema's required element ordering is preserved regardless of how the user assigned attributes.
        for name in self._elems:
            obj = self.__dict__.get(name)
            if isinstance(obj, list) and obj:
                for o in obj:
                    o.to_xml(odm_elem, top_elem)
            elif isinstance(obj, ODMElement) and not DESC.is_pristine_auto_created(obj):
                obj.to_xml(odm_elem, top_elem)
        return top_elem

    def to_xml_string(self) -> str:
        """Convert this element to an XML string.

        The string includes xmlns declarations for the default namespace and
        any prefixes used in the serialized tree, so the result is
        namespace-well-formed and can be re-parsed on its own.

        Returns:
            str: UTF-8 XML representation of this element.
        """
        elem = self.to_xml()
        nsr = NS.NamespaceRegistry()
        snapshot = NS.get_document_namespaces(self)
        if snapshot:
            nsr.set_odm_namespace_attributes(
                elem, namespaces=snapshot["namespaces"], default=snapshot["default"])
        else:
            nsr.set_odm_namespace_attributes(elem)
        xml_str = ET.tostring(elem, encoding='UTF-8', method='xml')
        return xml_str.decode("utf-8")

    def to_dict(self) -> dict:
        """
        transform odmlib object hierarchy into a Python dictionary and return it

        :return: dictionary serialization of odmlib hierarchy
        """
        # Note: namespaces used in the XML serialization are not part of the dictionary or json serializations
        property_dict = {}
        for attr, obj in self.__dict__.items():
            if isinstance(obj, ODMElement):
                if not DESC.is_pristine_auto_created(obj):
                    property_dict[attr] = obj.to_dict()                # element
            elif isinstance(obj, list):
                property_dict[attr] = [o.to_dict() for o in obj]       # list of ELEMENTS
            elif obj is not None:
                property_dict[attr] = obj                              # attributes
        return property_dict

    def __repr__(self):
        """Return a developer-readable representation of this element.

        Returns:
            str: Class name with declared field names listed.
        """
        args = ", ".join(name for name in self._fields)
        return type(self).__name__ + "(" + args + ")"

    def __str__(self):
        """Return a human-readable representation of this element.

        Returns the element's text content if present, or its OID value
        if it has one, otherwise falls back to a field name listing.

        Returns:
            str: Human-readable string for this element.
        """
        if "_content" in self._fields and self._content:
            return self._content
        elif "OID" in self._fields and self.OID:
            return type(self).__name__ + "(OID=" + self.OID + ")"
        else:
            args = ", ".join(name for name in self._fields)
            return type(self).__name__ + "(" + args + ")"

    def find(self, obj_name: str, attr: str, val: Any) -> Optional[ODMElement]:
        """Return the first odmlib object where attribute ``attr`` equals ``val``.

        Searches within the child element(s) named ``obj_name`` on this element.
        For list elements (ODMListObject), returns the first match.
        For single elements (ODMObject), returns the element if it matches.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param attr: text name of the ODM Element Attribute (case sensitive)
        :param val: attribute value to search for
        :return: first matching odmlib object, or None if not found
        """
        obj_list = getattr(self, obj_name)
        if isinstance(obj_list, list):
            for o in obj_list:
                if o.__dict__.get(attr) == val:
                    return o
            return None
        elif isinstance(obj_list, ODMElement):
            if obj_list.__dict__.get(attr) == val:
                return obj_list
            return None
        else:
            # unset single element (None) or a scalar attribute name
            return None

    def find_all(self, obj_name: str, attr: str, val: Any) -> List[ODMElement]:
        """Return all odmlib objects where attribute ``attr`` equals ``val``.

        Like find(), but returns all matches instead of just the first.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param attr: text name of the ODM Element Attribute (case sensitive)
        :param val: attribute value to search for
        :return: list of matching odmlib objects (empty list if no matches)
        """
        obj_list = getattr(self, obj_name)
        if isinstance(obj_list, list):
            return [o for o in obj_list if o.__dict__.get(attr) == val]
        elif isinstance(obj_list, ODMElement):
            if obj_list.__dict__.get(attr) == val:
                return [obj_list]
            return []
        else:
            # unset single element (None) or a scalar attribute name
            return []

    def find_by(self, obj_name: str, **kwargs: Any) -> Optional[ODMElement]:
        """Return the first odmlib object matching all keyword criteria.

        A more ergonomic alternative to find() for multi-attribute lookups.

        :param obj_name: text name of the ODM Element (case sensitive)
        :param kwargs: attribute name=value pairs to match
        :return: first matching odmlib object, or None
        """
        obj_list = getattr(self, obj_name)
        if not isinstance(obj_list, list):
            obj_list = [obj_list] if isinstance(obj_list, ODMElement) else []
        for o in obj_list:
            if all(o.__dict__.get(k) == v for k, v in kwargs.items()):
                return o
        return None

    def write_xml(self, odm_file: str, odm_writer: type = ODMWriter) -> None:
        """
        write the odmlib hierarchy as an XML file

        :param odm_file: string ODM filename and path
        :param odm_writer: object used to write the elementree XML to a file
        """
        odm_elem = self.to_xml()
        writer_cls = odm_writer
        odm_writer = odm_writer()
        if writer_cls is ODMWriter:
            # use the namespaces this document was loaded under, if known,
            # so later loads of other documents cannot change its xmlns
            odm_writer.write_odm(odm_file, odm_elem,
                                 ns_snapshot=NS.get_document_namespaces(self))
        else:
            odm_writer.write_odm(odm_file, odm_elem)

    def write_json(self, odm_file: str) -> None:
        """
        write the odmlib hierarchy as a JSON file

        :param odm_file: string ODM filename and path
        """
        with open(odm_file, 'w', encoding='utf-8') as outfile:
            json.dump(self.to_dict(), outfile)

    def build_oid_index(self) -> IDX.OIDIndex:
        """Build an OID lookup index for this element and all descendants.

        Traverses the entire object tree and creates an index mapping
        OID attribute values to their containing odmlib objects.

        Returns:
            OIDIndex: Index supporting ``find_all(oid)`` lookups.
        """
        idx = IDX.OIDIndex()
        self._init_oid_index(idx)
        return idx

    def _init_oid_index(self, idx):
        """
        for odmlib object, loads all OIDs into a dict that functions as an OID index

        :return oid_index: object that provices a dictionary lookup based on OID
        """
        for attr, obj in self.__dict__.items():
            if isinstance(obj, ODMElement):
                obj._init_oid_index(idx)                    # element
            elif isinstance(obj, list):
                for o in obj:
                    o._init_oid_index(idx)                  # list of ELEMENTS
            else:
                if attr == "OID" or "OID" in attr:
                    idx.add_oid(obj, self)
        return

    def verify_oids(self, oid_checker: Any) -> bool:
        """
        checks all the OIDs for uniqueness and Def/Ref integrity; oid_checker throws a ValueError on failure

        :param oid_checker: object that performs that checks OID uniqueness and Def/Ref checks
        """
        self._init_oid_check(oid_checker)
        return oid_checker.check_oid_refs()

    def unreferenced_oids(self, oid_checker: Any) -> list:
        """Find OID definitions that are not referenced anywhere.

        Calls :meth:`verify_oids` first if OIDs have not yet been verified.

        Args:
            oid_checker: An ``OIDRef`` instance (from ``rules/oid_ref.py``)
                or a ``DynamicOIDRef`` instance.

        Returns:
            list: OID definition values that have no corresponding references.
        """
        if not oid_checker.is_oids_verified():
            self.verify_oids(oid_checker)
        return oid_checker.check_unreferenced_oids()

    def _init_oid_check(self, oid_checker):
        """
        for odmlib object, loads all OIDs and checks them for uniqueness; throws an error if uniqueness check fails

        :param oid_checker: object used to check OIDs for uniqueness and Def/Ref check
        """
        for attr, obj in self.__dict__.items():
            if isinstance(obj, ODMElement):
                obj._init_oid_check(oid_checker)                    # element
            elif isinstance(obj, list):
                for o in obj:
                    o._init_oid_check(oid_checker)                  # list of ELEMENTS
            else:
                # assumes consistency in OID naming. Exceptions: FileOID and PriorFileOID in ODM.
                # Define-XML document references are ID-based rather than OID-named:
                # leaf/@ID is the definition, referenced by leafID and def:ArchiveLocationID.
                if attr == "OID":
                    oid_checker.add_oid(obj, self.__class__.__name__)
                elif attr == "ID" and self.__class__.__name__ == "leaf":
                    oid_checker.add_oid(obj, self.__class__.__name__)
                elif "OID" in attr or attr in ("leafID", "ArchiveLocationID"):
                    oid_checker.add_oid_ref(obj, attr)
        return

    def verify_conformance(self, validator: Any) -> Any:
        """
        uses validator object to check object for conformance with the model

        :param validator: object that validates the odmlib object against the model
        """
        doc_dict = self.to_dict()
        result = validator.check_conformance(doc_dict, type(self).__name__)
        return result

    def verify_order(self) -> bool:
        """Verify that child elements are in the model declaration order.

        Recursively checks this element and all descendants — calling at
        the odmlib root covers the whole document. Works on any
        :class:`ODMElement` subclass; not applicable to
        :class:`xml.etree.ElementTree.Element` (load through a loader
        first if you only have an ElementTree).

        Limitations:

        * Each class's expected order comes from descriptors declared in
          its own class body. Custom extensions that subclass a model
          class must redeclare base children in schema order — otherwise
          inherited children are flagged as unexpected.
        * In permissive mode (:class:`~odmlib.mode.ValidationMode.SKIP_TYPE`)
          unknown attributes can land in ``__dict__``; they will trip
          this check until cleaned up.
        * Only the order of *different* child element kinds is checked.
          Order within a single list (e.g. multiple ``ItemRef`` entries)
          is not validated — ODM relies on ``OrderNumber`` attributes
          for that.
        * Completeness is not checked. Missing required children must be
          caught via :meth:`verify_conformance` or :meth:`validate`.

        Note:
            :meth:`to_xml` / :meth:`write_xml` already emit children in
            ``_elems`` order, so ``verify_order()`` is **not** required
            before XML serialization. It is still useful before
            :meth:`to_dict` / :meth:`to_json`, which walk ``__dict__``
            and therefore reflect instance assignment order.

        Returns:
            bool: True if ordering is correct.

        Raises:
            OdmlibElementOrderError: If any element has children out of
                order. Use :meth:`reorder_object` to fix automatically.
        """
        obj_list = [key for key in list(self.__dict__.keys()) if key != "_content" and key not in self._attrs]
        elem_list = [elem for elem in self._elems if elem in obj_list]
        if obj_list != elem_list:
            raise OdmlibElementOrderError(
                f"The order of elements in {self.__class__.__name__} should be "
                f"{', '.join(key for key in self._elems.keys())}",
                element_type=self.__class__.__name__,
                hint="Use reorder_object() to fix element ordering automatically",
            )
        for attr, obj in self.__dict__.items():
            if isinstance(obj, ODMElement):
                obj.verify_order()
            elif isinstance(obj, list):
                for o in obj:
                    o.verify_order()
        return True

    def reorder_object(self) -> None:
        """Reorder this element's children to match model declaration order.

        Modifies ``__dict__`` in-place. Issues an :class:`OdmlibWarning`
        to indicate that reordering was needed.

        Note:
            Recursion is not automatic — call on each element that needs
            reordering, or call :meth:`verify_order` first to identify
            which elements need reordering.
        """
        warnings.warn(
            f"{self.__class__.__name__} elements are being reordered to match the ODM specification. "
            "Use verify_order() before reorder_object() to understand the ordering issue.",
            OdmlibWarning,
            stacklevel=2,
        )
        ordered_obj = OrderedDict()
        for model_elem_name, model_elem_obj in self._elems.items():
            if model_elem_name in self.__dict__:
                obj = self.__dict__.pop(model_elem_name)
                ordered_obj[model_elem_name] = obj
        for name, elem in ordered_obj.items():
            self.__dict__[name] = elem

    def validate(self, collect_errors=False, oid_checker=None, conformance_checker=None):
        """Validate this element and all children.

        Args:
            collect_errors: If True, accumulate all errors and return them as a
                list instead of raising on the first failure. Defaults to False
                (fail-fast, existing behaviour).
            oid_checker: Optional OIDRef instance for OID validation.
            conformance_checker: Optional MetadataSchema instance for
                conformance validation.

        Returns:
            If ``collect_errors=False``: ``True`` (or raises on first error).
            If ``collect_errors=True``: list of :class:`~odmlib.exceptions.OdmlibError`
            instances (empty list means valid).
        """
        if not collect_errors:
            # Fail-fast — preserves existing behaviour exactly
            self.verify_order()
            if oid_checker:
                self.verify_oids(oid_checker)
            if conformance_checker:
                self.verify_conformance(conformance_checker)
            return True

        collector = ErrorCollector()

        try:
            self.verify_order()
        except OdmlibError as e:
            collector.add_error(e)

        if oid_checker:
            try:
                self.verify_oids(oid_checker)
            except OdmlibError as e:
                collector.add_error(e)

        if conformance_checker:
            try:
                self.verify_conformance(conformance_checker)
            except OdmlibError as e:
                collector.add_error(e)

        return collector.errors

