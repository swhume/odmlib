# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

odmlib is a Python library for creating, parsing, and validating CDISC ODM (Operational Data Model) documents. It supports multiple CDISC standards: ODM 1.3.2, ODM 2.0, Define-XML 2.0/2.1, Dataset-XML, Dataset-JSON, CT-XML, and ARM.

## Commands

```bash
# Install for development (includes pytest, coverage, mypy, sphinx, pandas)
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_odm_loader.py -v

# Run with coverage
python -m pytest tests/ --cov=odmlib --cov-report=term-missing

# Build docs
cd docs && make html
```

CI enforces a 70% coverage threshold (`--cov-fail-under=70`).

## Architecture

The library uses a **descriptor-based, metaclass-driven ORM pattern** to map XML/JSON to Python objects.

### Core Mechanism

**`ODMMeta` metaclass** (`odm_element.py`) processes class definitions at creation time, separating XML attributes (`_attrs`) from child elements (`_elems`) and preserving declaration order. Every model class inherits from `ODMElement`.

**Type-validated descriptors** (`typed.py`, `descriptor.py`) enforce types at assignment time. Descriptor types include `String`, `OID`, `OIDRef`, `Integer`, `Float`, `Email`, `DateTimeString`, `ODMObject` (single child), `ODMListObject` (list of children), and ~80 others.

**Declarative model classes** (`odmlib/<standard>/model.py`) define each ODM element as a Python class with descriptors as class attributes. Adding support for a new ODM element means adding a class here — the metaclass and descriptors handle serialization automatically.

### Data Flow

```
XML/JSON File → Parser (odm_parser.py)
    → DocumentLoader (XMLODMLoader / JSONODMLoader / etc.)
    → Recursively instantiate model objects via descriptors
    → ODMElement Python object tree
    → Validation (OID refs, conformance, schema)
    → Output: write_xml() / as_json()
```

### Key Modules

| Module | Role |
|--------|------|
| `odm_element.py` | `ODMElement` base class, `ODMMeta` metaclass, XML writer |
| `typed.py` | All type descriptor classes (~80+) |
| `descriptor.py` | Base `Descriptor` protocol |
| `loader.py` | `ODMLoader` facade — unified entry point for loading any standard |
| `odm_loader.py` | Concrete XML/JSON loaders for ODM |
| `define_loader.py` | Concrete loaders for Define-XML |
| `arm_loader.py` | Loaders for ARM-extended Define-XML |
| `builder.py` | Fluent/chainable API for programmatic document construction |
| `context.py` | Context managers: `open_odm()`, `open_define()` |
| `oid_generator.py` | Derives OID validation rules from model classes via introspection |
| `odm_parser.py` | XML/JSON parsing and schema validation |
| `ns_registry.py` | Namespace management (Borg singleton) |
| `exceptions.py` | Exception hierarchy with backward-compat dual inheritance |
| `dataframe.py` | Optional pandas integration |

### Standard-Specific Packages

Each CDISC standard lives in its own package under `odmlib/`:
- `odm_1_3_2/` — ODM 1.3.2 (primary, most complete)
- `odm_2_0/` — ODM 2.0 (draft)
- `define_2_0/`, `define_2_1/` — Define-XML
- `dataset_json_1_1/` — Dataset-JSON v1.1
- `arm/` — Analysis Results Metadata extension

Each package has a `model.py` and a `rules/` subdirectory with Cerberus conformance schemas and OID reference rules.

### Adding a New ODM Element

1. Add a class to the appropriate `model.py` using descriptors as class attributes
2. Add conformance rules to `rules/` if needed
3. Register OID ref/def rules in `oid_generator.py` if the element introduces new OIDs

### Validation Layers

1. **Type validation** — descriptor `__set__` raises on bad types (fail-fast)
2. **OID uniqueness/reference** — `oid_generator.py` introspects model classes to derive rules dynamically
3. **Conformance** — Cerberus schemas in `rules/` directories
4. **Schema** — xmlschema validates against official XSD schemas
