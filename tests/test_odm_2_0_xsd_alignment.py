"""Guard: the ODM 2.0 model's divergence from the bundled XSD must equal an allowlist.

Phase 0 of ``ODM_XSD_ALIGNMENT.md``. Nothing else in the suite compares
``odmlib/odm_2_0/model.py`` to ``odmlib/schemas/odm/2.0/*.xsd``, so every gap
closed in v0.2.1 had to be rediscovered by hand -- build a document, validate it,
fix what the schema rejects. This module does that comparison mechanically and
pins the result.

The assertions check **equality**, not containment, in both directions:

* a divergence that is not in the allowlist fails as *unexpected* -- new drift
  cannot be introduced silently;
* an allowlist entry that no longer occurs fails as *stale* -- a phase that
  fixes a gap must delete its entry, so the allowlist can never overstate what
  is still broken.

Each alignment phase therefore ends by deleting entries here. When every list
is empty except the deliberate waivers, the model matches the schema.

``verify_order()`` cannot do this job. The XML loader fills children by
iterating ``_elems`` and calling ``find``/``findall`` per descriptor
(``odm_loader.py``), never following document order, so a loaded object's
``__dict__`` is always in model order and ``verify_order()`` passes on every
loaded document -- including schema-invalid ones, which odmlib silently
normalizes on re-serialization. Only comparing declaration order against the
XSD sequence catches an ordering bug.

Comparison rules, chosen to avoid noise that no phase would ever "fix":

* ``mixed="true"`` types and ``xs:simpleContent`` extensions contribute
  ``_content``; without this, ``TranslatedText``, ``Title`` and ``Code`` all
  report a phantom extra attribute.
* ``_content`` *requiredness* is not compared. The XSD base type ``text`` is an
  unrestricted string, so an empty element is always schema-valid; whether
  odmlib marks ``_content`` required is a modelling choice, not a conformance
  question. Its presence or absence *is* compared.
* Only children present on both sides are order-compared, so a missing child
  does not also produce a spurious ordering failure.
* ``*ElementExtension`` groups are vendor extension points containing an empty
  ``<xs:sequence/>``; expanding them is a harmless no-op.

A note on value sets, because the two directions are **not** symmetric: a key
with no matching descriptor is inert, unused data. A ``ValueSetString``
descriptor with no key is the loud one -- ``ValueSet.validate`` maps the unknown
sentinel to ``False`` and ``ValidValues.__set__`` then raises for every value,
so the attribute cannot be set at all.

Run ``python tests/test_odm_2_0_xsd_alignment.py`` to print the current
divergences as ready-to-paste literals when updating the allowlists.
"""
import ast
import glob
import json
import os
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.odm_element as OE
import odmlib.odm_2_0.model as ODM2
import odmlib.typed as T

XS = "{http://www.w3.org/2001/XMLSchema}"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(REPO_ROOT, "odmlib", "schemas", "odm", "2.0")
STUB_PATH = os.path.join(REPO_ROOT, "odmlib", "odm_2_0", "model.pyi")
VALUESETS_PATH = os.path.join(REPO_ROOT, "odmlib", "data", "valuesets.json")
TYPE_PREFIX = "ODMcomplexTypeDefinition-"


# ---------------------------------------------------------------------------
# XSD parsing
# ---------------------------------------------------------------------------

def _load_schema():
    """Return (attribute_groups, groups, complex_types, elem->type, simple_types)."""
    attr_groups, groups, ctypes, elem_type, simple = {}, {}, {}, {}, {}
    for path in sorted(glob.glob(os.path.join(SCHEMA_DIR, "*.xsd"))):
        root = ET.parse(path).getroot()
        for node in root.findall(f"{XS}attributeGroup"):
            if node.get("name"):
                attr_groups[node.get("name")] = node
        for node in root.findall(f"{XS}group"):
            if node.get("name"):
                groups[node.get("name")] = node
        for node in root.findall(f"{XS}complexType"):
            if node.get("name"):
                ctypes[node.get("name")] = node
        for node in root.findall(f"{XS}simpleType"):
            if node.get("name"):
                simple[node.get("name")] = node
        for node in root.findall(f"{XS}element"):
            # ODM elements all carry type="ODMcomplexTypeDefinition-<Name>";
            # the bundled xhtml and xlink schemas use inline types and are
            # deliberately skipped.
            if node.get("name") and (node.get("type") or "").startswith(TYPE_PREFIX):
                elem_type[node.get("name")] = node.get("type")
    return attr_groups, groups, ctypes, elem_type, simple


