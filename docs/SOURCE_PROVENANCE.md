# Source provenance

Recorded on 2026-09-24. EzScenarioPython is an independently maintained Python
adaptation of [ezSpec](https://gitlab.com/TeddyChen/ezspec), developed by Teddy
Chen and the ezKanban Team. It is not an upstream ezSpec release. See the root
[NOTICE](../NOTICE) for attribution and [LICENSE](../LICENSE) for Apache-2.0.

## Reference and licensing evidence

The reference is [commit
`061eadc8dd47510bf12d62dd87d3fdaa0a37b20d`](https://gitlab.com/TeddyChen/ezspec/-/tree/061eadc8dd47510bf12d62dd87d3fdaa0a37b20d).
Its root `pom.xml` declares revision `2.0.5`, Apache License 2.0 in its
`licenses` section, and Teddy Chen and ezKanban Team in its `developers`
section. The commit identifier, rather than a release label, pins the source
used for this inventory.

The tracked tree at that commit contains no root LICENSE or NOTICE file.
The licensing declaration recorded here comes from `pom.xml`; this project's
NOTICE was written for the Python adaptation, not copied from an upstream
NOTICE. Java files identified below contain author annotations, but the
reviewed Java sources do not supply copyright years to reproduce. No years or
additional copyright ownership claims have been inferred.

All Java paths in the tables are relative to the indicated module's Java
package root. All Python paths are relative to this repository. The mappings
describe origins and reference material; they do not assert line-for-line
translation.

## Core adaptations

Java package root: `ezspec-core/src/main/java/tw/teddysoft/ezspec/`.
Every Java source listed in this table has an `@author Teddy Chen` annotation.
The Python modules retain that attribution and identify the adaptation.

| Python path | Java source | Python changes |
| --- | --- | --- |
| `src/ezspec/keyword/argument.py` | `keyword/Argument.java` | Python parsing, values, and type conversions |
| `src/ezspec/keyword/environment.py` | `keyword/ScenarioEnvironment.java` | Python execution context and value access |
| `src/ezspec/keyword/examples.py` | `keyword/Example.java`, `keyword/Examples.java` | Python table sources and model APIs |
| `src/ezspec/keyword/feature.py` | `keyword/Feature.java` | Python Feature model and declarative outline entry point |
| `src/ezspec/keyword/rule.py` | `keyword/Rule.java`, `keyword/Background.java` | Python Rule selection and background execution |
| `src/ezspec/keyword/result.py` | `keyword/Result.java`, `keyword/StepExecutionOutcome.java` | Python outcomes and exception formatting |
| `src/ezspec/keyword/scenario.py` | `keyword/Scenario.java`, `keyword/RuntimeScenario.java` | Python callback execution, exceptions, and thread execution |
| `src/ezspec/keyword/scenario_outline.py` | `keyword/ScenarioOutline.java` | Python outline execution and shared per-case construction |
| `src/ezspec/keyword/registration.py` | `keyword/RuntimeScenario.java` | DSL registration extracted from the Python adaptation into a shared mixin |
| `src/ezspec/keyword/step.py` | `keyword/Step.java`, `Given.java`, `When.java`, `Then.java`, `And.java`, `But.java`, `ThenSuccess.java`, `ThenFailure.java`, `ConcurrentGroup.java` (all under `keyword/`) | Python step classes, callbacks, and concurrency-group markers |
| `src/ezspec/keyword/table/models.py` | `keyword/table/Header.java`, `Row.java`, `Table.java` | Python table parsing and data access |
| `src/ezspec/keyword/visitor/protocols.py` | `keyword/visitor/SpecificationElement.java`, `SpecificationElementVisitor.java` | Python protocols in place of Java interfaces |
| `src/ezspec/exception/errors.py` | `exception/EzSpecError.java`, `PendingException.java` | Python exception classes and aggregated errors |
| `src/ezspec/extension/utils.py` | `extension/SpecUtils.java` | Python formatting helpers |
| `src/ezspec/extension/pytest/examples.py` | `extension/junit5/Junit5Examples.java` | pytest parameter data instead of JUnit argument providers |

Other core references have no file-level author annotation in the inspected
files. Project-level attribution remains in NOTICE:

| Python path | Java source | Python changes |
| --- | --- | --- |
| `src/ezspec/extension/pytest/decorators.py` | `EzFeature.java`; `extension/junit5/EzRule.java`, `EzScenario.java`, `EzScenarioOutline.java`, `EzDynamicScenario.java`, `EzDynamicScenarioOutline.java` | Python decorators, pytest metadata, Rule context, and collection-time Examples |
| `src/ezspec/tags.py` | `EzSpecTag.java`, `LivingDoc.java` | Python constants |

## Reporting references

Java package root: `ezspec-report/src/main/java/tw/teddysoft/ezspec/`.

| Python path | Java source or reference | Attribution and changes |
| --- | --- | --- |
| `src/ezspec/report/plain_text.py` | `visitor/PlainTextReport.java` | Java author: Teddy Chen. Adapted to Python rendering and error presentation |
| `src/ezspec/report/dto.py` | `report/SpecificationElementDto.java`, `FeatureDto.java`, `RuleDto.java`, `BackgroundDto.java`, `ScenarioDto.java`, `ScenarioOutlineDto.java`, `StepDto.java`, `ExampleDto.java`, `TableDto.java`, `HeaderDto.java`, `RowDto.java` | No file-level author annotation observed. Java schema adapted to Python dataclasses and protocols |
| `src/ezspec/report/decorators.py` | `EzFeatureReport.java`, `report/DisableEzSpecReport.java`, `report/EzSpecReportFormat.java` | No file-level author annotation observed. Python decorators and configuration |
| `src/ezspec/report/generator.py`, `src/ezspec/extension/pytest/reporting.py` | `extension/junit5/EzSpecReportExtension.java` | Java reference author: Teddy Chen. Report lifecycle and output behavior reimplemented for pytest and Python |
| `src/ezspec/report/i18n.py` | `i18n/GherkinKeywords.java` and English/Traditional Chinese report vocabulary | No file-level author annotation observed. Small Python keyword catalogue rather than the complete Java resource |
| `src/ezspec/report/json_report.py` | DTO schema listed above | Python standard-library `json` implementation. It does not port the Jackson mapper in `util/Json.java` |

The Java `util/Json.java` reference names Teddy Chen and ezKanban team as
authors. Its Jackson implementation is not included here. Likewise, the
Java reference's React dashboard bundle and its React license file are not
distributed in this project. The complete `gherkin-languages.json` resource
is not included; the Python report catalogue contains only its supported
English and Traditional Chinese display vocabulary. Revisit provenance if
additional upstream resources or dashboard assets are imported.

## Executable examples

Java package root: `ezspec-sample/src/test/java/tw/teddysoft/ezspec/`.
No file-level author annotations were observed in these four Java examples;
the project's authors are acknowledged in NOTICE.

| Python path | Java source |
| --- | --- |
| `examples/default_rule/test_scenario_example.py` | `example/defaultrule/ScenarioExample.java` |
| `examples/default_rule/test_scenario_outline_example.py` | `example/defaultrule/ScenarioOutlineExample.java` |
| `examples/rules/test_scenario_example.py` | `example/rules/ScenarioExample.java` |
| `examples/rules/test_scenario_outline_example.py` | `example/rules/ScenarioOutlineExample.java` |

The examples use Python assertions and pytest decorators. Outline methods now
declare Examples at collection time and return an outline definition; these
changes allow independent selection and rerunning of each row.

## Python-specific implementation and audit limits

`keyword/case.py`, `keyword/definition.py`, the pytest collection/execution/
registry/compatibility modules, and `report/outline_projection.py` implement
the Python collection and reporting architecture. They are not identified as
direct translations of individual Java source files. Compatibility re-export
modules and package initializers organize the Python API.

This inventory checks source identities, file-level attribution, and
representative implementation relationships. It is not an exhaustive
line-by-line comparison or legal review. Tests and documentation include
behavior and vocabulary informed by the Java reference, but their complete
textual provenance has not been audited individually. Do not interpret this
inventory as verification of upstream ownership or of every third-party
component in upstream Java dependencies.
