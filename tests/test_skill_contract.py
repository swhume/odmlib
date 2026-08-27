"""Contract tests for the odmlib Claude Code skill (``.claude/skills/odmlib/``).

The skill is prose that asserts how this library behaves.  Nothing else in the
repository checks those assertions, so a library change can silently invalidate
the skill -- which is exactly what happened when context-manager writing became
opt-in in 0.2.1 while the skill still documented the 0.2.0 contract.

These tests pin the *machine-checkable* half of the skill's claims against live
introspection.  A library change that contradicts the skill fails here instead
of shipping.  The expected values below are deliberately spelled out as literal
tables: when one of these fails, update the skill prose **and** the table
together, after confirming which of the two is actually wrong.

Stdlib only -- no pyyaml (it is not a dependency), so the front matter is read
by a small purpose-built parser rather than a general YAML one.
"""
import inspect
import os
import re
from unittest import TestCase, skipIf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib")
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
REFERENCES_DIR = os.path.join(SKILL_DIR, "references")

# An sdist checkout has no .claude/ directory; skip rather than fail there.
NO_SKILL = not os.path.isfile(SKILL_MD)
SKILL_REASON = f"skill not present at {SKILL_DIR}"

# Sentinel for "this parameter has no default" in the expected tables below.
REQUIRED = "<required>"

# Agent Skills front-matter spec caps `description` at this many characters.
DESCRIPTION_MAX = 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_front_matter(text):
    """Read the leading ``---`` YAML block of a skill file.

    Supports only what SKILL.md actually uses: ``key: value`` scalars and
    folded block scalars (``key: >-``), whose continuation lines are joined
    with single spaces the way YAML folds them.  This is not a general YAML
    parser and is not meant to become one.
    """
    if not text.startswith("---"):
        raise AssertionError("SKILL.md must open with a YAML front-matter block")
    end = text.index("\n---", 3)
    block = text[3:end]

    fields, key, buf, folded = {}, None, [], False

    def flush():
        if key is not None:
            fields[key] = " ".join(buf).strip()

    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if match and not line[0].isspace():
            flush()
            key = match.group(1)
            rest = match.group(2).strip()
            folded = rest in (">-", ">", "|", "|-")
            buf = [] if folded else [rest]
        elif key is not None:
            buf.append(stripped)
    flush()
    return fields


def signature_pairs(func):
    """``[(param_name, default), ...]`` for *func*, excluding ``self``.

    ``default`` is the literal default, or :data:`REQUIRED` when the parameter
    has none.  ``**kwargs`` is reported as ``("**kwargs", REQUIRED)`` so that
    adding or dropping it is caught too.
    """
    pairs = []
    for name, param in inspect.signature(func).parameters.items():
        if name in ("self", "cls"):
            continue
        if param.kind is inspect.Parameter.VAR_KEYWORD:
            pairs.append(("**" + name, REQUIRED))
            continue
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            pairs.append(("*" + name, REQUIRED))
            continue
        default = param.default
        pairs.append((name, REQUIRED if default is inspect.Parameter.empty else default))
    return pairs


def read_skill_md():
    with open(SKILL_MD, encoding="utf-8") as handle:
        return handle.read()


# ---------------------------------------------------------------------------
# Front matter
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestSkillFrontMatter(TestCase):
    """The front matter is the skill's trigger surface and has a hard size cap."""

    @classmethod
    def setUpClass(cls):
        cls.fields = parse_front_matter(read_skill_md())

    def test_name_is_odmlib(self):
        self.assertEqual(self.fields.get("name"), "odmlib")

    def test_description_present(self):
        self.assertIn("description", self.fields)
        self.assertGreater(len(self.fields["description"]), 200)

    def test_description_within_length_limit(self):
        """Agent Skills caps `description` at 1024 characters."""
        length = len(self.fields["description"])
        self.assertLessEqual(
            length, DESCRIPTION_MAX,
            f"front-matter description is {length} chars, "
            f"{length - DESCRIPTION_MAX} over the {DESCRIPTION_MAX} limit",
        )

    def test_description_mentions_trigger_terms(self):
        """Trimming the description must not cost it its trigger keywords."""
        description = self.fields["description"]
        for term in ("odmlib", "ODM", "Define-XML", "Dataset-JSON", "ARM", "CDISC"):
            with self.subTest(term=term):
                self.assertIn(term, description)


