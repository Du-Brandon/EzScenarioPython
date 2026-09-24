# Executable examples

These examples are the Python counterpart of the Java `ezspec-sample` module.
They are executable pytest specifications rather than a separately published
package.

```powershell
python -m pytest examples -q
```

The four source examples cover:

- scenarios using the default Rule;
- scenario outlines using the default Rule;
- scenarios assigned to a named Rule;
- scenario outlines created from a named Rule.

The outline examples demonstrate raw Gherkin tables, `PytestExamples`, lists
of examples, and nested tables. Their `@EzScenarioOutline(examples=...)`
sources are available at collection time, so pytest creates one item per row.
The ordinary Scenario examples keep the original `newScenario().Execute()`
style to demonstrate compatibility.

```powershell
python -m pytest examples --collect-only -q
python -m pytest examples --ezspec-steps
```

Copy a full node id from `--collect-only` and pass it to pytest to rerun one
Outline row. Named Rule outline examples declare the Rule in decorator
metadata and bind the returned definition to the Rule so its Background is
used.

Generate living-documentation reports from the same examples with:

```powershell
python -m pytest examples --ezspec-report
```

The default output directory is `build/ezspec-report/`. The TXT and Java
schema compatible JSON describe the specification; each feature's
`.execution.json` records the selected rows and their run outcomes.
