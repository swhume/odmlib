"""Helpers for the JSON round-trip harness in ``tests/test_json_roundtrip.py`` (P3).

A :class:`Fixture` names an XML document and the model and loaders that read it. The
leg functions load and re-serialize it, and :func:`canonical_xml` reduces two XML
documents to a form that may be compared as strings.

The normalizer is the **complete** list of differences the harness forgives. Anything
else is a failure, and the fix belongs in the library:

* **N1** -- parse with ElementTree, which drops comments and document-level processing
  instructions; odmlib models neither (the ``<?xml-stylesheet?>`` in
  ``defineV21-SDTM.xml``, for example).
* **N2** -- drop whitespace-only tails, and the whitespace-only text of an element that
  has element children: indentation. Never touch anything inside XHTML. Leaf text is
  compared exactly. Also drop the whitespace-only text of an element whose class models
  no text (``_content``), the rule the loaders themselves apply
  (``document_loader.element_content``). Such an element's content is element-only, so
  the whitespace is indentation even when it has no children:
  ``<ItemData ...>\n  </ItemData>``, or one whose only child was a comment.
* **N3** -- ``ET.canonicalize(..., rewrite_prefixes=True)``, so prefixes compare by URI
  (``xsi:`` versus ``xs:`` on ``schemaLocation``) and attribute order does not matter.
* **N4** -- leg B only: stable-sort each run of interleaved-group members into model
  order. The spec's JSON has one array per type, so it cannot carry the interleaving.
* **N5** -- compare attributes whose descriptor is a ``T.Integer`` or ``T.Float``
  subclass by ``Decimal`` value, so ``Rank="1"`` written back as ``1.0`` matches.

One named exception sits outside the normalizer: :data:`KNOWN_REORDERINGS` lists the
documents whose XSD-valid child order odmlib does not preserve, and the exact reordering
it applies. The harness applies that reordering to the *expected* side only, and fails if
the source document stops needing it.
"""
from __future__ import annotations

import contextlib
import importlib
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import odmlib.arm_loader as AL
import odmlib.define_loader as DL
import odmlib.loader as LD
import odmlib.mode as mode
import odmlib.ns_registry as NS
import odmlib.odm_loader as OL
import odmlib.typed as T

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
ODM_V2_DIR = os.path.join(DATA_DIR, "odm_v2")
XHTML_NS = "http://www.w3.org/1999/xhtml"
CONFTEST_DEFAULT = ("odm", "http://www.cdisc.org/ns/odm/v1.3")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Fixture:
    """An XML document, and the model and loaders that read it.

    ``kind`` picks the loader pair: ``"odm"`` (XMLODMLoader / JSONODMLoader),
    ``"define"`` (XMLDefineLoader / JSONDefineLoader) or ``"arm"``
    (XMLArmLoader / JSONArmLoader). ``root`` is the root element's name, and
    ``vendored_json`` the companion JSON from ``tests/data/odm_v2`` (leg E).

    ``permissive`` loads the document under ``odmlib.mode.permissive()``. It is for a
    fixture that is deliberately not schema-valid, and ``permissive_reason`` must say
    why. Values a strict load would reject are then stored as found, and the legs prove
    they survive both round trips unchanged.
    """
    name: str
    path: str
    model_package: str
    kind: str = "odm"
    root: str = "ODM"
    vendored_json: Optional[str] = None
    permissive: bool = False
    permissive_reason: str = ""

    def __post_init__(self):
        if self.permissive and not self.permissive_reason:
            raise ValueError(f"{self.name}: a permissive fixture must give permissive_reason")

    def loading(self):
        """The context to load in: permissive for a permissive fixture, else strict."""
        return mode.permissive() if self.permissive else contextlib.nullcontext()

    @property
    def model(self) -> Any:
        return importlib.import_module(f"odmlib.{self.model_package}.model")

    def xml_loader(self) -> LD.ODMLoader:
        if self.kind == "define":
            return LD.ODMLoader(DL.XMLDefineLoader(model_package=self.model_package))
        if self.kind == "arm":
            return LD.ODMLoader(AL.XMLArmLoader(model_package=self.model_package))
        return LD.ODMLoader(OL.XMLODMLoader(model_package=self.model_package))

    def json_loader(self) -> LD.ODMLoader:
        if self.kind == "define":
            return LD.ODMLoader(DL.JSONDefineLoader(model_package=self.model_package))
        if self.kind == "arm":
            return LD.ODMLoader(AL.JSONArmLoader(model_package=self.model_package))
        return LD.ODMLoader(OL.JSONODMLoader(model_package=self.model_package))


