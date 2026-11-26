"""Interleaved repeating groups keep their order (crfutils plan §4A, O5).

The ODM 2.0 XSD lets two child types alternate inside ``ItemGroupDef``
(``ItemGroupRef``/``ItemRef``), ``StudyEventGroupDef``
(``StudyEventGroupRef``/``StudyEventRef``) and ``WorkflowDef``
(``Transition``/``Branching``). Before v0.3.0 odmlib stored each type in its own list
and wrote every member of the first list before the second, so a form without
OrderNumbers had its questions reordered on a load/write round trip.

The per-type lists are now views onto one ordered sequence (``odmlib.interleave``).
These tests pin the load and write order, ``children()``, and how every list
operation moves a child within the shared sequence.
"""
import copy
import json
import pickle
import unittest
import xml.etree.ElementTree as ET

import odmlib.loader as LD
import odmlib.ns_registry as NS
import odmlib.odm_2_0.model as ODM2
import odmlib.odm_loader as OL
from odmlib.interleave import GroupMemberList
from odmlib.odm_parser import ODMSchemaValidator

ODM_NS = "http://www.cdisc.org/ns/odm/v2.0"


def _setup_odm2_namespaces():
    NS.NamespaceRegistry(prefix="odm", uri=ODM_NS, is_default=True, is_reset=True)
    NS.NamespaceRegistry(prefix="xml", uri="http://www.w3.org/XML/1998/namespace")


def _load(xml):
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
    loader.load_odm_string(xml)
    return loader.root()


def _document(mdv_body):
    return (f'<ODM xmlns="{ODM_NS}" FileOID="F.1" FileType="Snapshot" '
            f'CreationDateTime="2026-10-16T09:00:00" ODMVersion="2.0">'
            f'<Study OID="ST.1" StudyName="S" ProtocolName="P">'
            f'<MetaDataVersion OID="MDV.1" Name="V1">{mdv_body}</MetaDataVersion></Study></ODM>')


def _item_def(oid):
    return f'<ItemDef OID="{oid}" Name="{oid}" DataType="text"/>'


# Demographics_RACE_check_all_that_apply.xml in DataExchange-ODM: three ItemRefs, then
# a nested group, then another ItemRef -- reloaded group-first by odmlib 0.2.1.
RACE_FORM = (
    '<ItemGroupDef OID="IG.DM" Name="Demographics" Repeating="No" Type="Form">'
    '<ItemRef ItemOID="IT.BRTHDTC" Mandatory="Yes"/>'
    '<ItemRef ItemOID="IT.SEX" Mandatory="Yes"/>'
    '<ItemRef ItemOID="IT.ETHNIC" Mandatory="No"/>'
    '<ItemGroupRef ItemGroupOID="IG.RACE" Mandatory="Yes"/>'
    '<ItemRef ItemOID="IT.COMMENT" Mandatory="No"/>'
    '</ItemGroupDef>'
    '<ItemGroupDef OID="IG.RACE" Name="Race" Repeating="No" Type="Section">'
    '<ItemRef ItemOID="IT.RACE" Mandatory="Yes"/></ItemGroupDef>'
    + "".join(_item_def(oid) for oid in ("IT.BRTHDTC", "IT.SEX", "IT.ETHNIC", "IT.COMMENT",
                                         "IT.RACE"))
)
RACE_ORDER = ["IT.BRTHDTC", "IT.SEX", "IT.ETHNIC", "IG.RACE", "IT.COMMENT"]


def _key(child):
    return getattr(child, "ItemOID", None) or getattr(child, "ItemGroupOID", None) \
        or getattr(child, "StudyEventOID", None) or getattr(child, "StudyEventGroupOID", None) \
        or child.OID


def _order(element, *names):
    return [_key(child) for child in element.children(*names)]


def _written_order(element):
    return [c.get("ItemOID") or c.get("ItemGroupOID") or c.get("StudyEventOID")
            or c.get("StudyEventGroupOID") or c.get("OID")
            for c in ET.fromstring(element.to_xml_string())]


def _ir(oid):
    return ODM2.ItemRef(ItemOID=oid, Mandatory="No")


def _igr(oid):
    return ODM2.ItemGroupRef(ItemGroupOID=oid, Mandatory="No")


def _igd(**kwargs):
    return ODM2.ItemGroupDef(OID="IG.F", Name="F", Repeating="No", Type="Form", **kwargs)


