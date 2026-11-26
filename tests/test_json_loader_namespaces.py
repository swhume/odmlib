"""JSON loaders register their model's namespaces (P2.5, defect 1).

JSON carries no namespaces. Before 0.3.0 the JSON loaders registered nothing, so a
document loaded after ``NamespaceRegistry.reset()`` was written with whatever the
registry happened to hold: ODM 2.0 came out as ``xmlns=".../odm/v1.3"`` and
Define-XML 2.1 with ``def:`` undeclared. Each test resets the registry first, so the
bug cannot hide behind an earlier load.
"""
import importlib
import os
import warnings
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.arm_loader as AL
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL

DATA = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
ODM13 = "http://www.cdisc.org/ns/odm/v1.3"
ODM20 = "http://www.cdisc.org/ns/odm/v2.0"
DEF20 = "http://www.cdisc.org/ns/def/v2.0"
DEF21 = "http://www.cdisc.org/ns/def/v2.1"
ARM10 = "http://www.cdisc.org/ns/arm/v1.0"


def _json_of(xml_loader, path):
    loader = LD.ODMLoader(xml_loader)
    loader.open_odm_document(path)
    return loader.root().to_json()


def _reset():
    """A registry holding only the conftest default (ODM 1.3), as after reset()."""
    NS.NamespaceRegistry(prefix="odm", uri=ODM13, is_default=True, is_reset=True)


def _written(json_loader, text):
    """Load *text* with *json_loader* after a reset; return (root Element, warnings)."""
    _reset()
    loader = LD.ODMLoader(json_loader)
    loader.load_odm_string(text)
    odm = loader.root()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        element = ET.fromstring(odm.to_xml_string())
    return element, [str(w.message) for w in caught]


class TestJsonLoadersDeclareTheirNamespaces(TestCase):

    def test_odm_2_0_is_written_in_the_v2_namespace(self):
        text = _json_of(OL.XMLODMLoader(model_package="odm_2_0"),
                        os.path.join(DATA, "odmv2_example.xml"))
        root, caught = _written(OL.JSONODMLoader(model_package="odm_2_0"), text)
        self.assertEqual(root.tag, "{%s}ODM" % ODM20)
        self.assertEqual(caught, [])

    def test_odm_1_3_2_keeps_v1_3(self):
        text = _json_of(OL.XMLODMLoader(model_package="odm_1_3_2"),
                        os.path.join(DATA, "cdash-odm-test.xml"))
        NS.NamespaceRegistry(prefix="odm", uri=ODM20, is_default=True, is_reset=True)
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_1_3_2"))
        loader.load_odm_string(text)
        self.assertEqual(ET.fromstring(loader.root().to_xml_string()).tag, "{%s}ODM" % ODM13)

    def test_define_2_1_declares_def(self):
        text = _json_of(DL.XMLDefineLoader(model_package="define_2_1"),
                        os.path.join(DATA, "defineV21-SDTM.xml"))
        root, caught = _written(DL.JSONDefineLoader(model_package="define_2_1"), text)
        self.assertEqual(caught, [])
        self.assertIsNotNone(root.find(".//{%s}leaf" % DEF21))
        self.assertIsNotNone(root.find(".//{%s}ValueListDef" % DEF21))

    def test_define_2_0_declares_its_own_def(self):
        text = _json_of(DL.XMLDefineLoader(model_package="define_2_0"),
                        os.path.join(DATA, "define2-0-0-sdtm-test.xml"))
        root, caught = _written(DL.JSONDefineLoader(model_package="define_2_0"), text)
        self.assertEqual(caught, [])
        self.assertIsNotNone(root.find(".//{%s}ValueListDef" % DEF20))
        self.assertIsNone(root.find(".//{%s}ValueListDef" % DEF21))

    def test_arm_declares_def_and_arm(self):
        text = _json_of(AL.XMLArmLoader(), os.path.join(DATA, "definev21-adam.xml"))
        root, caught = _written(AL.JSONArmLoader(), text)
        self.assertEqual(caught, [])
        self.assertIsNotNone(root.find(".//{%s}AnalysisResultDisplays" % ARM10))
        self.assertIsNotNone(root.find(".//{%s}leaf" % DEF21))

    def test_json_leg_does_not_depend_on_an_earlier_xml_load(self):
        """The P3 harness resets between legs; a JSON load must stand on its own."""
        text = _json_of(OL.XMLODMLoader(model_package="odm_2_0"),
                        os.path.join(DATA, "odmv2_example.xml"))
        NS.NamespaceRegistry.reset()          # nothing registered at all
        loader = LD.ODMLoader(OL.JSONODMLoader(model_package="odm_2_0"))
        loader.load_odm_string(text)
        self.assertEqual(ET.fromstring(loader.root().to_xml_string()).tag, "{%s}ODM" % ODM20)


class TestRegisterNamespaces(TestCase):
    """Every bundled XML model package exposes a re-runnable register_namespaces()."""

    PACKAGES = ("odm_1_3_2", "odm_2_0", "define_2_0", "define_2_1", "arm_1_0",
                "ct_1_1_1", "dataset_1_0_1")

    def test_registers_auxiliary_prefixes_only(self):
        for name in self.PACKAGES:
            model = importlib.import_module(f"odmlib.{name}.model")
            with self.subTest(model=name):
                NS.NamespaceRegistry.reset()
                model.register_namespaces()
                model.register_namespaces()          # re-runnable
                registry = NS.NamespaceRegistry()
                self.assertEqual(registry.namespaces, model.AUXILIARY_NAMESPACES)
                self.assertEqual(registry.default_namespace, {})   # the loader's job
                self.assertNotIn("odm", model.AUXILIARY_NAMESPACES)

    def test_define_and_arm_extend_their_base(self):
        import odmlib.arm_1_0.model as ARM
        import odmlib.define_2_1.model as DEF
        import odmlib.odm_1_3_2.model as ODM
        self.assertEqual(DEF.AUXILIARY_NAMESPACES, {**ODM.AUXILIARY_NAMESPACES, "def": DEF21})
        self.assertEqual(ARM.AUXILIARY_NAMESPACES, {**DEF.AUXILIARY_NAMESPACES, "arm": ARM10})