# ---------------------------------------------------------------------------
# Signatures
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestDocumentedSignatures(TestCase):
    """Signatures the skill documents, pinned against live introspection.

    Each entry is the exact parameter list the skill's api-reference publishes.
    """

    def _assert_signature(self, func, expected):
        self.assertEqual(signature_pairs(func), expected)

    # -- context managers: writing is opt-in (the B1 regression) -------------

    def test_open_odm(self):
        from odmlib.context import open_odm
        self._assert_signature(open_odm, [
            ("input_file", REQUIRED),
            ("output_file", None),
            ("model_package", "odm_1_3_2"),
            ("format", None),
            ("permissive", False),
            ("write_on_exit", None),      # None, NOT True: writing is opt-in
        ])

    def test_open_define(self):
        from odmlib.context import open_define
        self._assert_signature(open_define, [
            ("input_file", REQUIRED),
            ("output_file", None),
            ("model_package", "define_2_1"),
            ("format", None),
            ("permissive", False),
            ("write_on_exit", None),      # None, NOT True: writing is opt-in
        ])

    def test_write_on_exit_default_is_none(self):
        """Guard the exact defect B1 fixed, stated as its own assertion.

        A bare ``open_odm(path)`` must not write.  If this default ever goes
        back to ``True``, SKILL.md and api-reference.md both become wrong.
        """
        from odmlib.context import open_odm, open_define
        for func in (open_odm, open_define):
            with self.subTest(func=func.__name__):
                self.assertIsNone(
                    inspect.signature(func).parameters["write_on_exit"].default)

    # -- serialization ------------------------------------------------------

    def test_to_xml_string(self):
        from odmlib.odm_element import ODMElement
        self._assert_signature(ODMElement.to_xml_string, [
            ("xml_declaration", False),
        ])

    def test_to_xml_string_declaration_is_keyword_only(self):
        from odmlib.odm_element import ODMElement
        param = inspect.signature(ODMElement.to_xml_string).parameters["xml_declaration"]
        self.assertIs(param.kind, inspect.Parameter.KEYWORD_ONLY)

    def test_to_element_takes_no_arguments(self):
        from odmlib.odm_element import ODMElement
        self._assert_signature(ODMElement.to_element, [])

    # -- validation ---------------------------------------------------------

    def test_validate(self):
        from odmlib.odm_element import ODMElement
        self._assert_signature(ODMElement.validate, [
            ("collect_errors", False),
            ("oid_checker", None),
            ("conformance_checker", None),
            ("max_errors", None),
        ])

    def test_create_oid_checker(self):
        from odmlib.oid_generator import create_oid_checker
        self._assert_signature(create_oid_checker, [
            ("model_package", REQUIRED),
            ("extra_skip_attrs", None),
            ("extra_skip_elems", None),
        ])

    # -- builder: real defaults, and no ErrorMessage parameter (B3) ----------

    def test_add_method_def(self):
        from odmlib.builder import ODMBuilder
        self._assert_signature(ODMBuilder.add_method_def, [
            ("OID", REQUIRED),
            ("Name", REQUIRED),
            ("Type", REQUIRED),
            ("description", REQUIRED),
            ("formal_expression", None),
            ("expression_context", "Python"),   # a real value, not None
            ("lang", "en"),
            ("**kwargs", REQUIRED),
        ])

    def test_add_condition_def(self):
        from odmlib.builder import ODMBuilder
        self._assert_signature(ODMBuilder.add_condition_def, [
            ("OID", REQUIRED),
            ("Name", REQUIRED),
            ("description", None),
            ("formal_expression", None),
            ("expression_context", "Python"),   # a real value, not None
            ("lang", "en"),
            ("**kwargs", REQUIRED),
        ])

    def test_add_measurement_unit(self):
        from odmlib.builder import ODMBuilder
        self._assert_signature(ODMBuilder.add_measurement_unit, [
            ("OID", REQUIRED),
            ("Name", REQUIRED),
            ("symbol", REQUIRED),
            ("lang", "en"),
            ("**kwargs", REQUIRED),
        ])

    def test_with_range_check(self):
        from odmlib.builder import ODMBuilder
        self._assert_signature(ODMBuilder.with_range_check, [
            ("comparator", REQUIRED),
            ("check_values", REQUIRED),
            ("soft_hard", "Soft"),              # a real value, not None
            ("**kwargs", REQUIRED),
        ])

    def test_with_range_check_has_no_error_message_parameter(self):
        """``ErrorMessage`` is a child element, not a keyword argument.

        Documenting it as a parameter invites ``ErrorMessage="..."``, which
        falls through ``**kwargs`` and raises ``OdmlibTypeError``.
        """
        from odmlib.builder import ODMBuilder
        params = inspect.signature(ODMBuilder.with_range_check).parameters
        self.assertNotIn("ErrorMessage", params)

    # -- loaders and namespaces --------------------------------------------

    def test_xml_odm_loader(self):
        import odmlib.odm_loader as OL
        self._assert_signature(OL.XMLODMLoader.__init__, [
            ("model_package", "odm_1_3_2"),
            ("ns_uri", None),
            ("local_model", False),
            ("nsr", None),                      # documented since S4
        ])

    def test_bind_document_namespaces(self):
        import odmlib.ns_registry as NS
        self._assert_signature(NS.bind_document_namespaces, [
            ("odm_obj", REQUIRED),
            ("snapshot", None),
            ("recursive", False),
        ])