def _data(name: str) -> str:
    return os.path.join(DATA_DIR, name)


#: The fixtures every leg runs over, apart from the vendored ODM v2.0 documents, which
#: :func:`all_fixtures` adds from their manifest.
CORE_FIXTURES = (
    # ODM 1.3.2: metadata, clinical data, reference data
    Fixture("odm_1_3_2/cdash-odm-test", _data("cdash-odm-test.xml"), "odm_1_3_2"),
    Fixture("odm_1_3_2/test_clinical_data_01", _data("test_clinical_data_01.xml"), "odm_1_3_2"),
    Fixture("odm_1_3_2/odm-data-snapshot", _data("odm-data-snapshot.xml"), "odm_1_3_2"),
    Fixture("odm_1_3_2/test_referece_data_01", _data("test_referece_data_01.xml"), "odm_1_3_2"),
    # Define-XML 2.0 and 2.1
    Fixture("define_2_0/define2-0-0-sdtm-test", _data("define2-0-0-sdtm-test.xml"),
            "define_2_0", kind="define"),
    Fixture("define_2_1/defineV21-SDTM", _data("defineV21-SDTM.xml"), "define_2_1", kind="define"),
    Fixture("define_2_1/defineV21-SEND-class", _data("defineV21-SEND-class.xml"),
            "define_2_1", kind="define"),
    Fixture("define_2_1/define-360i", _data("define-360i.xml"), "define_2_1", kind="define",
            permissive=True,
            permissive_reason="a template: 615 attributes hold __PLACEHOLDER__, which no "
                              "strict load accepts (KeySequence, Length, ...)"),
    # ARM 1.0 over Define-XML 2.1 (the ADaM example carries analysis results)
    Fixture("arm_1_0/definev21-adam", _data("definev21-adam.xml"), "arm_1_0", kind="arm"),
    # CT-XML 1.1.1 (hand-written: no CDISC CT file is small enough to vendor)
    Fixture("ct_1_1_1/ct-1-1-1-sample", _data("ct-1-1-1-sample.xml"), "ct_1_1_1"),
    # ODM 2.0
    Fixture("odm_2_0/odmv2_example", _data("odmv2_example.xml"), "odm_2_0"),
    Fixture("odm_2_0/cdash_demo_v20", _data("cdash_demo_v20.xml"), "odm_2_0"),
)


def vendored_fixtures(clinical_data=None):
    """The vendored ODM v2.0 documents, from ``tests/data/odm_v2/MANIFEST.json``.

    ``clinical_data`` selects those with (True) or without (False) ClinicalData;
    the default, None, selects all of them.
    """
    with open(os.path.join(ODM_V2_DIR, "MANIFEST.json"), encoding="utf-8") as handle:
        manifest = json.load(handle)
    fixtures = []
    for entry in manifest["fixtures"]:
        if clinical_data is not None and entry["has_clinical_data"] != clinical_data:
            continue
        xml = next(f["path"] for f in entry["files"] if f["path"].endswith(".xml"))
        js = next(f["path"] for f in entry["files"] if f["path"].endswith(".json"))
        fixtures.append(Fixture(
            name=f"odm_v2/{xml}", path=os.path.join(ODM_V2_DIR, xml), model_package="odm_2_0",
            root=entry["root"], vendored_json=os.path.join(ODM_V2_DIR, js)))
    return fixtures


def all_fixtures():
    """Every fixture the legs run over: the core set plus every vendored ODM v2.0 document.

    The vendored ClinicalData documents joined in P4, when odmlib modelled ClinicalData.
    """
    return CORE_FIXTURES + tuple(vendored_fixtures())


#: Documents whose child order is XSD-valid but which odmlib writes in model order, with
#: the reordering odmlib applies: ``(parent, child that moves, child it moves after)``.
#: The ODM 1.3.2 foundation repeats Define-XML's ItemDef extension group without bound,
#: so ``def:ValueListRef`` may precede ``def:Origin``; odmlib writes ``Origin`` first, as
#: the Define-XML 2.1 examples do. Preserving the order would need the interleave
#: mechanism extended to single-valued members (a possible later change).
KNOWN_REORDERINGS = {
    "define_2_1/define-360i": (("ItemDef", "ValueListRef", "Origin"),),
}


