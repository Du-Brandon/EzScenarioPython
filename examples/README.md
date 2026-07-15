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
of examples, and nested tables.

Generate living-documentation reports from the same examples with:

```powershell
python -m pytest examples --ezspec-report
```

The default output directory is `build/ezspec-report/`.
