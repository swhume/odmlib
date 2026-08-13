Validating ODM Documents
=========================

odmlib provides several validation mechanisms for ODM documents.

Element Order Verification
--------------------------

ODM specifies the required order of child elements in XML.

.. note::

   ``write_xml()`` and ``to_xml()`` always emit children in the model
   declaration order defined in the model module (e.g.
   ``odmlib/odm_1_3_2/model.py``), regardless of the order in which you
   assigned the children on the instance. You **do not** need to call
   ``reorder_object()`` before serializing — the serializer drives the
   order from the metaclass-captured ``_elems``, which mirrors the
   schema content model.

The ``verify_order()`` / ``reorder_object()`` API is still useful when
you want to fail-fast on object construction order (e.g. so unit tests
catch a stale build script that assigns children out of order), or when
you mutate the in-memory ``__dict__`` ordering for some other reason.

odmlib can verify and fix element ordering:

.. code-block:: python

    import warnings
    from odmlib.exceptions import OdmlibElementOrderError

    # Check order (raises OdmlibElementOrderError if out of order)
    try:
        odm.verify_order()
        print("Element order is correct")
    except OdmlibElementOrderError as e:
        print(f"Order error: {e}")
        # Fix automatically (issues OdmlibWarning)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            odm.reorder_object()

Scope and limitations
~~~~~~~~~~~~~~~~~~~~~

``verify_order()`` is a method on :class:`~odmlib.odm_element.ODMElement`,
so it works on any odmlib model object — the ``ODM`` root, ``Study``,
``MetaDataVersion``, ``ItemGroupDef``, leaf elements, and so on. It
recurses through every ``ODMElement`` child and every entry of every
``ODMListObject`` list, so a single call on the odmlib root covers the
whole document.

It does **not** work on :class:`xml.etree.ElementTree.Element` — that
is the parsed XML representation, not an odmlib object. If you only
have an ElementTree, load it through
:class:`~odmlib.odm_loader.XMLODMLoader` (or
:class:`~odmlib.odm_loader.XMLDefineLoader` for Define-XML) first.

A few limitations to keep in mind:

- **Custom extensions must redeclare base children.** Each class's
  child-element ordering comes from the descriptors declared in its
  own class body, captured into ``_elems`` by ``ODMMeta``. If you
  subclass an existing model class to extend it, you must redeclare
  the base children in schema order — see
  ``odmlib/define_2_1/model.py`` for the canonical pattern (the
  ``ItemGroupDef`` extension assigns ``Description = ODM.ItemGroupDef.Description``
  etc. to lock in the order). If a base child is missing from the
  subclass body, ``verify_order()`` will treat it as unexpected.
- **Permissive mode can produce false positives.** When loading a
  non-conformant document with
  :class:`~odmlib.mode.ValidationMode.SKIP_TYPE` active, unknown
  attributes are accepted into the instance ``__dict__`` directly.
  Those keys are not in ``_elems`` and will trip ``verify_order()``.
  Run order verification only after you have cleaned up any
  unknown-attribute artefacts. See :doc:`permissive_loading` for the
  load-fix-validate workflow.
- **List-internal order is not checked.** ``verify_order()`` only
  checks the order of different *kinds* of child elements relative to
  each other (e.g., ``Description`` before ``ItemRef``). It does not
  check whether two ``ItemRef`` entries inside an ``ItemGroupDef``
  appear in the right order — ODM typically relies on ``OrderNumber``
  attributes for that, not list position.
- **Completeness is not checked.** ``verify_order()`` does not detect
  missing required children. Use
  :meth:`~odmlib.odm_element.ODMElement.verify_conformance` (Cerberus
  schema check) for that, or :meth:`~odmlib.odm_element.ODMElement.validate`
  to combine both.

Relationship to serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Different serializers handle child order differently:

- :meth:`~odmlib.odm_element.ODMElement.to_xml` /
  :meth:`~odmlib.odm_element.ODMElement.write_xml` emit children in
  ``_elems`` (model declaration) order regardless of ``__dict__``
  insertion order. **You do not need to run ``verify_order()`` /
  ``reorder_object()`` before XML serialization.**