def apply_reorderings(root: ET.Element, reorderings) -> int:
    """Move each listed child after the last listed sibling; return how many moved.

    For ``(parent, mover, anchor)``, every ``mover`` child of a ``parent`` element that
    precedes its last ``anchor`` child is moved to just after that anchor.
    """
    moved = 0
    for parent, mover, anchor in reorderings:
        for element in root.iter():
            if not isinstance(element.tag, str) or _local(element.tag) != parent:
                continue
            children = list(element)
            anchors = [c for c in children if isinstance(c.tag, str) and _local(c.tag) == anchor]
            if not anchors:
                continue
            last = children.index(anchors[-1])
            movers = [c for c in children[:last]
                      if isinstance(c.tag, str) and _local(c.tag) == mover]
            for child in movers:
                element.remove(child)
            position = list(element).index(anchors[-1]) + 1
            for offset, child in enumerate(movers):
                element.insert(position + offset, child)
            moved += len(movers)
    return moved


# ---------------------------------------------------------------------------
# Loading and writing
# ---------------------------------------------------------------------------

def reset_registry() -> None:
    """Reset the namespace registry to the conftest default (ODM 1.3 only).

    Every leg starts here, so a leg cannot pass on namespaces an earlier load left
    behind -- the JSON-loader bug fixed in P2.5 hid behind exactly that.
    """
    NS.NamespaceRegistry(prefix=CONFTEST_DEFAULT[0], uri=CONFTEST_DEFAULT[1],
                         is_default=True, is_reset=True)


def load_xml(fixture: Fixture) -> Any:
    """Load the fixture's XML document strictly and return its root object."""
    reset_registry()
    loader = fixture.xml_loader()
    with fixture.loading():
        element = loader.open_odm_document(fixture.path)
        return loader.create_odmlib(element)


def load_json_file(fixture: Fixture, path: str) -> Any:
    """Load a JSON document for *fixture* from *path* and return its root object."""
    reset_registry()
    loader = fixture.json_loader()
    with fixture.loading():
        document = loader.open_odm_document(path)
        if fixture.root != "ODM" and list(document) == [fixture.root]:
            document = document[fixture.root]      # the vendored {"<root>": {...}} wrapper
        return loader.create_odmlib(document, fixture.root)


def json_document(path: str, root: str) -> dict:
    """Read a JSON file as a dict, unwrapping a ``{"<root>": {...}}`` wrapper."""
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    if root != "ODM" and list(document) == [root]:
        document = document[root]
    return document


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def _model_class(model: Any, element: ET.Element) -> Any:
    if not isinstance(element.tag, str) or _namespace(element.tag) == XHTML_NS:
        return None
    return getattr(model, _local(element.tag), None)


def _numeric_value(text: str) -> Optional[str]:
    """``text`` as a canonical decimal string, or None if it is not a number."""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    return format(value.normalize(), "f")


def _sort_group_runs(element: ET.Element, cls: Any) -> None:
    """N4: stable-sort each run of interleaved-group members into model order."""
    group_of = getattr(cls, "_group_of", {})
    if not group_of:
        return
    children = list(element)
    result, i = [], 0
    while i < len(children):
        group = group_of.get(_local(children[i].tag)) if isinstance(children[i].tag, str) else None
        if group is None:
            result.append(children[i])
            i += 1
            continue
        run = []
        while i < len(children) and isinstance(children[i].tag, str) \
                and group_of.get(_local(children[i].tag)) == group:
            run.append(children[i])
            i += 1
        order = cls._groups[group]
        result.extend(sorted(run, key=lambda child: order.index(_local(child.tag))))
    element[:] = result


def normalize(element: ET.Element, model: Any, *, sort_groups: bool = False) -> None:
    """Apply N2, N4 (when *sort_groups*) and N5 to *element* and its subtree, in place."""
    if not isinstance(element.tag, str) or _namespace(element.tag) == XHTML_NS:
        return                                      # never touch XHTML
    cls = _model_class(model, element)
    if element.text is not None and element.text.isspace() and (
            len(element) or (cls is not None and "_content" not in cls._fields)):
        element.text = None                         # N2: indentation, not text
    for child in element:
        if child.tail is not None and child.tail.isspace() \
                and not (isinstance(child.tag, str) and _namespace(child.tag) == XHTML_NS):
            child.tail = None                       # N2: indentation after a child
    if cls is not None:
        for key, value in list(element.attrib.items()):
            descriptor = cls._attrs.get(_local(key))
            if isinstance(descriptor, (T.Integer, T.Float)):
                number = _numeric_value(value)
                if number is not None:
                    element.attrib[key] = number    # N5
        if sort_groups:
            _sort_group_runs(element, cls)          # N4
    for child in element:
        normalize(child, model, sort_groups=sort_groups)


