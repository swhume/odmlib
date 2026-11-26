"""Smoke test for a PyInstaller-frozen odmlib (issue #37).

CI freezes this script with plain ``pyinstaller --onefile smoke.py`` -- no
``--collect-data`` or ``--hidden-import`` flags -- and runs the binary. Each step needs
something only odmlib's hook provides:

1. a valueset lookup reads ``odmlib/data/valuesets.json``;
2. ``ODMSchemaValidator`` compiles the bundled ODM 2.0 XSD, which pulls in its
   ``xs:include`` files;
3. loading an ODM 2.0 document imports ``odmlib.odm_2_0.model`` by name, which static
   analysis cannot see.

Not collected by pytest (no ``test_`` prefix). Run it directly to check an
unfrozen install: ``python tests/pyinstaller/smoke.py``.
"""
import sys

DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<ODM xmlns="http://www.cdisc.org/ns/odm/v2.0" FileOID="SMOKE.1" FileType="Snapshot"
     Granularity="Metadata" ODMVersion="2.0" CreationDateTime="2026-11-26T12:00:00">
  <Study OID="ST.SMOKE" StudyName="Smoke" ProtocolName="Smoke">
    <MetaDataVersion OID="MDV.1" Name="MDV 1">
      <ItemGroupDef OID="IG.DM" Name="Demographics" Repeating="No" Type="Form">
        <ItemRef ItemOID="IT.AGE" Mandatory="Yes"/>
      </ItemGroupDef>
      <ItemDef OID="IT.AGE" Name="Age" DataType="integer"/>
    </MetaDataVersion>
  </Study>
</ODM>
"""


def main():
    from odmlib.valueset import ValueSet
    data_types = ValueSet.value_set("ItemDef.DataType", version="odm_2_0")
    assert "integer" in data_types, data_types
    print("valuesets.json: ok")

    from odmlib.odm_parser import ODMSchemaValidator
    import xml.etree.ElementTree as ET
    validator = ODMSchemaValidator(standard="odm", version="2.0")
    errors = list(validator.xsd.iter_errors(ET.fromstring(DOCUMENT.encode("utf-8"))))
    assert errors == [], errors
    print("ODM 2.0 XSD: ok")

    import odmlib.loader as LD
    import odmlib.odm_loader as OL
    loader = LD.ODMLoader(OL.XMLODMLoader(model_package="odm_2_0"))
    loader.load_odm_string(DOCUMENT)
    mdv = loader.MetaDataVersion()
    assert mdv.ItemDef[0].OID == "IT.AGE", mdv.ItemDef
    print("ODM 2.0 load: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