ATTR_GROUPS, GROUPS, CTYPES, ELEM_TYPE, SIMPLE_TYPES = _load_schema()


def _xsd_attributes(node, seen=None):
    """Return [(name, required)] for a complexType, resolving attributeGroup refs."""
    seen = set() if seen is None else seen
    out = []
    for attr in node.findall(f".//{XS}attribute"):
        name = attr.get("name") or (attr.get("ref") or "").split(":")[-1]
        if name:
            out.append((name, attr.get("use") == "required"))
    for ref in node.findall(f".//{XS}attributeGroup[@ref]"):
        name = ref.get("ref")
        if name in ATTR_GROUPS and name not in seen:
            seen.add(name)
            out.extend(_xsd_attributes(ATTR_GROUPS[name], seen))
    return out


def _xsd_children(node, seen=None):
    """Return [(name, is_list, required)] in XSD sequence order, expanding groups."""
    seen = set() if seen is None else seen
    out = []
    for child in node:
        tag = child.tag.replace(XS, "")
        if tag == "element" and child.get("ref"):
            max_occurs = child.get("maxOccurs", "1")
            is_list = max_occurs == "unbounded" or (
                max_occurs.isdigit() and int(max_occurs) > 1)
            out.append((child.get("ref"), is_list, child.get("minOccurs", "1") != "0"))
        elif tag == "group" and child.get("ref"):
            name = child.get("ref")
            repeats = child.get("maxOccurs", "1") == "unbounded"
            optional = child.get("minOccurs", "1") == "0"
            if name in GROUPS and name not in seen:
                seen.add(name)
                for member, member_list, member_req in _xsd_children(GROUPS[name], seen):
                    out.append((member, member_list or repeats,
                                member_req and not optional))
        elif tag in ("sequence", "choice", "all", "complexContent", "extension",
                     "restriction"):
            inner = _xsd_children(child, seen)
            if tag == "choice":
                # odmlib cannot express xs:choice; every arm is optional to it.
                inner = [(n, is_list, False) for (n, is_list, _) in inner]
            out.extend(inner)
    return out


def _xsd_element(name):
    """Return (attrs, children, has_content) for an XSD element name."""
    ctype = CTYPES[ELEM_TYPE[name]]
    attrs = _xsd_attributes(ctype)
    children = _xsd_children(ctype)
    has_content = (ctype.get("mixed") == "true"
                   or ctype.find(f"{XS}simpleContent") is not None)
    return attrs, children, has_content


# ---------------------------------------------------------------------------
# Model introspection
# ---------------------------------------------------------------------------

def _model_classes():
    """Return {class_name: class} for ODMElement subclasses defined in the model."""
    out = {}
    for name in dir(ODM2):
        obj = getattr(ODM2, name)
        if (isinstance(obj, type) and issubclass(obj, OE.ODMElement)
                and obj is not OE.ODMElement and obj.__module__ == ODM2.__name__):
            out[name] = obj
    return out


MODEL = _model_classes()


# ---------------------------------------------------------------------------
# Comparison A -- model vs XSD
# ---------------------------------------------------------------------------