- :meth:`~odmlib.odm_element.ODMElement.to_dict` /
  :meth:`~odmlib.odm_element.ODMElement.to_json` walk ``__dict__``
  directly, so they reflect whatever order the instance accumulated.
  If a stable, schema-aligned key order matters for downstream
  consumers of your JSON/dict output, run ``verify_order()`` (and
  ``reorder_object()`` if it fails) before calling them.

OID Uniqueness and Reference Integrity
---------------------------------------

odmlib can verify that all OIDs are unique and that all OID references
point to valid definitions:

Using the Dynamic OID Checker (recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from odmlib import create_oid_checker

    # Create a dynamic checker for ODM 1.3.2
    checker = create_oid_checker("odm_1_3_2")

    # Verify OIDs (raises OdmlibOIDError on failure)
    is_valid = odm.verify_oids(checker)
    print(f"OIDs valid: {is_valid}")

    # Find unreferenced definitions (e.g., unused code lists)
    unreferenced = odm.unreferenced_oids(checker)
    for oid in unreferenced:
        print(f"Unreferenced: {oid}")

Using the Manual OID Checker (deprecated)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import odmlib.odm_1_3_2.rules.oid_ref as OR
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        checker = OR.OIDRef()

    is_valid = odm.verify_oids(checker)

Conformance Validation
-----------------------

Cerberus-based schema validation checks structural conformance:

.. code-block:: python

    import odmlib.odm_1_3_2.rules.metadata_schema as SC

    validator = SC.MetadataSchema()
    result = mdv.verify_conformance(validator)
    print(f"Conformance result: {result}")

Combined Validation with Error Collection
------------------------------------------

Use the ``validate()`` method to run all checks and collect every error
instead of failing on the first one:

.. code-block:: python

    from odmlib import create_oid_checker
    import odmlib.odm_1_3_2.rules.metadata_schema as SC

    checker = create_oid_checker("odm_1_3_2")
    validator = SC.MetadataSchema()

    errors = odm.validate(
        collect_errors=True,
        oid_checker=checker,
        conformance_checker=validator
    )

    if not errors:
        print("Document is valid")
    else:
        for err in errors:
            print(f"Error: {err}")

What "every error" means per layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each of the three layers enumerates its own problems rather than stopping at
the first:

* **Element order** — one :class:`~odmlib.exceptions.OdmlibElementOrderError`
  per misordered element. The walk continues into the children of a misordered
  element, so a single pass lists everything
  :meth:`~odmlib.odm_element.ODMElement.reorder_object` needs to fix.
* **OID** — one :class:`~odmlib.exceptions.OdmlibOIDError` per duplicate OID
  and per bad reference. Duplicates no longer abort the traversal, so the
  reference checks still run. On a duplicate the *first* definition is kept.
* **Conformance** — the bundled Cerberus result is expanded into one
  :class:`~odmlib.exceptions.OdmlibConformanceError` per failing field, each
  carrying a dotted ``field_path`` (e.g. ``"ItemGroupDef.0.Name"``) and the
  complete raw dict on ``cerberus_errors``.

Because the number of errors is now unbounded, errors are best filtered by
type rather than accessed by index:

.. code-block:: python

    from odmlib import OdmlibOIDError

    oid_problems = [e for e in errors if isinstance(e, OdmlibOIDError)]

Capping the error list
~~~~~~~~~~~~~~~~~~~~~~

A badly broken document can produce thousands of errors.  ``max_errors`` stops
collection once the cap is reached and appends a final
:class:`~odmlib.exceptions.OdmlibErrorLimitError`, so the list holds at most
``max_errors + 1`` entries:

.. code-block:: python

    errors = odm.validate(collect_errors=True, oid_checker=checker,
                          max_errors=100)

    if errors and isinstance(errors[-1], OdmlibErrorLimitError):
        print("More problems remain — fix these and re-run")

The cap is enforced inside each layer, so validation genuinely stops early
rather than collecting everything and truncating the result.

Checker reuse
~~~~~~~~~~~~~

An OID checker accumulates every OID it sees, so it is single-use per
document.  Reusing one reports every OID as a duplicate.  Either build a fresh
checker per document, or call ``reset()``:

.. code-block:: python

    checker.reset()
    errors = other_odm.validate(collect_errors=True, oid_checker=checker)

``validate()`` emits an :class:`~odmlib.exceptions.OdmlibWarning` in collect
mode when it is handed a checker that still holds state.

.. note::

   The deprecated ``rules/oid_ref.py`` ``OIDRef`` classes (removed in v0.3.0)
   do not implement the collecting protocol and contribute at most **one**
   error for the whole OID layer.  Use
   :func:`~odmlib.oid_generator.create_oid_checker` to get full reporting.
   :func:`~odmlib.exceptions.is_collecting_checker` tells you which you have.

Only :class:`~odmlib.exceptions.OdmlibError` subclasses are collected.  Any
other exception — a bug in a custom checker, an ``AttributeError`` from a
malformed tree — propagates in both modes rather than being reported as a
document defect.

Collecting from ``verify_oids()`` directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The OID layer can be run on its own with collection enabled:

.. code-block:: python

    from odmlib import ErrorCollector

    collector = ErrorCollector()
    with checker.collecting(collector):
        odm.verify_oids(checker)

    for err in collector.errors:
        print(err)

This pattern is particularly useful after permissive loading, where a
non-conformant document has been loaded with validation bypassed.  After
fixing known issues, use ``validate(collect_errors=True)`` to confirm all
problems have been resolved.  See :doc:`permissive_loading` for the
complete workflow.

XML Schema (XSD) Validation
---------------------------

Use :class:`~odmlib.odm_parser.ODMSchemaValidator` to validate an
ODM/Define-XML document against the official CDISC XSD bundled with
odmlib:

.. code-block:: python

    from odmlib.odm_parser import ODMSchemaValidator, ODMParser

    # ODM 1.3.2
    validator = ODMSchemaValidator(standard="odm", version="1.3.2")

    # ODM 2.0
    validator = ODMSchemaValidator(standard="odm", version="2.0")

    # Define-XML 2.0 / 2.1
    validator = ODMSchemaValidator(standard="define", version="2.1")

    # Validate a file directly (raises OdmlibSchemaValidationError on failure)
    validator.validate_file("study.xml")

    # Or validate an already-parsed ElementTree (returns bool)
    tree = ODMParser("study.xml").parse_tree()
    is_valid = validator.validate_tree(tree)

For a custom or local XSD that is not bundled with odmlib, pass an
explicit ``xsd_file`` path:

.. code-block:: python

    validator = ODMSchemaValidator(xsd_file="/path/to/custom.xsd")

The supported ``(standard, version)`` combinations are listed in
:data:`odmlib.schema_manager._MAIN_SCHEMA`.

Understanding Error Types
--------------------------

odmlib uses a custom exception hierarchy:

.. list-table::
   :header-rows: 1

   * - Exception
     - When raised
   * - :exc:`~odmlib.exceptions.OdmlibError`
     - Base class for all odmlib errors
   * - :exc:`~odmlib.exceptions.OdmlibTypeError`
     - Type validation failure (wrong type assigned to attribute)
   * - :exc:`~odmlib.exceptions.OdmlibValidationError`
     - Value validation failure (invalid format, out of range)
   * - :exc:`~odmlib.exceptions.OdmlibRequiredAttributeError`
     - Required attribute missing during construction
   * - :exc:`~odmlib.exceptions.OdmlibElementOrderError`
     - Element order does not match ODM specification
   * - :exc:`~odmlib.exceptions.OdmlibOIDError`
     - OID uniqueness or ref/def integrity failure
   * - :exc:`~odmlib.exceptions.OdmlibLoaderStateError`
     - Loader used before document opened
   * - :exc:`~odmlib.exceptions.OdmlibNamespaceError`
     - Invalid namespace URI or unregistered prefix
