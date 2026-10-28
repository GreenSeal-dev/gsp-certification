# Contributing to GSP

Thank you for helping improve the GreenSeal Green Software Practices (GSP), maintained by [GreenSeal.dev](https://greenseal.dev).

## How to contribute

Contributions are welcome through issues and pull requests:

- **Issues**: report errors, unclear wording, broken links or gaps, or propose new or changed practices. Explain the problem and, where possible, point to evidence or references.
- **Pull requests**: for concrete changes. Keep each pull request focused on one topic and describe what changes and why.

When changing `gsp_requirements.yml`:

- every requirement needs a `levels` field (see the comment at the top of the file)
- new requirement IDs follow `GSP-L<level>-<CATEGORY>-<nn>`, where the level is the one at which the requirement is first introduced
- check that the audit checklist still builds: `python src/convert_cert_2.py`

## How decisions are made

GreenSeal.dev maintains GSP and decides which changes are accepted and in which release they appear. Accepted changes are recorded in [`CHANGELOG.md`](CHANGELOG.md) and released as a new version.

## Licence of contributions

By contributing, you agree that your contributions are licensed under the same licence as the part of the repository they change: [CC BY 4.0](LICENSE) for the practices and documentation, and [MIT](LICENSE-CODE) for the code.
