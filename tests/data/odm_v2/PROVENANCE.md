# Vendored ODM v2.0 fixtures: provenance and licences

This directory holds 25 ODM v2.0 documents, each as an XML + JSON pair, and an
OID-reference oracle. They were copied from the **odm-v2** Claude Code skill
(`.claude/skills/odm-v2/examples/` in its own repository) so that odmlib's tests do
not depend on a sibling checkout. Every XML file validates against the official
ODM v2.0 XSD bundled at `odmlib/schemas/odm/2.0/`.

`MANIFEST.json` records, for each file, its source path, its sha256 and the odm-v2
commit it was copied from. For each fixture it also records the status (`verbatim`,
or `corrected` with the corrections listed), the tool that produced the JSON
(`odmlib`, or odm-v2's `odm_json.py` where odmlib has no class for an element), and
the licence. This file is the only one maintained by hand. Everything else is
written by:

```bash
python scripts/sync_odm_v2_fixtures.py --source <odm-v2>/.claude/skills/odm-v2/examples
python scripts/sync_odm_v2_fixtures.py --check --source <same path>   # drift report, writes nothing
```

`tests/test_vendored_fixtures.py` checks the hashes, the XSD validity, the oracle and
the known OID findings without needing the odm-v2 checkout. Do not edit a fixture in
place: fix it in odm-v2 and resync, or the hash check fails.

`.gitattributes` marks this directory `-text`, so git never converts line endings and
a Windows checkout stays byte-identical to the recorded hashes.

## What is here

| Directory | Fixtures | Origin |
|---|---|---|
| `templates/` | 4 | Hand-written odm-v2 starters: two ClinicalData files (snapshot and transactional) and two metadata files (study design, study metadata). |
| `spec/` | 5 | The full documents among the ODM v2.0 specification's examples: three with ClinicalData (nested ItemGroupData for a multiple selection, and the two Query examples), plus HL7 FHIR Integration and the File Conformity prolog. |
| `github/` | 16 | Every example in cdisc-org/DataExchange-ODM `examples/` that validates. Nine are ODM documents (seven contain ClinicalData), and seven are rooted at `MetaDataVersion`. Not vendored: two ODM 1.3.2 files, and `FHIR_Integration/Data_Retrieval_From_FHIR_in_ODM.xml`, which fails the XSD. |
| `ref_targets.json` | 1 | Each element's `ref_targets` from odm-v2's `model/odm-v2.0.json`: the element types the ODM v2.0 spec lets each OID-reference attribute point at. It was built independently of odmlib, and the tests compare `create_oid_checker("odm_2_0")` against it. |

Twelve fixtures contain `ClinicalData`; `MANIFEST.json` flags them with
`has_clinical_data`. Until odmlib models the ODM v2.0 data layer (v0.3.0 plan, P4),
loading drops their ClinicalData.

## Sources and licences

### odm-v2 (templates, all JSON files, the spec corrections, `ref_targets.json`)

The templates, every JSON file in this directory, the corrections applied to
`corrected` spec examples, and `ref_targets.json` come from the odm-v2 skill:

```
The MIT License (MIT)

Copyright © 2022-2026 Sam Hume

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the “Software”), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
```

### cdisc-org/DataExchange-ODM (`github/*.xml`)

The XML files under `github/` are byte-identical to the files of the same path under
`examples/` in <https://github.com/cdisc-org/DataExchange-ODM>. This was checked
against commit `6cb00a9` on 2026-11-26. Each fixture's `upstream` field in
`MANIFEST.json` gives the original path.

```
MIT License

Copyright (c) 2022 cdisc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### CDISC ODM v2.0 specification (`spec/*.xml`)

The XML files under `spec/` reproduce examples from the **CDISC Operational Data
Model (ODM) v2.0** specification, as published on the CDISC wiki (export dated
2026-10-16/18). Copyright © CDISC. They are included with attribution, for testing
conformance to the standard. Each fixture's `appears_in` field in `MANIFEST.json`
names the specification page and code block it was taken from. Where the
specification's example did not validate against the ODM v2.0 XSD, odm-v2 applied
the minimum corrections needed; `MANIFEST.json` lists them under `fixes`, and those
corrections are odm-v2's (MIT, above). These files are not a normative copy of the
specification. Consult the specification itself for the authoritative text.

## Known content issues

These are deliberate: they are the upstream content as published.

- **Dangling OID references.** `tests/test_vendored_fixtures.py` pins the number of
  OID findings per file. In the GitHub examples, Columbia has 11 unresolved
  references and 1 duplicate OID, `fhir-example` has 9 unresolved `ItemOID`s,
  `Inclusion_Exclusion_Simple_Workflow` has 1 unresolved reference, 1 reference to
  the wrong element type and 1 duplicate OID, and `Conditional_Repeats` and
  `Timing_LZZT` have 1 unresolved reference each. Spec examples are often
  partial, so `hl7-fhir-integration` and the nested-ItemGroupData example also
  reference definitions they do not contain. The two ClinicalData templates
  reference a study defined in another file. These counts cover metadata references
  only until odmlib models ClinicalData (P4).