def compare_model_to_xsd():
    """Return (per_class_findings, missing_classes, classes_not_in_xsd)."""
    findings = {}
    for name in sorted(ELEM_TYPE):
        if name not in MODEL:
            continue
        cls = MODEL[name]
        xsd_attrs, xsd_children, has_content = _xsd_element(name)
        if has_content:
            xsd_attrs = [("_content", False)] + xsd_attrs
        xsd_attr_req = dict(xsd_attrs)
        model_attr_req = {a: d.required for a, d in cls._attrs.items()}
        model_children = {
            e: (isinstance(d, T.ODMListObject), d.required)
            for e, d in cls._elems.items()
        }

        found = set()
        for attr, required in xsd_attr_req.items():
            if attr not in model_attr_req:
                found.add(f"attr-missing:{attr}")
            elif attr != "_content" and model_attr_req[attr] != required:
                found.add(f"attr-required:{attr}"
                          f"(xsd={'required' if required else 'optional'})")
        for attr in model_attr_req:
            if attr not in xsd_attr_req:
                found.add(f"attr-extra:{attr}")

        xsd_child_spec = {n: (is_list, req) for n, is_list, req in xsd_children}
        for child, (is_list, required) in xsd_child_spec.items():
            if child not in model_children:
                found.add(f"elem-missing:{child}")
                continue
            model_list, model_required = model_children[child]
            if model_list != is_list:
                found.add(f"elem-list:{child}"
                          f"(xsd={'list' if is_list else 'single'})")
            if model_required != required:
                found.add(f"elem-required:{child}"
                          f"(xsd={'required' if required else 'optional'})")
        for child in model_children:
            if child not in xsd_child_spec:
                found.add(f"elem-extra:{child}")

        shared = set(xsd_child_spec) & set(model_children)
        xsd_order = [n for n, _, _ in xsd_children if n in shared]
        model_order = [e for e in cls._elems if e in shared]
        if xsd_order != model_order:
            found.add("elem-order")

        if found:
            findings[name] = found

    missing = {n for n in ELEM_TYPE if n not in MODEL}
    not_in_xsd = {n for n in MODEL if n not in ELEM_TYPE}
    return findings, missing, not_in_xsd


# ---------------------------------------------------------------------------
# Comparison B -- stub vs model
# ---------------------------------------------------------------------------

def compare_stub_to_model():
    """Return (classes_missing_from_stub, classes_only_in_stub, field_mismatches)."""
    with open(STUB_PATH, encoding="utf-8") as stub_file:
        tree = ast.parse(stub_file.read())
    stub = {
        node.name: [n.target.id for n in node.body if isinstance(n, ast.AnnAssign)]
        for node in tree.body if isinstance(node, ast.ClassDef)
    }
    model = {n: list(c._attrs) + list(c._elems) for n, c in MODEL.items()}
    missing = set(model) - set(stub)
    extra = set(stub) - set(model)
    mismatched = {n for n in set(model) & set(stub) if model[n] != stub[n]}
    return missing, extra, mismatched


# ---------------------------------------------------------------------------
# Comparison C -- valuesets vs model, by name and by value
# ---------------------------------------------------------------------------

def _classify(type_name, seen=None):
    """Classify an XSD simpleType.

    Returns ``("closed", values)`` for a plain enumeration, ``("open", values)``
    for a union of an enumeration with bare ``xs:string`` (an extensible
    vocabulary), ``("pattern", regex)`` for a pattern restriction, or
    ``("free", None)`` for anything unconstrained.
    """
    seen = set() if seen is None else seen
    if type_name in seen or type_name not in SIMPLE_TYPES:
        return ("free", None)
    seen.add(type_name)
    node = SIMPLE_TYPES[type_name]
    values = [e.get("value") for e in node.findall(f".//{XS}enumeration")]
    patterns = [pat.get("value") for pat in node.findall(f".//{XS}pattern")]
    union = node.find(f"{XS}union")
    if union is not None:
        is_open = False
        for inner in union.findall(f"{XS}simpleType"):
            for res in inner.findall(f"{XS}restriction"):
                if res.get("base") == "xs:string" and not list(res):
                    is_open = True
                else:
                    kind, sub = _classify(res.get("base"), seen)
                    if kind in ("closed", "open") and sub:
                        values.extend(sub)
        for member in (union.get("memberTypes") or "").split():
            kind, sub = _classify(member, seen)
            if kind in ("closed", "open") and sub:
                values.extend(sub)
            elif kind == "free":
                is_open = True
        if values:
            return ("open" if is_open else "closed", sorted(set(values)))
        return ("free", None)
    if values:
        return ("closed", sorted(set(values)))
    if patterns:
        return ("pattern", patterns[0])
    restriction = node.find(f"{XS}restriction")
    if restriction is not None and restriction.get("base") in SIMPLE_TYPES:
        return _classify(restriction.get("base"), seen)
    return ("free", None)