# ---------------------------------------------------------------------------
# Context-manager write behavior
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestContextManagerWriteBehavior(TestCase):
    """Exercise the three write modes SKILL.md documents, on real files.

    The signature tests above pin ``write_on_exit=None`` as the default, but a
    default alone does not pin *behavior*: the decision is made by
    ``if write_on_exit is None: write_on_exit = output_file is not None`` in
    ``ODMContext.__init__``.  Rewriting that line to ``= True`` would make every
    bare ``open_odm()`` overwrite its input while leaving every signature
    untouched -- silent data loss that a signature check cannot see.  These
    tests fail on that change.
    """

    def setUp(self):
        import tempfile
        from odmlib import ODMBuilder
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "study.xml")
        odm = (
            ODMBuilder(model_package="odm_1_3_2")
            .set_file(FileOID="ODM.ORIGINAL", FileType="Snapshot",
                      CreationDateTime="2026-06-30T00:00:00",
                      Granularity="Metadata", ODMVersion="1.3.2",
                      Originator="contract-test")
            .add_study("ST.1", "Demo", "Demo study", "PROTO-1")
            .add_metadata_version(OID="MDV.1", Name="MDV")
            .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
            .build()
        )
        odm.write_xml(self.path)

    def _file_oid(self, path):
        from odmlib.context import open_odm
        with open_odm(path, write_on_exit=False) as odm:
            return odm.FileOID

    def test_bare_open_odm_writes_nothing(self):
        """The documented default: load read-only, discard edits on exit."""
        from odmlib.context import open_odm
        before = open(self.path, "rb").read()
        with open_odm(self.path) as odm:
            odm.FileOID = "ODM.SHOULD.NOT.PERSIST"
        self.assertEqual(open(self.path, "rb").read(), before,
                         "a bare open_odm() must not modify the input file")
        self.assertEqual(self._file_oid(self.path), "ODM.ORIGINAL")

    def test_write_on_exit_false_writes_nothing(self):
        from odmlib.context import open_odm
        before = open(self.path, "rb").read()
        with open_odm(self.path, write_on_exit=False) as odm:
            odm.FileOID = "ODM.SHOULD.NOT.PERSIST"
        self.assertEqual(open(self.path, "rb").read(), before)

    def test_output_file_writes_there_and_leaves_input_alone(self):
        from odmlib.context import open_odm
        before = open(self.path, "rb").read()
        out = os.path.join(self._tmp.name, "study_out.xml")
        with open_odm(self.path, output_file=out) as odm:
            odm.FileOID = "ODM.WRITTEN.ELSEWHERE"
        self.assertTrue(os.path.isfile(out))
        self.assertEqual(self._file_oid(out), "ODM.WRITTEN.ELSEWHERE")
        self.assertEqual(open(self.path, "rb").read(), before,
                         "output_file= must leave the input untouched")

    def test_write_on_exit_true_updates_in_place(self):
        from odmlib.context import open_odm
        with open_odm(self.path, write_on_exit=True) as odm:
            odm.FileOID = "ODM.UPDATED.IN.PLACE"
        self.assertEqual(self._file_oid(self.path), "ODM.UPDATED.IN.PLACE")

    def test_open_define_default_is_also_read_only(self):
        define_file = os.path.join(REPO_ROOT, "tests", "data", "defineV21-SDTM.xml")
        if not os.path.isfile(define_file):
            self.skipTest("test Define-XML file not available")
        import shutil
        from odmlib.context import open_define
        copied = os.path.join(self._tmp.name, "define.xml")
        shutil.copyfile(define_file, copied)
        before = open(copied, "rb").read()
        with open_define(copied) as define:
            define.FileOID = "SHOULD.NOT.PERSIST"
        self.assertEqual(open(copied, "rb").read(), before,
                         "a bare open_define() must not modify the input file")


