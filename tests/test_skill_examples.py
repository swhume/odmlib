"""Every skill example must run clean against the installed odmlib.

``.claude/skills/odmlib/examples/*.py`` are the skill's worked idioms.  They
call the real API, so they are the loudest available guard against drift: if a
signature, default, or return shape changes underneath them, they stop exiting
0 and this fails.

What this does *not* catch is prose drift -- an example whose code is correct
but whose surrounding documentation describes something else.
``tests/test_skill_contract.py`` covers that half.

Examples are discovered by glob, so a newly added one is covered automatically.
Each runs in its own temporary working directory: they write to
``os.getcwd()/odmlib_skill_output/``, so running them from the repository root
would litter it.
"""
import glob
import os
import subprocess
import sys
from unittest import TestCase, skipIf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib", "examples")

# An sdist checkout has no .claude/ directory; skip rather than fail there.
NO_EXAMPLES = not os.path.isdir(EXAMPLES_DIR)
SKIP_REASON = f"skill examples not present at {EXAMPLES_DIR}"

# The eight that exist today.  A lower bound, so an empty or broken glob cannot
# pass silently -- but adding a ninth example needs no change here.
MINIMUM_EXAMPLE_COUNT = 8

# Generous: the whole set runs in a few seconds, so this only trips on a hang.
PER_EXAMPLE_TIMEOUT = 120


def discover_examples():
    return sorted(glob.glob(os.path.join(EXAMPLES_DIR, "*.py")))


@skipIf(NO_EXAMPLES, SKIP_REASON)
class TestSkillExamplesRun(TestCase):

    def test_examples_are_discovered(self):
        """An empty glob would make the execution test vacuously pass."""
        found = discover_examples()
        self.assertGreaterEqual(
            len(found), MINIMUM_EXAMPLE_COUNT,
            f"expected at least {MINIMUM_EXAMPLE_COUNT} examples in "
            f"{EXAMPLES_DIR}, found {len(found)}: "
            f"{[os.path.basename(p) for p in found]}")

    def test_every_example_exits_zero(self):
        import tempfile
        for path in discover_examples():
            name = os.path.basename(path)
            with self.subTest(example=name):
                with tempfile.TemporaryDirectory() as workdir:
                    result = subprocess.run(
                        [sys.executable, path],
                        cwd=workdir,
                        capture_output=True,
                        text=True,
                        timeout=PER_EXAMPLE_TIMEOUT,
                    )
                    self.assertEqual(
                        result.returncode, 0,
                        f"{name} exited {result.returncode}\n"
                        f"--- stdout ---\n{result.stdout}\n"
                        f"--- stderr ---\n{result.stderr}")

    def test_examples_write_nothing_beside_the_script(self):
        """An installed skill directory is read-only on most surfaces.

        Examples must write under the caller's cwd, never next to themselves.
        """
        before = set(os.listdir(EXAMPLES_DIR))
        import tempfile
        with tempfile.TemporaryDirectory() as workdir:
            for path in discover_examples():
                subprocess.run([sys.executable, path], cwd=workdir,
                               capture_output=True, text=True,
                               timeout=PER_EXAMPLE_TIMEOUT)
        after = set(os.listdir(EXAMPLES_DIR))
        self.assertEqual(
            before, after,
            f"examples created files in the skill directory: {sorted(after - before)}")


@skipIf(NO_EXAMPLES, SKIP_REASON)
class TestSkillExampleHygiene(TestCase):
    """Cheap static checks that do not need the examples to run."""

    def test_every_example_compiles(self):
        """A syntax error should report as such, not as a subprocess exit code."""
        for path in discover_examples():
            with self.subTest(example=os.path.basename(path)):
                with open(path, encoding="utf-8") as handle:
                    source = handle.read()
                try:
                    compile(source, path, "exec")
                except SyntaxError as exc:
                    self.fail(f"{os.path.basename(path)} does not compile: {exc}")

    def test_every_example_has_a_docstring(self):
        """The docstring is what a reader sees first; it must exist."""
        import ast
        for path in discover_examples():
            with self.subTest(example=os.path.basename(path)):
                with open(path, encoding="utf-8") as handle:
                    tree = ast.parse(handle.read())
                self.assertIsNotNone(
                    ast.get_docstring(tree),
                    f"{os.path.basename(path)} has no module docstring")