def _xsd_attribute_types(node, seen=None):
    """Return [(attribute_name, xsd_type_name)], resolving attributeGroup refs."""
    seen = set() if seen is None else seen
    out = []
    for attr in node.findall(f".//{XS}attribute"):
        name = attr.get("name") or (attr.get("ref") or "").split(":")[-1]
        if name:
            out.append((name, attr.get("type")))
    for ref in node.findall(f".//{XS}attributeGroup[@ref]"):
        name = ref.get("ref")
        if name in ATTR_GROUPS and name not in seen:
            seen.add(name)
            out.extend(_xsd_attribute_types(ATTR_GROUPS[name], seen))
    return out


def compare_valuesets_to_model():
    """Return (dead_keys, descriptors_with_no_key, value_findings).

    The first two are name-level. ``value_findings`` compares against what each
    attribute's XSD type actually permits, which is the check that catches a key
    resolving to the *wrong* values, or an enumerated attribute modelled as a
    plain string and therefore never checked at all.
    """
    with open(VALUESETS_PATH, encoding="utf-8") as vs_file:
        entries = json.load(vs_file)["odm_2_0"]
    keys = set(entries)
    declared = set()
    for name, cls in MODEL.items():
        for attr, descriptor in cls._attrs.items():
            if isinstance(descriptor, T.ValueSetString):
                declared.add(f"{name}.{attr}")

    findings = set()
    for element, type_name in ELEM_TYPE.items():
        cls = MODEL.get(element)
        if cls is None:
            continue
        for attr, attr_type in _xsd_attribute_types(CTYPES[type_name]):
            if not attr_type or attr not in cls._attrs:
                continue
            kind, payload = _classify(attr_type)
            key = f"{element}.{attr}"
            checked = isinstance(cls._attrs[attr], T.ValueSetString)
            entry = entries.get(key)
            if kind == "closed":
                if not checked or entry is None:
                    findings.add(f"valueset-missing:{key}")
                elif isinstance(entry, list) and sorted(set(entry)) != payload:
                    findings.add(f"valueset-values:{key}")
                elif not isinstance(entry, list):
                    findings.add(f"valueset-too-wide:{key}")
            elif kind in ("open", "pattern") and checked:
                # a closed list cannot express an extensible union or a pattern
                if isinstance(entry, list):
                    findings.add(f"valueset-too-narrow:{key}")
    return keys - declared, declared - keys, findings


# ---------------------------------------------------------------------------
# Allowlists -- shrink these as each alignment phase lands
# ---------------------------------------------------------------------------

#: Per-element divergences between the model and the bundled ODM 2.0 XSD.
MODEL_XSD_DIVERGENCES: dict[str, set[str]] = {
    "Location": {
        "elem-missing:Query",
    },
    "ODM": {
        "elem-missing:Association",
        "elem-missing:ClinicalData",
        "elem-missing:ReferenceData",
    },
    "TranslatedText": {
        "elem-missing:xhtml:div",
    },
}