# ---------------------------------------------------------------------------
# Importable surface
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestTopLevelImports(TestCase):
    """Everything the skill says you can import from ``odmlib``, you can."""

    # The list api-reference.md section 1 publishes, verbatim.
    DOCUMENTED = [
        "ODMBuilder", "open_odm", "open_define",
        "permissive", "ValidationMode", "get_mode", "set_mode",
        "create_oid_checker", "DynamicOIDRef",
        "OdmlibError", "OdmlibValidationError", "OdmlibRequiredAttributeError",
        "OdmlibOIDError", "OdmlibConformanceError", "OdmlibElementOrderError",
        "OdmlibErrorLimitError", "OdmlibSchemaValidationError", "OdmlibTypeError",
        "OdmlibParsingError", "OdmlibLoaderStateError", "OdmlibSerializationError",
        "OdmlibNamespaceError", "OdmlibWarning", "OdmlibDeprecationWarning",
        "OdmlibInteroperabilityWarning", "ErrorCollector", "ErrorReporting",
        "is_collecting_checker", "flatten_cerberus_errors",
    ]

    # Imported on first access via the PEP 562 module __getattr__.
    LAZY = [
        "DatasetJSON", "Column", "SourceSystem",
        "DefineFlattener", "DefineBuilder",
        "dataset_xml_to_dataset_json", "dataset_json_to_dataset_xml",
    ]

    def test_documented_names_importable(self):
        import odmlib
        for name in self.DOCUMENTED:
            with self.subTest(name=name):
                self.assertTrue(hasattr(odmlib, name))

    def test_lazy_names_importable(self):
        import odmlib
        for name in self.LAZY:
            with self.subTest(name=name):
                self.assertTrue(hasattr(odmlib, name))

    def test_all_covers_documented_and_lazy(self):
        """``__all__`` must advertise the whole documented surface."""
        import odmlib
        exported = set(odmlib.__all__)
        for name in self.DOCUMENTED + self.LAZY:
            with self.subTest(name=name):
                self.assertIn(name, exported)

    def test_lazy_names_visible_to_dir(self):
        """Lazy names stay out of the module dict, so ``__dir__`` must list them."""
        import odmlib
        listed = dir(odmlib)
        for name in self.LAZY:
            with self.subTest(name=name):
                self.assertIn(name, listed)

    def test_every_all_entry_resolves(self):
        import odmlib
        for name in odmlib.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(odmlib, name))

    def test_version_string_available(self):
        import odmlib
        self.assertIsInstance(odmlib.__version__, str)
        self.assertTrue(odmlib.__version__)


