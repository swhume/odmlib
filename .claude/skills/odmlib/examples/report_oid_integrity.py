"""OID reporting that goes beyond what validate() covers.

`validate(collect_errors=True, oid_checker=...)` now enumerates every duplicate
OID and every bad reference, so it is the right tool for "what is wrong with
this document?". Reach for a custom audit only for what it does NOT report:

  * WHERE each defect lives   -- validate() names the OID, not the element path
                                 that references it
  * unreferenced definitions  -- defined but never used (a quality signal, not
                                 an error, so validate() stays silent)
  * usage lookup              -- build_oid_index().find_all(oid): which objects
                                 carry a given OID
  * inventory                 -- every OID grouped by defining element class

This example does all four by walking the object tree the way odmlib does
internally and driving the OID checker's own static mappings.

Run:  python report_oid_integrity.py
"""
import warnings
from collections import defaultdict

import odmlib
from odmlib import ODMBuilder, create_oid_checker
from odmlib.odm_element import ODMElement

MODEL = "odm_1_3_2"


def messy_document():
    """Five independent OID defects — validate() reports the four that are errors."""
    return (
        ODMBuilder(model_package=MODEL)
        .set_file(FileOID="ODM.MESS", FileType="Snapshot",
                  CreationDateTime="2026-06-30T00:00:00", Granularity="Metadata",
                  ODMVersion="1.3.2", Originator="Hume Data Labs")
        .add_study("ST.1", "Demo", "Demo study", "PROTO-1")
        .add_metadata_version(OID="MDV.1", Name="MDV")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .add_item_ref(ItemOID="IT.AGE", Mandatory="Yes", OrderNumber="1")
        .add_item_ref(ItemOID="IT.GONE1", Mandatory="Yes", OrderNumber="2")   # dangling
        .add_item_ref(ItemOID="IT.GONE2", Mandatory="No", OrderNumber="3")    # dangling
        .add_item_ref(ItemOID="CL.SEX", Mandatory="No", OrderNumber="4")      # wrong target
        .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
        .add_item_def(OID="IT.DUP", Name="A", DataType="text")                # duplicate
        .add_item_def(OID="IT.DUP", Name="B", DataType="text")                # duplicate
        .add_item_def(OID="IT.ORPHAN", Name="Never used", DataType="text")    # unreferenced
        .add_code_list(OID="CL.SEX", Name="Sex", DataType="text")
        .build()
    )


def walk(element, path="", seen=None):
    """Yield (path, element) for element and every ODMElement descendant.

    Mirrors odmlib's internal traversal: iterate the instance __dict__, skip
    private keys, and recurse into ODMElement values and lists of them. Reading
    __dict__ rather than the descriptors is what makes this safe on a document
    loaded in permissive mode, where a required attribute may be unset.
    """
    seen = seen if seen is not None else set()
    if id(element) in seen:
        return
    seen.add(id(element))

    here = path or type(element).__name__
    yield here, element

    for key, value in vars(element).items():
        if key.startswith("_"):
            continue
        if isinstance(value, ODMElement):
            yield from walk(value, f"{here}/{key}", seen)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, ODMElement):
                    yield from walk(item, f"{here}/{key}[{i}]", seen)