def parse(source: Any) -> ET.Element:
    """Parse a path, or a string of XML, with ElementTree (N1)."""
    if isinstance(source, str) and source.lstrip().startswith("<"):
        return ET.fromstring(source.encode("utf-8"))
    return ET.parse(source).getroot()


def canonical_xml(source: Any, model: Any, *, sort_groups: bool = False,
                  reorderings=()) -> str:
    """Return the canonical form of an XML document (a path, or a string of XML).

    N1 comes from parsing with ElementTree, N3 from ``ET.canonicalize``.
    *reorderings* (from :data:`KNOWN_REORDERINGS`) is applied before normalizing.
    """
    root = parse(source)
    apply_reorderings(root, reorderings)
    normalize(root, model, sort_groups=sort_groups)
    return ET.canonicalize(ET.tostring(root, encoding="unicode"), rewrite_prefixes=True)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def first_xml_difference(expected: str, actual: str, context: int = 160) -> str:
    """Describe where two canonical XML strings first differ."""
    if expected == actual:
        return ""
    i = next((n for n, (a, b) in enumerate(zip(expected, actual)) if a != b),
             min(len(expected), len(actual)))
    start = max(0, i - context // 2)
    return (f"first difference at offset {i}:\n"
            f"  expected ...{expected[start:i + context // 2]!r}\n"
            f"  actual   ...{actual[start:i + context // 2]!r}")


def dict_differences(expected: Any, actual: Any, path: str = "$", limit: int = 10) -> list:
    """List up to *limit* paths where two JSON-like values differ."""
    found: list = []

    def walk(a, b, p):
        if len(found) >= limit:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b), key=str):
                if key not in b:
                    found.append(f"{p}.{key}: missing from actual (expected {_short(a[key])})")
                elif key not in a:
                    found.append(f"{p}.{key}: unexpected in actual ({_short(b[key])})")
                else:
                    walk(a[key], b[key], f"{p}.{key}")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                found.append(f"{p}: {len(a)} items expected, {len(b)} actual")
            for n, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{p}[{n}]")
        elif a != b:
            found.append(f"{p}: expected {_short(a)}, actual {_short(b)}")

    walk(expected, actual, path)
    return found


def _short(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else repr(value)
    return text if len(text) <= 80 else text[:77] + "..."


# ---------------------------------------------------------------------------
# The legs
# ---------------------------------------------------------------------------

def _expected_xml(fixture: Fixture, *, sort_groups: bool) -> str:
    return canonical_xml(fixture.path, fixture.model, sort_groups=sort_groups,
                         reorderings=KNOWN_REORDERINGS.get(fixture.name, ()))


def _write_json(obj: Any, folder: str, fixture: Fixture) -> str:
    path = os.path.join(folder, fixture.name.replace("/", "__") + ".json")
    obj.write_json(path)
    return path


def leg_a(fixture: Fixture):
    """XML -> obj -> XML. Returns (expected, actual) canonical XML; no reordering."""
    actual = load_xml(fixture).to_xml_string()
    return (_expected_xml(fixture, sort_groups=False),
            canonical_xml(actual, fixture.model))


def leg_b(fixture: Fixture, folder: str):
    """XML -> obj -> JSON file -> JSON loader -> obj -> XML, compared after N4."""
    path = _write_json(load_xml(fixture), folder, fixture)
    actual = load_json_file(fixture, path).to_xml_string()
    return (_expected_xml(fixture, sort_groups=True),
            canonical_xml(actual, fixture.model, sort_groups=True))


def json_source(fixture: Fixture, folder: str) -> str:
    """The JSON leg C starts from: the vendored file, or odmlib's own JSON of the XML."""
    if fixture.vendored_json:
        return fixture.vendored_json
    return _write_json(load_xml(fixture), folder, fixture)


def leg_c(fixture: Fixture, folder: str):
    """JSON -> obj -> JSON. Returns (input dict, output dict); no normalization."""
    path = json_source(fixture, folder)
    output = json.loads(load_json_file(fixture, path).to_json())
    return json_document(path, fixture.root), output


def leg_d(fixture: Fixture, folder: str):
    """The XML-loaded and the JSON-loaded trees. Returns their ``to_dict()``."""
    from_xml = load_xml(fixture)
    path = _write_json(from_xml, folder, fixture)
    return from_xml.to_dict(), load_json_file(fixture, path).to_dict()


def leg_e(fixture: Fixture):
    """``to_dict()`` of the XML-loaded tree versus the vendored JSON."""
    return (json_document(fixture.vendored_json, fixture.root),
            json.loads(load_xml(fixture).to_json()))
