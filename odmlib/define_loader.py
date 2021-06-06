import odmlib.document_loader as DL
import odmlib.odm_parser as P
import odmlib.ns_registry as NS
import json
import importlib
import xml.etree.ElementTree as ET


class XMLDefineLoader(DL.DocumentLoader):
    def __init__(self, model_package="define_2_0", ns_uri="http://www.cdisc.org/ns/def/v2.0"):
        self.filename = None
        self.parser = None
        self.DEF = importlib.import_module(f"odmlib.{model_package}.model")
        self.ns_uri = ns_uri
        self.nsr = NS.NamespaceRegistry()

    def load_document(self, elem, *args):
        elem_name = elem.tag[elem.tag.find('}') + 1:]
        if elem.text and not elem.text.isspace():
            attrib = {**elem.attrib, **{"_content": elem.text}}
            odm_obj = eval("self.DEF." + elem_name + "(**" + str(attrib) + ")")
        else:
            odm_obj = eval("self.DEF." + elem_name + "(**" + str(elem.attrib) + ")")
        odm_obj_dict = eval("self.DEF." + elem_name + ".__dict__.items()")
        for k, v in odm_obj_dict:
            if type(v).__name__ == "ODMObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                e = elem.find(v.namespace + ":" + k, namespace)
                if e is not None:
                    odm_child_obj = self.load_document(e)
                    exec("odm_obj." + k + " = odm_child_obj")
            elif type(v).__name__ == "ODMListObject":
                namespace = self.nsr.get_ns_entry_dict(v.namespace)
                for e in elem.findall(v.namespace + ":" + k, namespace):
                    odm_child_obj = self.load_document(e)
                    eval("odm_obj." + k + ".append(odm_child_obj)")
        return odm_obj

    def create_document(self, filename, namespace_registry=None):
        self.filename = filename
        self._set_registry(namespace_registry)
        self.parser = P.ODMParser(self.filename, self.nsr)
        root = self.parser.parse()
        return root

    def create_document_from_string(self, odm_string, namespace_registry=None):
        self._set_registry(namespace_registry)
        self.parser = P.ODMStringParser(odm_string, self.nsr)
        root = self.parser.parse()
        return root

    def _set_registry(self, namespace_registry):
        if namespace_registry:
            self.nsr = namespace_registry
        else:
            NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True)
            self.nsr = NS.NamespaceRegistry(prefix="def", uri=self.ns_uri)

    def load_odm(self):
        root = self.parser.ODM()
        root_odmlib = self.load_document(root)
        return root_odmlib

    def load_metadataversion(self, idx=0):
        mdv = self.parser.MetaDataVersion()
        mdv_odmlib = self.load_document(mdv[idx])
        return mdv_odmlib

    def load_study(self, idx=0):
        study = self.parser.Study()
        study_odmlib = self.load_document(study[idx])
        return study_odmlib


class JSONDefineLoader(DL.DocumentLoader):
    def __init__(self, model_package="define_2_0"):
        self.filename = None
        self.odm_dict = {}
        self.DEF = importlib.import_module(f"odmlib.{model_package}.model")

    def load_document(self, odm_dict, key):
        attrib = {key: value for key, value in odm_dict.items() if not isinstance(value, (list, dict))}
        odm_obj = eval("self.DEF." + key + "(**" + str(attrib) + ")")
        odm_obj_items = eval("self.DEF." + key + ".__dict__.items()")
        for k, v in odm_obj_items:
            if type(v).__name__ == "ODMObject":
                if k in odm_dict:
                    odm_child_obj = self.load_document(odm_dict[k], k)
                    exec("odm_obj." + k + " = odm_child_obj")
            elif type(v).__name__ == "ODMListObject":
                if k in odm_dict:
                    for val in odm_dict[k]:
                        odm_child_obj = self.load_document(val, k)
                        eval("odm_obj." + k + ".append(odm_child_obj)")
        return odm_obj

    def create_document(self, filename):
        self.filename = filename
        with open(self.filename) as json_in:
            self.odm_dict = json.load(json_in)
        return self.odm_dict

    def create_document_from_string(self, odm_string):
        self.odm_dict = json.loads(odm_string)
        return self.odm_dict

    def load_odm(self):
        if not self.odm_dict:
            raise ValueError("create_document must be used to create the document before executing load_odm")
        odm_odmlib = self.load_document(self.odm_dict, "MetaDataVersion")
        return odm_odmlib

    def load_metadataversion(self, idx=0):
        if not self.odm_dict:
            raise ValueError("create_document must be used to create the document before executing load_metadataversion")
        if "MetaDataVersion" in self.odm_dict:
            mdv_dict = self.odm_dict["MetaDataVersion"][idx]
        elif "Study" in self.odm_dict and "MetaDataVersion" in self.odm_dict["Study"][0]:
            mdv_dict = self.odm_dict["Study"][0]["MetaDataVersion"][idx]
        else:
            raise ValueError("MetaDataVersion not found in ODM dictionary")
        mdv_odmlib = self.load_document(mdv_dict, "MetaDataVersion")
        return mdv_odmlib