def audit(odm, model=MODEL):
    """Return a dict of every OID problem, using the checker's mappings."""
    # A checker ACCUMULATES state and is single-use per document: running
    # verify_oids() twice with the same one reports a bogus "not unique" for every
    # OID (call checker.reset() between runs, or build a fresh one). We only need
    # its static mappings (ref_def/oid_defs/skip_*), which are ready at construction,
    # so this checker is never verified against the document at all.
    checker = create_oid_checker(model)

    # oid_defs: LIST of element class names that define an OID (via their `OID` attr)
    # ref_def:  dict, reference attribute -> element class it must resolve to
    # skip_attr/skip_elem: OID-shaped things that are not refs / not reportable
    defs = defaultdict(list)              # oid value -> [(path, element class)]
    refs = []                             # (path, ref attr, oid value)

    for path, element in walk(odm):
        cls = type(element).__name__
        attrs = vars(element)

        if cls in checker.oid_defs and attrs.get("OID"):
            defs[attrs["OID"]].append((path, cls))

        for attr, value in attrs.items():
            if attr.startswith("_") or not isinstance(value, str):
                continue
            if attr in checker.skip_attr or attr not in checker.ref_def:
                continue
            refs.append((path, attr, value))

    defined = {oid: entries[0][1] for oid, entries in defs.items()}

    duplicates = {oid: entries for oid, entries in defs.items() if len(entries) > 1}
    dangling, wrong_target = [], []
    for path, attr, oid in refs:
        if oid not in defined:
            dangling.append((path, attr, oid))
        elif defined[oid] != checker.ref_def[attr]:
            wrong_target.append((path, attr, oid, defined[oid], checker.ref_def[attr]))

    # Compute orphans from the same walk rather than calling unreferenced_oids():
    # that method re-runs verify_oids() when the checker is not already verified,
    # which on a document with a DUPLICATE OID raises a misleading error naming an
    # OID that is not actually duplicated. (A checker that has been through a
    # collect-mode validate() IS verified, so unreferenced_oids() is safe there --
    # but owning the walk keeps this function independent of that ordering.)
    referenced = {oid for _, _, oid in refs}
    unreferenced = {
        oid: (checker.def_ref.get(cls) or [cls])[0]
        for oid, entries in defs.items()
        for cls in [entries[0][1]]
        if oid not in referenced and cls not in checker.skip_elem
    }

    return {
        "checker": checker,
        "duplicates": duplicates,
        "dangling": dangling,
        "wrong_target": wrong_target,
        "unreferenced": unreferenced,
    }


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)
    odm = messy_document()

    # 1. validate() already enumerates the actual ERRORS — start here.
    errors = odm.validate(collect_errors=True, oid_checker=create_oid_checker(MODEL))
    print(f"\nvalidate(collect_errors=True) -> {len(errors)} error(s):")
    for e in errors:
        print("   ", str(e).splitlines()[0])
    print("    ^ every duplicate and bad reference, but not WHERE they are")

    # 2. The custom audit adds the source path for each defect.
    result = audit(odm)
    total = (len(result["duplicates"]) + len(result["dangling"])
             + len(result["wrong_target"]))
    print(f"\nsame {total} defect(s), located:")

    for oid, entries in result["duplicates"].items():
        where = ", ".join(p for p, _ in entries)
        print(f"    duplicate    {oid} defined {len(entries)}x at {where}")
    for path, attr, oid in result["dangling"]:
        print(f"    dangling     {path}.{attr} -> {oid} (no definition)")
    for path, attr, oid, actual, expected in result["wrong_target"]:
        print(f"    wrong target {path}.{attr} -> {oid} is a {actual}, expected {expected}")

    # 3. Unreferenced is a quality signal, not a defect — validate() stays silent
    # about it. It is noisy under odm_*, whose checker only skips ODM; define_2_1
    # also skips Study/MetaDataVersion/ItemGroupDef, so its results are actionable.
    print("\nunreferenced definitions (validate() does not report these):")
    for oid, expected_ref_attr in result["unreferenced"].items():
        print(f"    {oid} defined but never referenced (expected via {expected_ref_attr})")
    print(f"\n  checker.skip_elem for {MODEL}: {sorted(result['checker'].skip_elem)}")
    print("  -> structural OIDs above are expected noise; filter them or pass")
    print("     extra_skip_elems=['Study','MetaDataVersion'] to create_oid_checker().")

    # 4. Usage lookup: turn any reported OID back into the objects carrying it.
    index = odm.build_oid_index()
    print("\nusage lookup via build_oid_index().find_all(oid):")
    for oid in ("IT.DUP", "IT.AGE"):
        holders = index.find_all(oid)
        kinds = ", ".join(type(o).__name__ for o in holders)
        print(f"    {oid}: {len(holders)} element(s) — {kinds}")

    # 5. Inventory: every OID grouped by the element class that defines it.
    inventory = defaultdict(list)
    for path, element in walk(odm):
        cls = type(element).__name__
        oid = vars(element).get("OID")
        if oid and cls in result["checker"].oid_defs:
            inventory[cls].append(oid)
    print("\nOID inventory by defining element:")
    for cls in sorted(inventory):
        print(f"    {cls:<18} {', '.join(sorted(set(inventory[cls])))}")