#: XSD elements with no model class at all. The ClinicalData/ReferenceData
#: subtree among these is deliberately deferred to v0.3.0.
CLASSES_MISSING_FROM_MODEL: set[str] = {
    "Annotation",
    "Association",
    "AuditRecord",
    "ClinicalData",
    "Comment",
    "DateTimeStamp",
    "Flag",
    "FlagType",
    "FlagValue",
    "InvestigatorRef",
    "ItemData",
    "ItemGroupData",
    "KeySet",
    "Query",
    "ReasonForChange",
    "ReferenceData",
    "Signature",
    "SignatureRef",
    "SiteRef",
    "SourceID",
    "StudyEventData",
    "SubjectData",
    "UserRef",
    "Value",
}

#: Model classes that are not declared as elements anywhere in the ODM 2.0
#: XSD -- ODM 1.3.2 carry-over.
CLASSES_NOT_IN_XSD: set[str] = set()

#: Model classes absent from ``model.pyi``.
STUB_CLASSES_MISSING: set[str] = {
    "CDISCNotes",
    "CRFCompletionInstructions",
    "Definition",
    "ImplementationNotes",
    "Prompt",
    "WhereClauseRef",
}

#: ``model.pyi`` classes that no longer exist in the model.
STUB_CLASSES_EXTRA: set[str] = set()

#: Classes whose ``model.pyi`` field list does not match the model.
STUB_FIELD_MISMATCHES: set[str] = {
    "CodeListItem",
    "ItemGroupDef",
    "ItemRef",
    "MethodDef",
    "ODM",
    "Study",
    "StudyEventDef",
}

#: ``odm_2_0`` valueset keys that match no ``ValueSetString`` descriptor. These
#: are inert -- unused data, not a validation hole. Keys for classes that do not
#: exist yet were removed rather than pre-staged: they cannot be verified, which
#: is how four misspellings survived undetected.
VALUESET_DEAD_KEYS: set[str] = set()

#: ``ValueSetString`` descriptors with no ``odm_2_0`` valueset key. Unlike a
#: dead key this is **loud**: ``value_set`` returns the unknown sentinel,
#: ``validate`` maps it to False, and ``ValidValues.__set__`` then raises for
#: every value, so the attribute becomes unusable.
VALUESET_MISSING_KEYS: set[str] = set()

#: Attributes whose value set does not match what the XSD type permits --
#: missing, wrong values, or a closed list where the XSD is an extensible union
#: or a pattern. Only *modelled* classes are compared, so the ClinicalData-layer
#: attributes will appear here of their own accord when v0.3.0 adds their
#: classes, with the values the XSD requires.
VALUESET_VALUE_FINDINGS: set[str] = set()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _diff_message(kind, unexpected, stale):
    lines = []
    if unexpected:
        lines.append(f"{len(unexpected)} NEW {kind} not in the allowlist "
                     f"(fix the model, or add them deliberately):")
        lines += [f"    + {item}" for item in sorted(unexpected)]
    if stale:
        lines.append(f"{len(stale)} STALE {kind} — no longer present, "
                     f"delete from the allowlist:")
        lines += [f"    - {item}" for item in sorted(stale)]
    return "\n" + "\n".join(lines)


class TestModelMatchesXSD(TestCase):
    """The model's divergence from the XSD equals MODEL_XSD_DIVERGENCES exactly."""

    @classmethod
    def setUpClass(cls):
        cls.findings, cls.missing, cls.not_in_xsd = compare_model_to_xsd()

    def test_per_element_divergences_match_allowlist(self):
        unexpected, stale = set(), set()
        for name in set(self.findings) | set(MODEL_XSD_DIVERGENCES):
            actual = self.findings.get(name, set())
            allowed = MODEL_XSD_DIVERGENCES.get(name, set())
            unexpected |= {f"{name}: {f}" for f in actual - allowed}
            stale |= {f"{name}: {f}" for f in allowed - actual}
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("model/XSD divergences", unexpected, stale))

    def test_classes_missing_from_model_match_allowlist(self):
        unexpected = self.missing - CLASSES_MISSING_FROM_MODEL
        stale = CLASSES_MISSING_FROM_MODEL - self.missing
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("XSD elements with no model class", unexpected, stale))

    def test_classes_not_in_xsd_match_allowlist(self):
        unexpected = self.not_in_xsd - CLASSES_NOT_IN_XSD
        stale = CLASSES_NOT_IN_XSD - self.not_in_xsd
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("model classes absent from the XSD", unexpected, stale))


