from unittest import TestCase
import odmlib.ns_registry as NS
import odmlib.odm_1_3_2.model as ODM
import xml.etree.ElementTree as ET
import odmlib.define_loader as DL
import odmlib.loader as LD
import os


class TestNamespaceRegistry(TestCase):
    def setUp(self) -> None:
        NS.NamespaceRegistry(prefix="odm", uri="http://www.cdisc.org/ns/odm/v1.3", is_default=True, is_reset=True)
        NS.NamespaceRegistry(prefix="xs", uri="http://www.w3.org/2001/XMLSchema-instance")
        NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")
        NS.NamespaceRegistry(prefix="xlink", uri="http://www.w3.org/1999/xlink")

    def test_update_registry(self):
        nsr = NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3', 'def': 'http://www.cdisc.org/ns/def/v2.0'})
        self.assertDictEqual(expected_ns, nsr.namespaces)
        nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3', 'def': 'http://www.cdisc.org/ns/def/v2.0',
                            'nciodm': 'http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC'})
        self.assertDictEqual(expected_ns, nsr.namespaces)

    def test_use_existing_registry(self):
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3'})
        nsr = NS.NamespaceRegistry()
        self.assertDictEqual(expected_ns, nsr.namespaces)

    def test_remove_registry_entry(self):
        # tests a singleton so each test builds on the previous one
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3',
                            'def': 'http://www.cdisc.org/ns/def/v2.0',
                            'nciodm': 'http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC'})
        self.assertDictEqual(expected_ns, nsr.namespaces)
        nsr.remove_registry_entry("def")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3',
                            'nciodm': 'http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC'})
        self.assertDictEqual(expected_ns, nsr.namespaces)

    def test_default_ns(self):
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3', 'def': 'http://www.cdisc.org/ns/def/v2.0',
                            'nciodm': 'http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC'})
        self.assertDictEqual(expected_ns, nsr.namespaces)
        self.assertDictEqual({'odm': 'http://www.cdisc.org/ns/odm/v1.3'}, nsr.default_namespace)

    def test_odm_ns_entries(self):
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        nsr = NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3', 'def': 'http://www.cdisc.org/ns/def/v2.0',
                            'nciodm': 'http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC'})
        self.assertDictEqual(expected_ns, nsr.namespaces)
        odm_ns = nsr.get_odm_namespace_entries()
        expected_list = ['xmlns=http://www.cdisc.org/ns/odm/v1.3',
                         'xmlns:xs=http://www.w3.org/2001/XMLSchema-instance',
                         'xmlns:xml=http://www.w3.org/XML/1998/namespace',
                         'xmlns:xlink=http://www.w3.org/1999/xlink',
                         'xmlns:def=http://www.cdisc.org/ns/def/v2.0',
                         'xmlns:nciodm=http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC']
        self.assertListEqual(expected_list, odm_ns)

    def test_prefix_without_url(self):
        expected_ns = self.get_ns_defaults()
        expected_ns.update({'odm': 'http://www.cdisc.org/ns/odm/v1.3'})
        nsr = NS.NamespaceRegistry(prefix="def")
        self.assertDictEqual(expected_ns, nsr.namespaces)
        nsr = NS.NamespaceRegistry(uri='http://www.cdisc.org/ns/def/v2.0')
        self.assertDictEqual(expected_ns, nsr.namespaces)

    def test_bad_ns_url(self):
        with self.assertRaises(ValueError):
            nsr = NS.NamespaceRegistry(prefix="def", uri="www.cdisc.org/ns/def/v2.0")

    def test_odm_ns_attributes(self):
        odm_test_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'test_odm_namespace.xml')
        NS.NamespaceRegistry(prefix="def", uri="http://www.cdisc.org/ns/def/v2.0")
        NS.NamespaceRegistry(prefix="nciodm", uri="http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC")
        NS.NamespaceRegistry(prefix="xsi", uri="http://www.w3.org/2001/XMLSchema-instance")
        root = self.add_root()
        odm_xml = root.to_xml()
        nsr = NS.NamespaceRegistry()
        nsr.set_odm_namespace_attributes(odm_xml)
        tree = ET.ElementTree(odm_xml)
        tree.write(odm_test_file, xml_declaration=True, encoding='utf-8', method='xml', short_empty_elements=True)
        self.assertEqual("ODM.MDV.TEST.001", root.FileOID)
        loader = LD.ODMLoader(DL.XMLDefineLoader())
        odm_root = loader.open_odm_document(odm_test_file)
        self.assertEqual("ODM.MDV.TEST.001", odm_root.attrib["FileOID"])
        odm = loader.create_odmlib(odm_root)
        self.assertEqual("ODM.MDV.TEST.001", odm.FileOID)
        nsr2 = NS.NamespaceRegistry()
        namespaces = nsr2.get_odm_namespace_entries()
        expected_ns_list = ['xmlns=http://www.cdisc.org/ns/odm/v1.3',
                            'xmlns:xs=http://www.w3.org/2001/XMLSchema-instance',
                            'xmlns:xml=http://www.w3.org/XML/1998/namespace',
                            'xmlns:xlink=http://www.w3.org/1999/xlink',
                            'xmlns:def=http://www.cdisc.org/ns/def/v2.0',
                            'xmlns:nciodm=http://ncicb.nci.nih.gov/xml/odm/EVS/CDISC',
                            'xmlns:xsi=http://www.w3.org/2001/XMLSchema-instance']
        self.assertListEqual(namespaces, expected_ns_list)




    def add_root(self):
        attrs = self.get_root_attributes()
        root = ODM.ODM(**attrs)
        return root

    def get_root_attributes(self):
        attrs = {"FileOID": "ODM.MDV.TEST.001", "AsOfDateTime": "2020-07-13T00:13:51.309617+00:00",
                 "CreationDateTime": "2020-07-13T00:13:51.309617+00:00", "ODMVersion": "1.3.2", "FileType": "Snapshot",
                 "Originator": "RDS", "SourceSystem": "ODMLib", "SourceSystemVersion": "0.1"}
        return attrs

    def get_ns_defaults(self):
        return {
            'xs': 'http://www.w3.org/2001/XMLSchema-instance',
            'xml': 'http://www.w3.org/XML/1998/namespace',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
