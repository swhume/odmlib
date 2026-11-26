"""ODMMeta: the T.SELF self-reference sentinel and the bare-descriptor-class guard (P2.1).

A recursive element (ODM 2.0 ``ItemGroupData`` holds ``ItemGroupData``) cannot name
its own class in its body, and assigning the descriptor after the body registers
nothing. ``element_class=T.SELF`` is resolved to the new class by ``ODMMeta``.

Separately, ``Context = T.String`` (the class, not an instance) used to be accepted
silently and left the field outside ``_attrs``, so values were never validated.
"""
import importlib
import pkgutil
from unittest import TestCase

import odmlib
import odmlib.odm_element as OE
import odmlib.typed as T
from odmlib.exceptions import OdmlibTypeError


class Node(OE.ODMElement):
    """A minimal recursive element."""
    Name = T.String()
    Node = T.ODMListObject(element_class=T.SELF)


class Other(OE.ODMElement):
    Name = T.String()


class TestSelfReference(TestCase):

    def test_self_reference_resolves(self):
        descriptor = Node._elems["Node"]
        self.assertIs(descriptor.element_class, Node)
        self.assertIs(descriptor.obj_type, Node)
        self.assertEqual(Node._fields, ["Name", "Node"])

    def test_nested_children_serialize(self):
        root = Node(Name="a", Node=[Node(Name="b", Node=[Node(Name="c")])])
        xml = root.to_xml_string()
        self.assertEqual(xml.count("<Node"), 3)
        self.assertEqual(root.to_dict()["Node"][0]["Node"][0]["Name"], "c")

    def test_self_reference_rejects_wrong_type(self):
        with self.assertRaises(OdmlibTypeError):
            Node(Name="a", Node=[Other(Name="x")])

    def test_single_child_self_reference(self):
        class Chain(OE.ODMElement):
            Next = T.ODMObject(element_class=T.SELF)
        self.assertIs(Chain._elems["Next"].element_class, Chain)
        Chain(Next=Chain())
        with self.assertRaises(OdmlibTypeError):
            Chain(Next=Other())

    def test_merge_fields_subclass_keeps_self_reference(self):
        class Extended(Node, merge_fields=True):
            Extra = T.String()
        descriptor = Extended._elems["Node"]
        # still the base's resolved class: a subclass instance is a Node too
        self.assertIs(descriptor.element_class, Node)
        self.assertEqual(Extended._fields, ["Name", "Node", "Extra"])
        Extended(Name="e", Node=[Node(Name="n"), Extended(Name="x")])


class TestBareDescriptorClassGuard(TestCase):

    def test_bare_descriptor_class_rejected(self):
        with self.assertRaises(OdmlibTypeError) as ctx:
            class Broken(OE.ODMElement):
                Context = T.String
        self.assertIn("did you mean Context = T.String()?", str(ctx.exception))
        self.assertEqual(ctx.exception.attribute, "Context")

    def test_all_model_packages_import(self):
        """Every bundled model passes the guard (it runs at class creation)."""
        names = sorted(m.name for m in pkgutil.walk_packages(odmlib.__path__, "odmlib.")
                       if m.name.endswith(".model"))
        self.assertGreaterEqual(len(names), 8)
        for name in names:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_arm_programming_code_context_is_validated(self):
        import odmlib.arm_1_0.model as ARM
        self.assertIn("Context", ARM.ProgrammingCode._attrs)
        self.assertEqual(ARM.ProgrammingCode(Context="SAS version 9.4").Context, "SAS version 9.4")
        with self.assertRaises(OdmlibTypeError):
            ARM.ProgrammingCode(Context=94)


class TestChildNamespaces(TestCase):
    """A child is found by its descriptor's namespace but written in its class's (P3).

    The XML loaders look a child up with the *descriptor's* namespace, and ``to_xml``
    writes it with the child *class's* ``namespace``. When the two disagree, a loaded
    document is written back in the wrong namespace. CT-XML's ``nciodm:CDISCSynonym``,
    ``CDISCDefinition``, ``CDISCSubmissionValue`` and ``PreferredTerm`` were all written
    in the ODM namespace until the round-trip harness caught it.
    """

    def test_every_child_descriptor_matches_its_element_class(self):
        names = sorted(m.name for m in pkgutil.walk_packages(odmlib.__path__, "odmlib.")
                       if m.name.endswith(".model"))
        mismatches = []
        for name in names:
            module = importlib.import_module(name)
            for cls in vars(module).values():
                if not (isinstance(cls, type) and issubclass(cls, OE.ODMElement)
                        and cls.__module__ == name):
                    continue
                for field, descriptor in cls._elems.items():
                    child = descriptor.element_class
                    if isinstance(child, type) and descriptor.namespace != child.namespace:
                        mismatches.append(f"{name}: {cls.__name__}.{field} is found as "
                                          f"{descriptor.namespace}: but {child.__name__} "
                                          f"is written as {child.namespace}:")
        self.assertEqual(mismatches, [])
