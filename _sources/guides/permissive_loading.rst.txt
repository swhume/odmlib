Permissive Loading Mode
========================

Introduction
------------

odmlib validates attribute values at assignment time, which means that
non-conformant ODM or Define-XML files cannot normally be loaded into the
object model.  The permissive loading mode solves this by selectively
bypassing validation during loading, allowing you to inspect, repair, and
re-validate documents that contain invalid content.

Quick Start
-----------

.. code-block:: python

    from odmlib import permissive
    import odmlib.loader as LD
    import odmlib.odm_loader as OL

    loader = LD.ODMLoader(OL.XMLODMLoader())

    with permissive():
        loader.open_odm_document("incomplete_define.xml")
        odm = loader.root()

    # odm is now loaded -- mode is back to strict

Graduated Control
-----------------

The ``permissive()`` context manager accepts a ``ValidationMode`` flag
that controls exactly which validation categories to bypass:

.. code-block:: python

    from odmlib import permissive, ValidationMode

    # Skip only required-attribute checks
    with permissive(ValidationMode.SKIP_REQUIRED):
        ...

    # Skip required + valueset (but still enforce types and formats)
    with permissive(ValidationMode.SKIP_REQUIRED | ValidationMode.SKIP_VALUESET):
        ...

    # Skip everything (the default)
    with permissive():  # defaults to ValidationMode.PERMISSIVE
        ...

.. list-table:: Validation Flags
   :header-rows: 1

   * - Flag
     - What it bypasses
     - Descriptor classes affected
   * - ``SKIP_REQUIRED``
     - Required-attribute checks at construction and access
     - ``Descriptor.__get__``, ``ODMElement.__init__``
   * - ``SKIP_TYPE``
     - Type checks and unknown-attribute rejection
     - ``Typed``, ``Integer``, ``Float``, ``Positive``, ``NonNegative``,
       ``ODMObject``, ``ODMListObject``, ``ODMElement.__init__``,
       ``ODMElement.__setattr__``
   * - ``SKIP_FORMAT``
     - Format validators
     - ``DateTimeString``, ``DateString``, ``PartialDateTimeString``,
       ``PartialDateString``, ``PartialTimeString``,
       ``IncompleteDateTimeString``, ``IncompleteDateString``,
       ``IncompleteTimeString``, ``DurationDateTimeString``,
       ``SASName``, ``SASFormat``, ``Email``, ``Url``, ``FileName``,
       ``Sized``, ``Regex``
   * - ``SKIP_VALUESET``
     - Enumerated value set enforcement
     - ``ValidValues``, ``ExtendedValidValues``, ``ValueSetString``
   * - ``PERMISSIVE``
     - All of the above (composite flag)
     - All descriptor classes

The Load -- Inspect -- Fix -- Validate Workflow
-------------------------------------------------

The recommended workflow for handling non-conformant files:

.. code-block:: python

    from odmlib import permissive
    import odmlib.loader as LD
    import odmlib.odm_loader as OL

    # Step 1: Load permissively
    loader = LD.ODMLoader(OL.XMLODMLoader())
    with permissive():
        loader.open_odm_document("broken_define.xml")
        odm = loader.root()

    # Step 2: Inspect -- mode is strict again, but objects are populated
    mdv = odm.Study[0].MetaDataVersion[0]
    for item in mdv.ItemDef:
        print(f"OID={item.OID}, DataType={item.DataType}")

    # Step 3: Fix issues (assignments are validated in strict mode)
    for item in mdv.ItemDef:
        if item.DataType not in ["text", "integer", "float"]:
            item.DataType = "text"

    # Step 4: Validate
    errors = odm.validate(collect_errors=True)
    if not errors:
        odm.write_xml("fixed_define.xml")
    else:
        for err in errors:
            print(err)

Context Manager Integration
----------------------------

The ``open_odm()`` and ``open_define()`` context managers accept a
``permissive`` parameter:

.. code-block:: python

    from odmlib.context import open_odm
    from odmlib import ValidationMode

    with open_odm("broken.xml", output_file="fixed.xml",
                  permissive=True) as odm:
        # Fix issues here
        ...
    # Saves on clean exit -- but note: save runs in strict mode

    # Targeted relaxation
    with open_odm("broken.xml", output_file="fixed.xml",
                  permissive=ValidationMode.SKIP_REQUIRED) as odm:
        ...

API Reference
--------------

.. autoclass:: odmlib.mode.ValidationMode
   :members:
   :undoc-members:

.. autofunction:: odmlib.mode.permissive

.. autofunction:: odmlib.mode.get_mode

.. autofunction:: odmlib.mode.set_mode

.. autofunction:: odmlib.mode.is_permissive

Safety Notes
------------

- Permissively loaded objects may contain invalid data that does not
  conform to the ODM specification.

- Always call ``validate(collect_errors=True)`` before serializing for
  production use.

- The permissive mode affects only the current context (thread or
  coroutine); other threads and coroutines remain in strict mode.

- When using ``open_odm(permissive=True)``, the auto-save on exit runs
  in strict mode.  If the object tree has unfixed issues that prevent
  serialization, the save may fail.  Call ``write_xml()`` or
  ``write_json()`` inside the ``with`` block (while permissive mode is
  still active) if you need to save an un-fixed document.

- For read-only inspection — for example, loading a known-broken
  document to enumerate its issues without risking a strict-mode save
  failure overwriting the input — pass ``write_on_exit=False``.  No
  file is created or modified when the ``with`` block exits, regardless
  of ``output_file``.

  .. code-block:: python

      with open_odm("broken.xml", permissive=True,
                    write_on_exit=False) as odm:
          errors = odm.validate(collect_errors=True)
          for err in errors:
              print(err)
      # broken.xml is untouched on exit
