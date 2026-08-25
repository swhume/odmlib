#!/usr/bin/env python3
"""Repack the odmlib Claude Code skill into its distributable ``.skill`` bundle.

``.claude/skills/odmlib.skill`` is a zip of ``.claude/skills/odmlib/``, rooted
at ``odmlib/``.  It has to be rebuilt whenever SKILL.md, a reference, or an
example changes -- otherwise the bundle ships stale content that no longer
matches the source tree.  ``tests/test_skill_bundle.py`` fails when the two
drift apart; this script is the fix for that failure.

Usage::

    python scripts/build_skill_bundle.py            # rebuild the bundle
    python scripts/build_skill_bundle.py --check    # report drift, write nothing

``--check`` exits 1 when the bundle is out of date, so it can gate CI.

Members are stored uncompressed with a fixed timestamp, so rebuilding
unchanged content produces a byte-identical bundle and does not churn diffs.
"""
import argparse
import hashlib
import os
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib")
BUNDLE_PATH = os.path.join(REPO_ROOT, ".claude", "skills", "odmlib.skill")
ROOT_PREFIX = "odmlib"

# Never ship these, whatever the source tree happens to contain.
EXCLUDED_DIRS = {"__pycache__", ".git", ".pytest_cache", ".ipynb_checkpoints"}
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".swp", ".orig", ".rej")
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db"}

# Fixed zip timestamp (the format's own epoch) keeps rebuilds reproducible.
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def iter_source_files(source_dir=SOURCE_DIR):
    """Yield bundle-relative paths (POSIX separators), sorted, excluding junk."""
    collected = []
    for current_root, dirnames, filenames in os.walk(source_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDED_DIRS)
        for filename in sorted(filenames):
            if filename in EXCLUDED_NAMES or filename.endswith(EXCLUDED_SUFFIXES):
                continue
            absolute = os.path.join(current_root, filename)
            relative = os.path.relpath(absolute, source_dir)
            collected.append(relative.replace(os.sep, "/"))
    return sorted(collected)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def source_digests(source_dir=SOURCE_DIR):
    """``{bundle_relative_path: sha256}`` for the source tree."""
    digests = {}
    for relative in iter_source_files(source_dir):
        with open(os.path.join(source_dir, relative), "rb") as handle:
            digests[relative] = sha256_bytes(handle.read())
    return digests


def bundle_digests(bundle_path=BUNDLE_PATH):
    """``{bundle_relative_path: sha256}`` for the packed bundle."""
    digests = {}
    with zipfile.ZipFile(bundle_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if not name.startswith(ROOT_PREFIX + "/"):
                raise ValueError(
                    f"bundle member {name!r} is not rooted at {ROOT_PREFIX}/")
            digests[name[len(ROOT_PREFIX) + 1:]] = sha256_bytes(archive.read(info))
    return digests


def diff(source, bundle):
    """``(missing_from_bundle, extra_in_bundle, content_mismatches)``."""
    missing = sorted(set(source) - set(bundle))
    extra = sorted(set(bundle) - set(source))
    changed = sorted(p for p in set(source) & set(bundle) if source[p] != bundle[p])
    return missing, extra, changed


def build(source_dir=SOURCE_DIR, bundle_path=BUNDLE_PATH):
    """Write the bundle from the source tree.  Returns the file count."""
    relatives = iter_source_files(source_dir)
    if not relatives:
        raise SystemExit(f"no files found under {source_dir}")

    directories = sorted({
        os.path.dirname(rel) for rel in relatives if os.path.dirname(rel)
    })

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_STORED) as archive:
        root_info = zipfile.ZipInfo(ROOT_PREFIX + "/", FIXED_TIMESTAMP)
        root_info.external_attr = (0o40775 << 16) | 0x10
        archive.writestr(root_info, b"")

        for directory in directories:
            info = zipfile.ZipInfo(f"{ROOT_PREFIX}/{directory}/", FIXED_TIMESTAMP)
            info.external_attr = (0o40775 << 16) | 0x10
            archive.writestr(info, b"")

        for relative in relatives:
            with open(os.path.join(source_dir, relative), "rb") as handle:
                payload = handle.read()
            info = zipfile.ZipInfo(f"{ROOT_PREFIX}/{relative}", FIXED_TIMESTAMP)
            info.external_attr = 0o100664 << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, payload)

    return len(relatives)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report drift and exit 1 if stale; write nothing")
    args = parser.parse_args(argv)

    if not os.path.isdir(SOURCE_DIR):
        raise SystemExit(f"skill source directory not found: {SOURCE_DIR}")

    if args.check:
        if not os.path.isfile(BUNDLE_PATH):
            print(f"bundle missing: {BUNDLE_PATH}")
            return 1
        missing, extra, changed = diff(source_digests(), bundle_digests())
        if not (missing or extra or changed):
            print(f"bundle is up to date ({len(source_digests())} files)")
            return 0
        for path in missing:
            print(f"  missing from bundle: {path}")
        for path in extra:
            print(f"  stale member in bundle: {path}")
        for path in changed:
            print(f"  content differs: {path}")
        print("\nrun: python scripts/build_skill_bundle.py")
        return 1

    count = build()
    missing, extra, changed = diff(source_digests(), bundle_digests())
    if missing or extra or changed:
        raise SystemExit("bundle verification failed immediately after build")
    size = os.path.getsize(BUNDLE_PATH)
    print(f"wrote {BUNDLE_PATH} ({count} files, {size} bytes) -- verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
