import odmlib.descriptor as DESC
import odmlib.typed as T
import odmlib.ns_registry as NS
from collections import OrderedDict
import json
import xml.etree.ElementTree as ET


class ODMMeta(type):
    @classmethod
    def __prepare__(cls, name, bases):
        """ preserves the order of declarations in each class """
        return OrderedDict()

    def __new__(cls, clsname, bases, clsdict):
        # variables created in classes become the class attributes
        fields = [key for key, val in clsdict.items() if isinstance(val, (DESC.Descriptor, ODMMeta))]

        for name in fields:
            clsdict[name].name = name

        clsdict["_fields"] = fields
        # the default class namespace is odm
        if "namespace" not in clsdict:
            clsdict["namespace"] = "odm"
        # add attribute non-default namespaces
        ns = {key: val.namespace for key, val in clsdict.items() if isinstance(val, (DESC.Descriptor, ODMMeta))
              if val.namespace != "odm"}
        clsdict["_attr_ns"] = ns

        clsobj = super().__new__(cls, clsname, bases, dict(clsdict))
        return clsobj


class ODMWriter:

    @staticmethod
    def write_odm(odm_file, odm_elem):
        """
        after converting ODMLIB to ElementTree, write the ElementTree to an ODM file
        :param odm_file: path and file to write the ODM XML
        :param odm_elem: Element object to write to ODM (presumably an ODM root)
        """
        tree = ET.ElementTree(odm_elem)
        root = tree.getroot()
        # workaround for elementtree NS bug - NamespaceRegistry assumes at least 1 default NS has been set
        nsr = NS.NamespaceRegistry()
        nsr.set_odm_namespace_attributes(root)
        tree.write(odm_file, xml_declaration=True, encoding='utf-8', method='xml', short_empty_elements=True)


class ODMElement(metaclass=ODMMeta):
    def __init__(self, **kwargs):
        """
        abstract ODM element class used to set the properties of any ODM object
        """
        for name, val in kwargs.items():
            if name not in self.__class__.__dict__.keys():
                # strip out non-default elementtree namespaces from the XML to work with just the name e.g. xml:lang
                if "}" in name:
                    name = name[name.find('}') + 1:]
                else:
                    raise TypeError(f"Unknown keyword argument {name} in {self.__class__.__name__}")
            setattr(self, name, val)
        for attr, obj in self.__class__.__dict__.items():
            if isinstance(obj, DESC.Descriptor) and (not isinstance(obj, T.ODMObject)) and (attr not in self.__dict__) and obj.required:
                raise ValueError(f"Missing required keyword argument {attr} in {self.__class__.__name__}")

    def __setattr__(self, key, value):
        """ ensure the object being added is a type that belongs to the class """
        if not hasattr(self, key):
            raise TypeError(f"Assignment error: {self.__class__.__name__} does not have a defined attribute {key}")
        super().__setattr__(key, value)

    def to_json(self):
        """
        transforms odmlib hierarchy into a dict and converts that to JSON and returns it

        :return: JSON representation of odmlib hierarchy
        """
        return json.dumps(self.to_dict())

    def to_xml(self, parent_elem=None, top_elem=None):
        """
        generates ElementTree XML from the odmlib object hierarchy

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
        for name, obj in self.__dict__.items():
            # process each element in a list of ELEMENTS
            if isinstance(obj, list) and obj:
                for o in obj:
                    o.to_xml(odm_elem, top_elem)
            elif isinstance(obj, ODMElement):
                obj.to_xml(odm_elem, top_elem)
        return top_elem

    def to_dict(self):
        """
        transform odmlib object hierarchy into a Python dictionary and return it

        :return: dictionary serialization of odmlib hierarchy
        """
        # Note: namespaces used in the XML serialization are not part of the dictionary or json serializations
        property_dict = {}
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                property_dict[attr] = obj.to_dict()                    # element
            elif isinstance(obj, list):
                property_dict[attr] = [o.to_dict() for o in obj]       # list of ELEMENTS
            elif obj is not None:
                property_dict[attr] = obj                              # attributes
        return property_dict

    def __repr__(self):
        args = ", ".join(name for name in self._fields)
        return type(self).__name__ + "(" + args + ")"

    def __str__(self):
        if "_content" in self._fields and self._content:
            return self._content
        elif "OID" in self._fields and self.OID:
            return type(self).__name__ + "(OID=" + self.OID + ")"
        else:
            args = ", ".join(name for name in self._fields)
            return type(self).__name__ + "(" + args + ")"

    def find(self, obj_name, attr, val):
        """
        return an odmlib object for object type obj_name where the attribute attr value equals val

        :param obj_name: text name of the ODM Element (case sensitive)
        :param attr: text name of the ODM Element Attribute (case sensitive)
        :param val: attribute value to search for
        :return: an odmlib object of the ODM element with the first time the attribute value matches val
        """
        obj_list = eval("self." + obj_name)
        for o in obj_list:
            if o.__dict__[attr] == val:
                return o
        return None

    def write_xml(self, odm_file, odm_writer=ODMWriter):
        """
        write the odmlib hierarchy as an XML file

        :param odm_file: string ODM filename and path
        :param odm_writer: object used to write the elementree XML to a file
        """
        odm_elem = self.to_xml()
        odm_writer = odm_writer()
        odm_writer.write_odm(odm_file, odm_elem)

    def write_json(self, odm_file):
        """
        write the odmlib hierarchy as a JSON file

        :param odm_file: string ODM filename and path
        """
        with open(odm_file, 'w') as outfile:
            json.dump(self.to_dict(), outfile)

    def verify_oids(self, oid_checker):
        """
        checks all the OIDs for uniqueness and Def/Ref integrity; oid_checker throws a ValueError on failure

        :param oid_checker: object that performs that checks OID uniqueness and Def/Ref checks
        """
        self._init_oid_check(oid_checker)
        oid_checker.check_oid_refs()

    def _init_oid_check(self, oid_checker):
        """
        for odmlib object, loads all OIDs and checks them for uniqueness; throws an error if uniqueness check fails

        :param oid_checker: object used to check OIDs for uniqueness and Def/Ref check
        """
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                obj._init_oid_check(oid_checker)                    # element
            elif isinstance(obj, list):
                for o in obj:
                    o._init_oid_check(oid_checker)                  # list of ELEMENTS
            else:
                if attr == "OID":
                    oid_checker.add_oid(obj, self.__class__.__name__)
                elif "OID" in attr:
                    oid_checker.add_oid_ref(obj, attr)
        return

    def verify_conformance(self, validator):
        """
        uses validator object to check object for conformance with the model

        :param validator: object that validates the odmlib object against the model
        """
        doc_dict = self.to_dict()
        result = validator.verify_conformance(doc_dict, type(self).__name__)
        return result

    def verify_order(self):
        # TODO attempt to fix order to match _fields by sorting?
        odm_content = {attr: obj for attr, obj in self.__dict__.items() if attr not in ["_fields", "_attr_ns"]}
        for attr, obj in odm_content.items():
            if isinstance(obj, ODMElement):
                if list(obj.__dict__.keys()) != obj._fields:
                    raise ValueError(f"The order of elements in {attr} should be {obj._fields}")
                obj.verify_order()
            elif isinstance(obj, list):
                for o in obj:
                    if list(obj.__dict__.keys()) != obj._fields:
                        raise ValueError(f"The order of elements in {attr} should be {obj._fields}")
                    o.verify_order()
        return True