class TestLoadAndWrite(unittest.TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_item_group_def_keeps_document_order(self):
        odm = _load(_document(RACE_FORM))
        form = odm.Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertEqual(_order(form, "ItemRef", "ItemGroupRef"), RACE_ORDER)
        self.assertEqual(_written_order(form), RACE_ORDER)

    def test_per_type_lists_are_unchanged(self):
        form = _load(_document(RACE_FORM)).Study[0].MetaDataVersion[0].ItemGroupDef[0]
        self.assertEqual([r.ItemOID for r in form.ItemRef],
                         ["IT.BRTHDTC", "IT.SEX", "IT.ETHNIC", "IT.COMMENT"])
        self.assertEqual([r.ItemGroupOID for r in form.ItemGroupRef], ["IG.RACE"])
        self.assertIsInstance(form.ItemRef, list)
        self.assertEqual(len(form), 4)                       # ItemGroupDef iterates ItemRefs
        self.assertEqual([r.ItemOID for r in form][0], "IT.BRTHDTC")

    def test_round_trip_is_byte_identical_and_schema_valid(self):
        first = _load(_document(RACE_FORM)).to_xml_string()
        _setup_odm2_namespaces()
        second = _load(first).to_xml_string()
        self.assertEqual(first, second)
        validator = ODMSchemaValidator(standard="odm", version="2.0")
        self.assertTrue(validator.validate_tree(ET.ElementTree(ET.fromstring(first))))

    def test_study_event_group_def_keeps_document_order(self):
        odm = _load(_document(
            '<StudyEventGroupDef OID="SEG.1" Name="Treatment">'
            '<StudyEventRef StudyEventOID="SE.V1" Mandatory="Yes"/>'
            '<StudyEventGroupRef StudyEventGroupOID="SEG.2" Mandatory="No"/>'
            '<StudyEventRef StudyEventOID="SE.V2" Mandatory="Yes"/></StudyEventGroupDef>'))
        segd = odm.Study[0].MetaDataVersion[0].StudyEventGroupDef[0]
        expected = ["SE.V1", "SEG.2", "SE.V2"]
        self.assertEqual(_order(segd, "StudyEventRef", "StudyEventGroupRef"), expected)
        self.assertEqual(_written_order(segd), expected)

    def test_workflow_def_keeps_document_order(self):
        odm = _load(_document(
            '<WorkflowDef OID="WF.1" Name="Flow"><WorkflowStart StartOID="SE.1"/>'
            '<Transition OID="TR.1" Name="T1" SourceOID="SE.1" TargetOID="BR.1"/>'
            '<Branching OID="BR.1" Name="Decide" Type="Exclusive">'
            '<TargetTransition TargetTransitionOID="TR.2"/></Branching>'
            '<Transition OID="TR.2" Name="T2" SourceOID="BR.1" TargetOID="SE.2"/>'
            '<WorkflowEnd EndOID="SE.2"/></WorkflowDef>'))
        workflow = odm.Study[0].MetaDataVersion[0].WorkflowDef[0]
        self.assertEqual(_order(workflow, "Transition", "Branching"), ["TR.1", "BR.1", "TR.2"])
        written = [c.get("OID") or c.tag for c in ET.fromstring(workflow.to_xml_string())]
        self.assertEqual(written, [f"{{{ODM_NS}}}WorkflowStart", "TR.1", "BR.1", "TR.2",
                                   f"{{{ODM_NS}}}WorkflowEnd"])

    def test_verify_order_passes(self):
        _load(_document(RACE_FORM)).verify_order()


class TestChildren(unittest.TestCase):
    def setUp(self):
        _setup_odm2_namespaces()

    def test_children_follows_model_order_around_the_group(self):
        form = _igd(Description=ODM2.Description(TranslatedText=[
            ODM2.TranslatedText(Type="text/plain", _content="d")]))
        form.ItemRef.append(_ir("IT.1"))
        form.ItemGroupRef.append(_igr("IG.1"))
        form.Alias.append(ODM2.Alias(Context="SDTM", Name="DM"))
        self.assertEqual([type(c).__name__ for c in form.children()],
                         ["Description", "ItemRef", "ItemGroupRef", "Alias"])

    def test_children_skips_auto_created_empty_children(self):
        form = _igd()
        form.Description                      # reading an unset child auto-creates it
        self.assertEqual(form.children(), [])

    def test_children_returns_a_new_list(self):
        form = _igd(ItemRef=[_ir("IT.1")])
        form.children().clear()
        self.assertEqual(len(form.ItemRef), 1)

    def test_children_works_on_every_element(self):
        mdv = ODM2.MetaDataVersion(OID="MDV.1", Name="V")
        mdv.ItemDef.append(ODM2.ItemDef(OID="IT.1", Name="A", DataType="text"))
        self.assertEqual([c.OID for c in mdv.children("ItemDef")], ["IT.1"])


class TestEditing(unittest.TestCase):
    """How each list operation moves a child within the shared sequence."""

    def setUp(self):
        _setup_odm2_namespaces()
        self.form = _igd()
        self.form.ItemRef.append(_ir("IT.1"))
        self.form.ItemGroupRef.append(_igr("IG.1"))
        self.form.ItemRef.append(_ir("IT.2"))

    def order(self):
        return _order(self.form, "ItemRef", "ItemGroupRef")

    def assertWritten(self, expected):
        self.assertEqual(self.order(), expected)
        self.assertEqual(_written_order(self.form), expected)

    def test_append_order_is_written(self):
        self.assertWritten(["IT.1", "IG.1", "IT.2"])

    def test_append_after_load_goes_to_the_end(self):
        form = _load(_document(RACE_FORM)).Study[0].MetaDataVersion[0].ItemGroupDef[0]
        form.ItemGroupRef.append(_igr("IG.NEW"))
        self.assertEqual(_order(form, "ItemRef", "ItemGroupRef"), RACE_ORDER + ["IG.NEW"])

    def test_extend_and_iadd(self):
        self.form.ItemRef.extend([_ir("IT.3")])
        self.form.ItemGroupRef += [_igr("IG.2")]
        self.assertWritten(["IT.1", "IG.1", "IT.2", "IT.3", "IG.2"])

    def test_insert_goes_before_the_next_child_of_its_type(self):
        self.form.ItemRef.insert(1, _ir("IT.1b"))
        self.assertWritten(["IT.1", "IG.1", "IT.1b", "IT.2"])
        self.form.ItemRef.insert(0, _ir("IT.0"))
        self.assertWritten(["IT.0", "IT.1", "IG.1", "IT.1b", "IT.2"])

    def test_insert_at_the_end_is_append(self):
        self.form.ItemGroupRef.insert(len(self.form.ItemGroupRef), _igr("IG.2"))
        self.assertWritten(["IT.1", "IG.1", "IT.2", "IG.2"])

    def test_remove_pop_del_clear(self):
        self.form.ItemRef.remove(self.form.ItemRef[0])
        self.assertWritten(["IG.1", "IT.2"])
        self.assertEqual(self.form.ItemGroupRef.pop().ItemGroupOID, "IG.1")
        self.assertWritten(["IT.2"])
        self.form.ItemGroupRef.append(_igr("IG.2"))
        del self.form.ItemRef[0]
        self.assertWritten(["IG.2"])
        self.form.ItemGroupRef.clear()
        self.assertWritten([])

    def test_sort_and_reverse_keep_the_interleaving(self):
        self.form.ItemRef.reverse()
        self.assertWritten(["IT.2", "IG.1", "IT.1"])
        self.form.ItemRef.sort(key=lambda ref: ref.ItemOID)
        self.assertWritten(["IT.1", "IG.1", "IT.2"])

    def test_setitem_replaces_in_place(self):
        self.form.ItemRef[1] = _ir("IT.X")
        self.assertWritten(["IT.1", "IG.1", "IT.X"])
        self.form.ItemRef[0:1] = [_ir("IT.A"), _ir("IT.B")]
        self.assertWritten(["IT.A", "IT.B", "IG.1", "IT.X"])
        del self.form.ItemRef[0:2]
        self.assertWritten(["IG.1", "IT.X"])

    def test_reassigning_a_list_takes_over_its_positions(self):
        old = self.form.ItemRef
        self.form.ItemRef = [_ir("IT.A"), _ir("IT.B"), _ir("IT.C")]
        self.assertWritten(["IT.A", "IG.1", "IT.B", "IT.C"])
        old.append(_ir("IT.STALE"))              # the replaced list is detached
        self.assertWritten(["IT.A", "IG.1", "IT.B", "IT.C"])
        self.assertIsInstance(self.form.ItemRef, GroupMemberList)

    def test_deleting_a_list_drops_its_children(self):
        del self.form.ItemRef
        self.assertWritten(["IG.1"])
        self.form.ItemRef.append(_ir("IT.9"))
        self.assertWritten(["IG.1", "IT.9"])

    def test_constructor_keyword_order(self):
        form = _igd(ItemRef=[_ir("IT.1")], ItemGroupRef=[_igr("IG.1")])
        self.assertEqual(_order(form, "ItemRef", "ItemGroupRef"), ["IT.1", "IG.1"])

    def test_verify_order_accepts_either_type_first(self):
        """Appending an ItemRef before any ItemGroupRef is not a misordering."""
        self.form.verify_order()
        self.assertEqual(self.form.validate(collect_errors=True), [])

    def test_random_edits_keep_each_list_a_subsequence_of_the_order(self):
        """Whatever the edits, each list is its own type's slice of the shared order."""
        import random
        rng = random.Random(20261016)
        lists = {"ItemRef": (self.form.ItemRef, _ir), "ItemGroupRef": (self.form.ItemGroupRef, _igr)}
        counter = 0
        for _ in range(400):
            name = rng.choice(sorted(lists))
            members, make = lists[name]
            counter += 1
            fresh = make(f"X.{counter}")
            operation = rng.choice(["append", "insert", "remove", "pop", "setitem", "slice",
                                    "sort", "reverse", "extend", "delitem"])
            if operation == "append":
                members.append(fresh)
            elif operation == "extend":
                members.extend([fresh, make(f"Y.{counter}")])
            elif operation == "insert":
                members.insert(rng.randint(0, len(members)), fresh)
            elif not members:
                continue
            elif operation == "remove":
                members.remove(rng.choice(members))
            elif operation == "pop":
                members.pop(rng.randrange(len(members)))
            elif operation == "setitem":
                members[rng.randrange(len(members))] = fresh
            elif operation == "slice":
                start = rng.randrange(len(members))
                members[start:start + rng.randint(0, 2)] = [fresh, make(f"Z.{counter}")]
            elif operation == "delitem":
                del members[rng.randrange(len(members))]
            elif operation == "sort":
                members.sort(key=_key)
            else:
                members.reverse()
            order = self.form.children("ItemRef", "ItemGroupRef")
            self.assertEqual(len(order), len(self.form.ItemRef) + len(self.form.ItemGroupRef))
            for list_name, (current, _) in lists.items():
                expected = [c for c in order if type(c).__name__ == list_name]
                self.assertEqual([id(c) for c in expected], [id(c) for c in current],
                                 f"{operation} broke {list_name}")

    def test_rebuilding_an_order(self):
        """Clear both lists and append in the wanted order to reorder across types."""
        wanted = [self.form.ItemGroupRef[0], self.form.ItemRef[1], self.form.ItemRef[0]]
        self.form.ItemRef.clear()
        self.form.ItemGroupRef.clear()
        for child in wanted:
            (self.form.ItemRef if isinstance(child, ODM2.ItemRef)
             else self.form.ItemGroupRef).append(child)
        self.assertWritten(["IG.1", "IT.2", "IT.1"])


class TestCopyingAndSerializing(unittest.TestCase):
    def setUp(self):
        _setup_odm2_namespaces()
        self.form = _load(_document(RACE_FORM)).Study[0].MetaDataVersion[0].ItemGroupDef[0]

    def test_deepcopy_is_independent_and_ordered(self):
        clone = copy.deepcopy(self.form)
        self.assertEqual(_order(clone, "ItemRef", "ItemGroupRef"), RACE_ORDER)
        clone.ItemRef.append(_ir("IT.NEW"))
        self.assertEqual(_order(self.form, "ItemRef", "ItemGroupRef"), RACE_ORDER)
        self.assertEqual(_order(clone, "ItemRef", "ItemGroupRef")[-1], "IT.NEW")

    def test_pickle_round_trip(self):
        clone = pickle.loads(pickle.dumps(self.form))
        self.assertEqual(_order(clone, "ItemRef", "ItemGroupRef"), RACE_ORDER)
        clone.ItemGroupRef.append(_igr("IG.NEW"))
        self.assertEqual(_order(clone, "ItemRef", "ItemGroupRef")[-1], "IG.NEW")

    def test_shallow_copy_of_a_list_is_a_plain_list(self):
        copied = copy.copy(self.form.ItemRef)
        self.assertIs(type(copied), list)
        copied.clear()
        self.assertEqual(len(self.form.ItemRef), 4)

    def test_json_keeps_every_member(self):
        """ODM 2.0 JSON keeps one array per type, so it does not carry the interleaving."""
        data = json.loads(self.form.to_json())
        self.assertEqual([r["ItemOID"] for r in data["ItemRef"]],
                         ["IT.BRTHDTC", "IT.SEX", "IT.ETHNIC", "IT.COMMENT"])
        self.assertEqual([r["ItemGroupOID"] for r in data["ItemGroupRef"]], ["IG.RACE"])

    def test_plain_lists_fall_back_to_model_order(self):
        """Lists written straight into __dict__ are not views; nothing is lost."""
        form = _igd()
        form.__dict__["ItemRef"] = [_ir("IT.1")]
        form.__dict__["ItemGroupRef"] = [_igr("IG.1")]
        self.assertEqual(_order(form, "ItemRef", "ItemGroupRef"), ["IG.1", "IT.1"])
        form.ItemRef.append(_ir("IT.2"))         # still a plain list
        self.assertEqual(_written_order(form), ["IG.1", "IT.1", "IT.2"])


if __name__ == "__main__":
    unittest.main()
