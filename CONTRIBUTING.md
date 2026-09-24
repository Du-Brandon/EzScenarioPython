# Contributing

EzScenarioPython is experimental. Bug reports, readable examples, and focused
pull requests are welcome. English and Traditional Chinese are both welcome.

## Development

Use Python 3.11 or newer and a virtual environment. From the repository root:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
python -m pytest examples --collect-only -q
```

To inspect the generated documentation:

```text
python -m pytest examples --ezspec-steps --ezspec-report
```

Reports go to `build/ezspec-report/`, which is ignored by Git. Use synthetic
Examples data: inputs, step descriptions, and failure messages can appear in
reports. Do not commit credentials or private production data.

## Reporting problems

Include a small runnable specification, the command used, expected and actual
behavior, and your Python, pytest, and operating-system versions. For security
issues, follow [SECURITY.md](SECURITY.md).

## Pull requests

- Keep changes focused and describe the observable problem and resulting behavior.
- Add a regression test for a behavior fix. pytest adapter changes should exercise
  real collection or execution, not only mocked hooks.
- Keep the core DSL independent of pytest. Put runner integration under
  `src/ezspec/extension/pytest/` and report rendering under `src/ezspec/report/`.
- Preserve the documented legacy API, no-Examples behavior, and report schema
  unless an API change has been discussed explicitly.
- Update examples and documentation when user-facing behavior changes.
- Run relevant tests and the full suite before submitting. State any validation
  you could not run; GitHub CI will check its configured platform matrix.

Contributions are provided under this project's [Apache-2.0 license](LICENSE).
Only submit material you have the right to contribute. Preserve applicable
upstream copyright and attribution notices, identify modifications in adapted
files, and record the source of copied or translated material.