class TestStubMirrorsModel(TestCase):
    """``model.pyi`` is checked by nothing else — nothing type-checks it in CI."""

    @classmethod
    def setUpClass(cls):
        cls.missing, cls.extra, cls.mismatched = compare_stub_to_model()

    def test_stub_missing_classes_match_allowlist(self):
        unexpected = self.missing - STUB_CLASSES_MISSING
        stale = STUB_CLASSES_MISSING - self.missing
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("model classes absent from model.pyi", unexpected, stale))

    def test_stub_extra_classes_match_allowlist(self):
        unexpected = self.extra - STUB_CLASSES_EXTRA
        stale = STUB_CLASSES_EXTRA - self.extra
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("model.pyi classes not in the model", unexpected, stale))

    def test_stub_field_mismatches_match_allowlist(self):
        unexpected = self.mismatched - STUB_FIELD_MISMATCHES
        stale = STUB_FIELD_MISMATCHES - self.mismatched
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("model.pyi field-list mismatches", unexpected, stale))


class TestValuesetsMatchModel(TestCase):
    """A valueset key that never resolves leaves its attribute unvalidated."""

    @classmethod
    def setUpClass(cls):
        cls.dead, cls.missing, cls.value_findings = compare_valuesets_to_model()

    def test_dead_valueset_keys_match_allowlist(self):
        unexpected = self.dead - VALUESET_DEAD_KEYS
        stale = VALUESET_DEAD_KEYS - self.dead
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("odm_2_0 valueset keys matching no descriptor",
                          unexpected, stale))

    def test_valueset_descriptors_all_have_keys(self):
        unexpected = self.missing - VALUESET_MISSING_KEYS
        stale = VALUESET_MISSING_KEYS - self.missing
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("ValueSetString descriptors with no valueset key",
                          unexpected, stale))

    def test_valueset_values_match_the_xsd(self):
        """Names matching is not enough -- the values must match the XSD type."""
        unexpected = self.value_findings - VALUESET_VALUE_FINDINGS
        stale = VALUESET_VALUE_FINDINGS - self.value_findings
        self.assertEqual(
            (unexpected, stale), (set(), set()),
            _diff_message("valueset/XSD value mismatches", unexpected, stale))


# ---------------------------------------------------------------------------
# Maintenance helper
# ---------------------------------------------------------------------------

def _dump():
    """Print the current divergences as literals ready to paste above."""
    findings, missing, not_in_xsd = compare_model_to_xsd()
    stub_missing, stub_extra, stub_mismatched = compare_stub_to_model()
    dead, no_key, value_findings = compare_valuesets_to_model()

    print("MODEL_XSD_DIVERGENCES: dict[str, set[str]] = {")
    for name in sorted(findings):
        print(f'    "{name}": {{')
        for item in sorted(findings[name]):
            print(f'        "{item}",')
        print("    },")
    print("}\n")
    for label, values in (
        ("CLASSES_MISSING_FROM_MODEL", missing),
        ("CLASSES_NOT_IN_XSD", not_in_xsd),
        ("STUB_CLASSES_MISSING", stub_missing),
        ("STUB_CLASSES_EXTRA", stub_extra),
        ("STUB_FIELD_MISMATCHES", stub_mismatched),
        ("VALUESET_DEAD_KEYS", dead),
        ("VALUESET_MISSING_KEYS", no_key),
        ("VALUESET_VALUE_FINDINGS", value_findings),
    ):
        print(f"{label}: set[str] = {{")
        for item in sorted(values):
            print(f'    "{item}",')
        print("}\n")


if __name__ == "__main__":
    _dump()
