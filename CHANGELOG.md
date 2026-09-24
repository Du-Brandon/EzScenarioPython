# Changelog

## Unreleased

- Fixed concurrent steps overwriting one another's active arguments and
  anonymous tables, including reserved-key access and active-table aliases.
- Group completion now carries step-local inputs forward in declaration order;
  user context remains shared and full argument history is retained.
- Added per-file adaptation notices and a Java source provenance map.
- Python Feature / Rule / Scenario DSL with pytest decorators, fixtures, and
  standard parametrization support.
- `@EzScenarioOutline(examples=...)` and `Feature.defineScenarioOutline()` for
  collection-time Examples and individually selectable rows.
- Independent runtime state for each Outline row and stable row identifiers.
- Terminal step results, TXT and Java-schema-compatible JSON reports, and an
  execution sidecar that records selection, attempts, and fixture outcomes.
- Explicit errors for unsupported lazy callbacks in the new Outline API.
- Legacy Outline no-Examples behavior retained as a no-op.
- Executable examples, contribution guidance, and a GitHub test workflow.

See the README for known limitations and locally validated environments.
