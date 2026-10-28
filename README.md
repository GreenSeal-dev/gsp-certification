# GreenSeal Green Software Practices (GSP)

The GreenSeal Green Software Practices (GSP) are an open set of practices for building energy- and resource-efficient software, maintained by [GreenSeal.dev](https://greenseal.dev).

GSP defines weighted, evidence-based requirements for assessing how organisations build and run sustainable software. Requirements are aligned with the lifecycle phases of [ISO/IEC TS 20125-1:2026](https://www.iso.org/standard/86105.html) and are kept in a single YAML file. A small converter turns that file into a scored, protected Excel checklist for audits.

## Framework

Requirements are grouped into five categories:

| Category | Level 2 requirements |
| --- | --- |
| Governance & Culture | 7 |
| Training & Knowledge | 6 |
| Measurement & Observability | 6 |
| Software & Architecture Practices | 8 |
| Continuous Improvement | 5 |

Each requirement includes:

- a requirement statement and rationale
- examples of acceptable evidence
- an assessment scale used for scoring
- a priority (`Core` or `Supporting`) and a weight
- the GSP level(s) it applies to (`levels`)

Requirement IDs follow the pattern `GSP-L<level>-<CATEGORY>-<nn>`, where the level is the one at which the requirement was first introduced (e.g. `GSP-L2-MEA-04`).

## Repository contents

| Path | Description |
| --- | --- |
| `gsp_requirements.yml` | Source of truth for all GSP requirements and levels |
| `src/convert_cert_2.py` | Generates the Excel audit checklist from the YAML |

## Generating an audit checklist

Requires Python 3.13.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Level 2 audit (default) -> GSP_L2_Audit.xlsx
python src/convert_cert_2.py

# Custom input and output paths
python src/convert_cert_2.py --level 2 gsp_requirements.yml my_audit.xlsx
```

The converter also accepts `--level 1`, but no Level 1 requirements have been published yet.

The generated workbook contains:

- **Audit Checklist**: one row per requirement, with an assessment dropdown, a notes field, raw and weighted scores, and a total score. Only the assessment and notes columns are editable.
- **Score_Ref** (hidden): the lookup table behind the scores.

By default, scores are spread linearly from 1.0 for the first option on the assessment scale down to 0.0 for the last. A requirement can define its own `scoring` map to override this.

## Versioning

GSP releases are versioned from v1.0.0 onwards, so audits and references can point to a fixed version. Each release is tagged in this repository, and changes are listed in [`CHANGELOG.md`](CHANGELOG.md).

## How to cite

Citation metadata is in [`CITATION.cff`](CITATION.cff), and GitHub shows it under **Cite this repository**. Please cite the version you used.

```bibtex
@misc{greenseal_gsp,
  author  = {{GreenSeal, Lda.}},
  title   = {GreenSeal Green Software Practices (GSP)},
  version = {1.0.0},
  year    = {2026},
  url     = {https://greenseal.dev}
}
```

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence

The practices and documentation in this repository, including `gsp_requirements.yml`, the Markdown files and the audit checklists generated from them, are licensed under the [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](LICENSE). You are free to use, share and adapt them, including commercially, provided you give attribution to "GreenSeal.dev (https://greenseal.dev)" and indicate if you made changes.

The code in this repository (`src/` and `requirements.txt`) is licensed under the [MIT licence](LICENSE-CODE).

## Trademarks and certification

"GreenSeal", "GreenSeal.dev" and "GSP Certified" are trademarks of GreenSeal, Lda. The licences above do not grant any rights to use these trademarks.

The practices are open, but only GreenSeal.dev can certify organisations or products against GSP. Derivative works must not imply certification or endorsement by GreenSeal.dev.

---

© GreenSeal, Lda. Licensed under CC BY 4.0.
