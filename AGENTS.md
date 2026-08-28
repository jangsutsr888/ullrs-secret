# Codex project instructions

## Project overview

- This is a Python 3.10+ CLI for importing hourly weather and estimating
  backcountry snow-surface conditions.
- The public command entry point is `ullrs-secret`; command wiring lives in
  `ullrs_secret/cli.py` and importer registration lives in
  `ullrs_secret/importers/`.
- `core_calc_en.tex` is the editable model derivation. The English PDF is a
  generated reading copy; use the implementation and tests to verify current
  behavior.

## Setup and verification

- Run `make install` for an editable install in `venv/`.
- Run `make test` after changing Python behavior.
- Run `make docs-check` after changing documentation, public commands, data
  formats, chart behavior, or examples.
- Integration tests use live terrain data and regenerate PNGs in `example/`.
  When they are relevant, run
  `ULLRS_SECRET_NO_SHOW=1 make integration_test` and inspect the images.

## Change expectations

- Preserve the standard `WeatherData` JSON contract across all importers.
- Keep the README concise. Put algorithms, complete option references, source
  details, and field interpretation in the Sphinx documentation.
- Update tests and the relevant dedicated documentation page when public
  behavior changes.
- Treat checked-in user changes as intentional and avoid unrelated cleanup.
- Do not present chart output as avalanche, glacier-travel, navigation, or
  route-safety advice.

## Documentation conventions

- Documentation content must be English.
- Keep the built-in Sphinx `classic` theme and the fully expanded global table
  of contents unless the user explicitly requests a redesign.
- Keep each chart command on its own page under `docs/charts/` and each import
  source on its own page under `docs/importers/`.
- Put integration-test chart images on their corresponding chart pages and NWS
  source screenshots on the NWS importer page. Do not restore the retired
  worked-example section or the deleted example Markdown walkthrough.
- Do not edit `docs/_build/` or `docs/_generated/` as source. The latter is
  staged from canonical images by `scripts/prepare_docs_assets.py`.

## Repository-specific skills

- Codex automatically discovers repository skills under
  `.agents/skills/<skill-name>/SKILL.md`.
- Do not add a repository skill unless a focused, recurring workflow needs
  instructions or tooling beyond this file. No repository-specific skill is
  currently required.
