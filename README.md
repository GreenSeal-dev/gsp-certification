# Green Software Practitioner (GSP) Certification

An open audit framework for assessing how organisations build and run sustainable software.

The Green Software Practitioner (GSP) certification defines a set of weighted, evidence-based requirements that auditors use to evaluate an organisation's software sustainability practices. Requirements are aligned with the lifecycle phases of [ISO/IEC TS 20125-1:2026](https://www.iso.org/) and are kept in a single YAML file. A small converter turns that file into a scored, protected Excel checklist for audits.

More information: [greenseal.dev](https://greenseal.dev)

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
- the certification level(s) it applies to (`levels`)

Requirement IDs follow the pattern `GSP-L<level>-<CATEGORY>-<nn>`, where the level is the one at which the requirement was first introduced (e.g. `GSP-L2-MEA-04`).

## Repository contents

| Path | Description |
| --- | --- |
| `gsp_requirements.yml` | Source of truth for all requirements and levels |
| `src/convert_cert_2.py` | Generates the Excel audit checklist from the YAML |
| `gsp_level2.yml` | Earlier Level 2-only version of the requirements (v0.0.5) |

## Generating an audit checklist

Requires Python 3.13.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Level 2 audit (default) -> GSP_L2_Audit.xlsx
python src/convert_cert_2.py

# Level 1 audit
python src/convert_cert_2.py --level 1

# Custom input and output paths
python src/convert_cert_2.py --level 2 gsp_requirements.yml my_audit.xlsx
```

The generated workbook contains:

- **Audit Checklist**: one row per requirement, with an assessment dropdown, a notes field, raw and weighted scores, and a total score. Only the assessment and notes columns are editable.
- **Score_Ref** (hidden): the lookup table behind the scores.

By default, scores are spread linearly from 1.0 for the first option on the assessment scale down to 0.0 for the last. A requirement can define its own `scoring` map to override this.

## Citation

If you use this framework in your research or practice, please cite it. Citation metadata is in [`CITATION.cff`](CITATION.cff), and GitHub shows it under **Cite this repository**.

```bibtex
@software{cruz_gsp_certification,
  author  = {Cruz, Luís},
  title   = {Green Software Practitioner (GSP) Certification Framework},
  version = {0.1.1},
  year    = {2026},
  url     = {https://github.com/GreenSeal-dev/gsp-certification}
}
```

## License

Copyright © 2026 GreenSeal. All rights reserved.

This repository is shared for reference and citation only. No license is granted to copy, modify or distribute its contents without written permission from GreenSeal.
