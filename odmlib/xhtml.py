"""XHTML markup carried inside ODM 2.0 ``TranslatedText``.

The ODM 2.0 XSD types ``TranslatedText`` as mixed content with an optional
``xhtml:div`` child. odmlib holds that child as one markup string -- the
serialized ``div``, plus any text that follows it inside the TranslatedText -- rather
than modelling the XHTML element set.

The stored string is self-contained: the ``div`` carries its own
``xmlns="http://www.w3.org/1999/xhtml"`` declaration, so writing it back never
depends on :class:`~odmlib.ns_registry.NamespaceRegistry` state, and the string
survives a JSON round trip unchanged. For example::

    <div xmlns="http://www.w3.org/1999/xhtml"><p>Systolic <b>blood</b> pressure</p></div>

.. versionadded:: 0.3.0
"""
from __future__ import annotations
import copy
import xml.etree.ElementTree as ET
from typing import Dict

XHTML_NS = "http://www.w3.org/1999/xhtml"
XHTML_DIV = "{" + XHTML_NS + "}div"
XML_NS = "http://www.w3.org/XML/1998/namespace"
_WRAPPER = "odmlib-xhtml-fragment"


def _literal_name(name: str, declarations: Dict[str, str], element: bool) -> str:
    """Turn a Clark name into the literal ``prefix:local`` form odmlib serializes."""
    if not name.startswith("{"):
        return name
    uri, local = name[1:].split("}", 1)
    if element and uri == XHTML_NS:
        return local                       # in scope through the div's default xmlns
    if uri == XML_NS:
        return "xml:" + local              # the xml prefix is always bound
    for prefix, bound in declarations.items():
        if bound == uri:
            return f"{prefix}:{local}"
    prefix = f"xhns{len(declarations)}"
    declarations[prefix] = uri
    return f"{prefix}:{local}"


def to_literal(element: ET.Element, top: bool = True) -> ET.Element:
    """Copy a namespace-resolved subtree into literal tags with local declarations.

    XHTML elements lose their namespace in favour of a default ``xmlns`` on the top
    element; any other namespace is declared on the element that uses it. The result can
    be appended to odmlib's prefix-literal serialization buffer, or passed to
    ``ET.tostring`` on its own.
    """
    declarations: Dict[str, str] = {}
    tag = _literal_name(element.tag, declarations, element=True)
    attrib = {"xmlns": XHTML_NS} if top else {}
    for key, value in element.attrib.items():
        attrib[_literal_name(key, declarations, element=False)] = value
    for prefix, uri in declarations.items():
        attrib["xmlns:" + prefix] = uri
    literal = ET.Element(tag, attrib)
    literal.text = element.text
    literal.tail = element.tail
    for child in element:
        literal.append(to_literal(child, top=False))
    return literal


def serialize_div(div: ET.Element) -> str:
    """Return the markup string for a parsed ``xhtml:div`` and the text after it.

    Whitespace-only text after the div is indentation, not content, and is dropped.
    """
    source = copy.copy(div)
    if source.tail is not None and source.tail.isspace():
        source.tail = None
    return ET.tostring(to_literal(source), encoding="unicode")


def parse_fragment(markup: str) -> ET.Element:
    """Parse a markup string into a namespace-resolved ``div`` (tail = trailing text).

    Elements written without a namespace are placed in the XHTML namespace, so
    ``<div><p>Hi</p></div>`` is accepted and stored as XHTML.

    Raises:
        ValueError: if the markup is not well formed, declares a DOCTYPE or entities,
            or is not exactly one ``div`` element optionally followed by text.
    """
    upper = markup.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise ValueError("DOCTYPE and entity declarations are not allowed in XHTML markup")
    try:
        wrapper = ET.fromstring(f"<{_WRAPPER}>{markup}</{_WRAPPER}>")
    except ET.ParseError as ex:
        raise ValueError(f"XHTML markup is not well-formed XML: {ex}") from ex
    if wrapper.text is not None and not wrapper.text.isspace():
        raise ValueError("XHTML markup must start with a div element, not text")
    if len(wrapper) != 1:
        raise ValueError(f"XHTML markup must hold exactly one div element, found {len(wrapper)}")
    div = wrapper[0]
    for element in div.iter():
        if isinstance(element.tag, str) and not element.tag.startswith("{"):
            element.tag = "{" + XHTML_NS + "}" + element.tag
    if div.tag != XHTML_DIV:
        raise ValueError(f"XHTML markup must be an xhtml:div element, found {div.tag}")
    return div


def normalize(markup: str) -> str:
    """Validate *markup* and return it in the canonical self-contained form."""
    return serialize_div(parse_fragment(markup))
