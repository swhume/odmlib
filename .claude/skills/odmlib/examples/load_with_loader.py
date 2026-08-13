"""Load documents with the explicit loader idiom.

Use the explicit loaders when you need what the facade does not expose: a specific
MetaDataVersion/Study without loading everything, namespace control (ns_uri=), loading
from a string, or the ARM / CT models.

Demonstrates:
  * LD.ODMLoader(OL.XMLODMLoader(...)) for ODM
  * loader.root() vs loader.MetaDataVersion() (an object, NOT a list)
  * loader.load_odm_string(...) to parse from memory
  * the Define-XML variant (set model_package="define_2_1" explicitly)

Run:  python load_with_loader.py   (creates its own input first)
Writes: ./odmlib_skill_output/loader_input.xml (under the current working directory)
"""
import os
import warnings

import odmlib
from odmlib import ODMBuilder
import odmlib.odm_loader as OL
import odmlib.define_loader as DL
import odmlib.loader as LD

# Write beside the caller, never beside this script — an installed skill directory
# is read-only on most deployment surfaces.
OUTDIR = os.path.join(os.getcwd(), "odmlib_skill_output")
os.makedirs(OUTDIR, exist_ok=True)
INPUT = os.path.join(OUTDIR, "loader_input.xml")


def make_input():
    odm = (
        ODMBuilder(model_package="odm_1_3_2")
        .set_file(FileOID="ODM.LD", FileType="Snapshot",
                  CreationDateTime="2026-06-30T00:00:00", Granularity="Metadata",
                  ODMVersion="1.3.2", Originator="Hume Data Labs")
        .add_study("ST.LD", "Loader Demo", "Explicit loader demo", "PROTO-LD")
        .add_metadata_version(OID="MDV.1", Name="MDV")
        .add_item_group_def(OID="IG.DM", Name="Demographics", Repeating="No")
        .add_item_def(OID="IT.AGE", Name="Age", DataType="integer")
        .build()
    )
    odm.write_xml(INPUT)
    return odm


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    print("odmlib", odmlib.__version__)
    source = make_input()

    # --- Load an ODM file via the explicit loader ---
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
    loader.open_odm_document(INPUT)

    odm = loader.root()                 # whole document
    mdv = loader.MetaDataVersion()      # FIRST MetaDataVersion as an object (not a list)
    print("root FileOID =", odm.FileOID)
    print("MetaDataVersion() ->", type(mdv).__name__,
          "| ItemDef count =", len(mdv.ItemDef))

    # find_by walks the subtree for a single match by attribute(s):
    age = mdv.find_by("ItemDef", OID="IT.AGE")
    print("find_by ItemDef OID=IT.AGE ->", age.Name if age else None)

    # --- Parse from a string instead of a file ---
    xml_text = source.to_xml_string()
    loader2 = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_1_3_2"))
    loader2.load_odm_string(xml_text)
    print("from string: FileOID =", loader2.root().FileOID)

    # --- Define-XML variant: the Define loader's own default is define_2_0,
    #     so name the version you mean. (No define file here, just the idiom.) ---
    _define_loader = LD.ODMLoader(DL.XMLDefineLoader(model_package="define_2_1"))
    print("Define loader ready:", type(_define_loader.loader).__name__,
          "(model_package=define_2_1)")