# ---------------------------------------------------------------------------
# Bundled XSD schema pairs
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestSchemaPairs(TestCase):
    """The six ``(standard, version)`` pairs the skill lists, and their files."""

    EXPECTED_PAIRS = {
        ("odm", "1.3.2"),
        ("odm", "2.0"),
        ("define", "2.0"),
        ("define", "2.1"),
        ("arm", "1.0"),
        ("arm", "1.0-define2.1"),
    }

    def test_pairs_match_skill(self):
        from odmlib.schema_manager import _MAIN_SCHEMA
        self.assertEqual(set(_MAIN_SCHEMA), self.EXPECTED_PAIRS)

    def test_each_pair_resolves_to_a_file(self):
        """A key that does not match its on-disk directory fails only at
        validation time -- so check every one resolves now."""
        import odmlib.schema_manager as SM
        for standard, version in sorted(self.EXPECTED_PAIRS):
            with self.subTest(standard=standard, version=version):
                path = SM.get_schema_path(standard, version)
                self.assertTrue(os.path.isfile(path), f"missing schema file: {path}")


# ---------------------------------------------------------------------------
# List-vs-object shape rule
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestStudyShapeRule(TestCase):
    """ODM nests Study/MetaDataVersion in lists; Define-XML and ARM do not.

    ``ODMListObject`` subclasses ``ODMObject``, so these use exact type
    comparison -- ``isinstance`` would pass for both and prove nothing.
    """

    def test_odm_132_study_and_mdv_are_lists(self):
        import odmlib.odm_1_3_2.model as ODM
        import odmlib.typed as T
        self.assertIs(type(ODM.ODM._elems["Study"]), T.ODMListObject)
        self.assertIs(type(ODM.Study._elems["MetaDataVersion"]), T.ODMListObject)

    def test_define_21_study_and_mdv_are_single_objects(self):
        import odmlib.define_2_1.model as DEFINE
        import odmlib.typed as T
        self.assertIs(type(DEFINE.ODM._elems["Study"]), T.ODMObject)
        self.assertIs(type(DEFINE.Study._elems["MetaDataVersion"]), T.ODMObject)

    def test_arm_10_study_and_mdv_are_single_objects(self):
        import odmlib.arm_1_0.model as ARM
        import odmlib.typed as T
        self.assertIs(type(ARM.ODM._elems["Study"]), T.ODMObject)
        self.assertIs(type(ARM.Study._elems["MetaDataVersion"]), T.ODMObject)


# ---------------------------------------------------------------------------
# Return types
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestUnreferencedOidsReturnType(TestCase):
    """``unreferenced_oids()`` returns a dict of orphan OID -> ref attribute."""

    DEFINE_FILE = os.path.join(REPO_ROOT, "tests", "data", "defineV21-SDTM.xml")

    def test_annotation_says_dict(self):
        from odmlib.odm_element import ODMElement
        annotation = inspect.signature(ODMElement.unreferenced_oids).return_annotation
        self.assertIn("dict", str(annotation))

    @skipIf(not os.path.isfile(DEFINE_FILE), "test Define-XML file not available")
    def test_returns_a_dict_at_runtime(self):
        import odmlib.define_loader as DL
        import odmlib.loader as LD
        from odmlib import create_oid_checker

        loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
        loader.open_odm_document(self.DEFINE_FILE)
        odm = loader.root()
        orphans = odm.unreferenced_oids(create_oid_checker("define_2_1"))
        self.assertIsInstance(orphans, dict)


# ---------------------------------------------------------------------------
# Cross-file links
# ---------------------------------------------------------------------------

@skipIf(NO_SKILL, SKILL_REASON)
class TestCrossFileLinks(TestCase):
    """Every path SKILL.md names must resolve, or the skill sends readers nowhere."""

    @classmethod
    def setUpClass(cls):
        cls.text = read_skill_md()

    def _referenced(self, pattern):
        return sorted(set(re.findall(pattern, self.text)))

    def test_reference_files_exist(self):
        names = self._referenced(r"references/([\w.-]+\.md)")
        self.assertTrue(names, "SKILL.md should point at its reference files")
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(os.path.isfile(os.path.join(REFERENCES_DIR, name)))

    def test_example_files_exist(self):
        names = self._referenced(r"examples/([\w.-]+\.py)")
        self.assertTrue(names, "SKILL.md should point at its examples")
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(
                    os.path.isfile(os.path.join(SKILL_DIR, "examples", name)))

    def test_repo_test_files_exist(self):
        """SKILL.md cites repo tests as worked examples; those must exist too."""
        names = self._referenced(r"tests/([\w.-]+\.py)")
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(
                    os.path.isfile(os.path.join(REPO_ROOT, "tests", name)))
