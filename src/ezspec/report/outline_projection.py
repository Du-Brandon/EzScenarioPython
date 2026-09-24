"""Project collected row-wise outlines into legacy and execution reports."""

from __future__ import annotations

import copy
import json
from typing import Any

from ezspec.keyword import Feature

from .dto import FeatureDto
from .i18n import get_gherkin_keywords


def merged_feature_dict(feature: Feature, execution: dict[str, Any]) -> dict[str, Any]:
    """Keep the Java JSON shape while adding actually started outline rows."""

    result = FeatureDto.from_feature(feature).to_dict()
    rules = result["ruleDtos"]
    assert isinstance(rules, list)
    items = {item["nodeId"]: item for item in execution["items"]}
    for group in execution["groups"]:
        template = group["template"] or {}
        rule_name = template.get("rule", group["declaredRule"])
        target = next((rule for rule in rules if rule["name"] == rule_name), rules[0])
        runtime_scenarios = []
        for node_id in group["nodeIds"]:
            for attempt in items[node_id]["attempts"]:
                runtime = attempt["runtimeScenarioDto"]
                if attempt["started"] and runtime is not None:
                    runtime_scenarios.append(copy.deepcopy(runtime))
        raw_steps = [
            {
                "keyword": step["keyword"],
                "description": step["description"],
                "stepExecutionOutcome": "Pending",
                "errorMessage": "",
                "exception": "",
                "stackTrace": "",
                "continuousAfterFailure": step["continuousAfterFailure"],
            }
            for step in template.get("steps", ())
        ]
        target["specificationElementDtos"].append(
            {
                "@class": "ScenarioOutlineDto",
                "keyword": "Scenario Outline",
                "name": template.get("name", group["method"].rsplit(".", 1)[-1]),
                "rawStepDtos": raw_steps,
                "allExampleDtos": copy.deepcopy(group["examples"]),
                "runtimeScenarioDtos": runtime_scenarios,
            }
        )
    return result


def render_outline_text(execution: dict[str, Any], *, language: str) -> str:
    """Show scope and each selected row without implying unselected success."""

    keywords = get_gherkin_keywords(language)
    items = {item["nodeId"]: item for item in execution["items"]}
    lines = [
        "逐列執行範圍: "
        f"共 {execution['totalRows']} 列／"
        f"選取 {execution['selectedRows']} 列／"
        f"開始 {execution['startedRows']} 列／"
        f"完成 {execution['completedRows']} 列"
    ]
    for group in execution["groups"]:
        template = group["template"] or {}
        name = template.get("name", group["method"].rsplit(".", 1)[-1])
        rule_name = template.get("rule", group["declaredRule"])
        lines.extend(
            (
                "",
                f"{keywords.getI18nKeyword('Rule')}: {rule_name or '(default)'}",
                f"{keywords.getI18nKeyword('Scenario Outline')}: {name}",
                f"Source: {group['method']}",
            )
        )
        if group["parameters"]:
            parameters = json.dumps(group["parameters"], ensure_ascii=False, sort_keys=True)
            lines.append(f"pytest parameters: {parameters}")
        if template.get("description"):
            lines.append(template["description"])
        for step in template.get("steps", ()):
            lines.append(
                f"{keywords.getI18nKeyword(step['keyword'])} {step['description']}".rstrip()
            )
        for example in group["examples"]:
            label = example["name"]
            lines.append(f"{keywords.getI18nKeyword('Examples')}: {label}".rstrip())
            if example["description"]:
                lines.append(example["description"])
            table = example["tableDto"]
            header = table["headerDto"]["header"]
            lines.append("| " + " | ".join(header) + " |")
            for row in table["rows"]:
                lines.append("| " + " | ".join(row["columns"]) + " |")
        group_items = [items[node_id] for node_id in group["nodeIds"]]
        if all(item["index"] is None for item in group_items):
            lines.append("0 列，未執行步驟")
        for item in group_items:
            if not item["selected"]:
                continue
            if item["index"] is not None:
                lines.append(f"[{item['index'] + 1}] {item['id']}  輸入 {item['inputs']}")
            for attempt in item["attempts"]:
                runtime = attempt["runtimeScenarioDto"]
                if runtime is not None:
                    for step in runtime["stepDtos"]:
                        lines.append(
                            f"  [{step['stepExecutionOutcome']}] "
                            f"{keywords.getI18nKeyword(step['keyword'])} "
                            f"{step['description']}".rstrip()
                        )
                for phase, outcome in attempt["phases"].items():
                    if outcome["outcome"] != "passed":
                        lines.append(f"  pytest {phase}: {outcome['outcome']}")
            if not item["attempts"]:
                lines.append("  未開始")
    return "\n".join(lines)


def render_execution_json(execution: dict[str, Any]) -> str:
    return json.dumps(execution, ensure_ascii=False, indent=2)
