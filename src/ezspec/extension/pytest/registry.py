"""Session-local, serializable snapshots for row-wise scenario outlines."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any

import pytest

from ezspec.report.dto import ExampleDto, ScenarioDto


_REGISTRY = pytest.StashKey["RunRegistry"]()


def _safe(value: Any) -> Any:
    """Copy values into JSON types without retaining user or pytest objects."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return [_safe(part) for part in value]
    if isinstance(value, dict):
        return {str(key): _safe(part) for key, part in value.items()}
    return repr(value)


def _owner_name(item: Any) -> str:
    owner = getattr(item, "cls", None)
    return f"{owner.__module__}.{owner.__qualname__}" if owner else ""


def _method_name(item: Any) -> str:
    method = getattr(item, "obj", None)
    if method is not None:
        return f"{getattr(method, '__module__', '')}.{getattr(method, '__qualname__', '')}"
    return str(getattr(item, "originalname", None) or getattr(item, "name", ""))


def _parameters(item: Any) -> dict[str, Any]:
    callspec = getattr(item, "callspec", None)
    params = getattr(callspec, "params", {})
    return {name: _safe(value) for name, value in params.items() if name != "_ezspec_case"}


def _group_key(item: Any) -> str:
    parent = getattr(item, "parent", None)
    parent_node_id = getattr(parent, "nodeid", None)
    if parent_node_id is None:
        parent_node_id = str(item.nodeid).rsplit("::", 1)[0]
    method = getattr(item, "originalname", None) or str(item.nodeid).rsplit("::", 1)[-1].split("[", 1)[0]
    callspec = getattr(item, "callspec", None)
    indices = getattr(callspec, "indices", None)
    external_identity = (
        {name: index for name, index in indices.items() if name != "_ezspec_case"}
        if indices is not None
        else _parameters(item)
    )
    return json.dumps(
        [str(parent_node_id), str(method), external_identity],
        ensure_ascii=False,
        sort_keys=True,
    )


def _steps_of(definition: Any) -> tuple[dict[str, Any], ...]:
    steps = definition.steps()
    return tuple(
        {
            "keyword": step.getName(),
            "description": step.description(),
            "continuousAfterFailure": step.isContinuousAfterFailure(),
        }
        for step in steps
    )


def _rule_name(definition: Any) -> str:
    rule = getattr(definition, "rule", None)
    return rule.getName() if rule is not None else ""


def _declared_rule(item: Any) -> str:
    method_metadata = getattr(getattr(item, "obj", None), "__ezspec_metadata__", {})
    rule = method_metadata.get("rule", "")
    if rule:
        return str(rule)
    owner = getattr(item, "cls", None)
    if "rule" in getattr(owner, "__ezspec_kinds__", ()):
        return str(getattr(owner, "__ezspec_metadata__", {}).get("value", ""))
    return ""


@dataclass(slots=True)
class _Group:
    key: str
    owner: str
    method: str
    parameters: dict[str, Any]
    declared_rule: str
    example_dtos: tuple[dict[str, Any], ...]
    node_ids: list[str] = field(default_factory=list)
    template: dict[str, Any] | None = None


@dataclass(slots=True)
class _Item:
    node_id: str
    group_key: str
    example_index: int | None
    row_index: int | None
    index: int | None
    case_id: str | None
    inputs: dict[str, str]
    selected: bool = False
    attempts: list[dict[str, Any]] = field(default_factory=list)


class RunRegistry:
    """Only owns strings, JSON values, and DTO snapshots; no live scenarios."""

    def __init__(self) -> None:
        self._groups: dict[str, _Group] = {}
        self._items: dict[str, _Item] = {}

    def register_item(self, item: Any, catalog: Any, case: Any | None) -> None:
        node_id = str(item.nodeid)
        group_key = _group_key(item)
        group = self._groups.get(group_key)
        if group is None:
            examples = tuple(ExampleDto.of(example).to_dict() for example in catalog.to_examples())
            group = _Group(
                key=group_key,
                owner=_owner_name(item),
                method=_method_name(item),
                parameters=_parameters(item),
                declared_rule=_declared_rule(item),
                example_dtos=examples,
            )
            self._groups[group_key] = group
        elif group.example_dtos != tuple(
            ExampleDto.of(example).to_dict() for example in catalog.to_examples()
        ):
            raise ValueError(f"{node_id}: Examples changed within one outline group")
        if node_id not in group.node_ids:
            group.node_ids.append(node_id)
        if case is None:
            record = _Item(node_id, group_key, None, None, None, None, {})
        else:
            record = _Item(
                node_id,
                group_key,
                case.example_index,
                case.row_index,
                case.index,
                case.id,
                dict(zip(case.headers, case.values, strict=True)),
            )
        self._items[node_id] = record

    def mark_selected(self, items: list[Any]) -> None:
        selected = {str(item.nodeid) for item in items}
        for node_id, record in self._items.items():
            record.selected = node_id in selected

    def _record(self, item: Any) -> _Item | None:
        return self._items.get(str(item.nodeid))

    def begin_attempt(self, item: Any) -> None:
        record = self._record(item)
        if record is None:
            return
        if record.attempts and set(record.attempts[-1]["phases"]) == {"setup"}:
            return
        record.attempts.append(self._new_attempt(record, started=False))

    @staticmethod
    def _new_attempt(record: _Item, *, started: bool) -> dict[str, Any]:
        return {
            "number": len(record.attempts) + 1,
            "started": started,
            "completed": False,
            "phases": {},
            "runtimeScenarioDto": None,
        }

    def validate_definition(self, item: Any, definition: Any) -> None:
        record = self._record(item)
        if record is None:
            return
        group = self._groups[record.group_key]
        owner = getattr(item, "cls", None)
        expected_feature = getattr(owner, "feature", None)
        rule = getattr(definition, "rule", None)
        actual_feature = rule.getFeature() if rule is not None else None
        if expected_feature is not None and actual_feature is not expected_feature:
            raise ValueError(
                f"{record.node_id}: outline definition belongs to a different "
                f"Feature than {group.owner}.feature"
            )
        proposed = {
            "rule": _rule_name(definition),
            "name": definition.getName(),
            "description": definition.getDescription(),
            "steps": list(_steps_of(definition)),
        }
        if group.template is None:
            group.template = proposed
        elif group.template != proposed:
            raise ValueError(
                f"{record.node_id}: outline declaration differs for "
                f"{group.method} with pytest parameters {group.parameters!r}; "
                "Rule, name, description, and step keyword/description/policy "
                "must match across Examples rows"
            )
        if record.index is not None:
            if not record.attempts:
                self.begin_attempt(item)
            record.attempts[-1]["started"] = True

    def record_runtime(self, item: Any, definition: Any, runtime: Any) -> None:
        record = self._record(item)
        if record is None or runtime is None:
            return
        if self._groups[record.group_key].template is None:
            self.validate_definition(item, definition)
        if not record.attempts:
            self.begin_attempt(item)
        record.attempts[-1]["runtimeScenarioDto"] = ScenarioDto.of(runtime).to_dict()

    def record_phase(self, item: Any, report: Any) -> None:
        record = self._record(item)
        if record is None:
            return
        phase = str(report.when)
        if not record.attempts or (phase == "setup" and record.attempts[-1]["phases"]):
            record.attempts.append(self._new_attempt(record, started=False))
        attempt = record.attempts[-1]
        attempt["phases"][phase] = {
            "outcome": str(report.outcome),
            "duration": float(getattr(report, "duration", 0.0)),
            "error": str(getattr(report, "longrepr", "")) if report.failed else "",
        }
        if phase == "teardown":
            attempt["completed"] = "call" in attempt["phases"]

    def format_item_steps(self, item: Any) -> str:
        record = self._record(item)
        if record is None:
            return ""
        group = self._groups[record.group_key]
        if record.index is None:
            lines = [f"{record.node_id}: 0 列，未執行步驟"]
        else:
            name = group.template["name"] if group.template else group.method
            lines = [f"{name} [{record.case_id}]", f"  輸入: {record.inputs}"]
        if record.attempts:
            attempt = record.attempts[-1]
            runtime = attempt["runtimeScenarioDto"]
            if runtime:
                for step in runtime["stepDtos"]:
                    lines.append(
                        f"  [{step['stepExecutionOutcome']}] "
                        f"{step['keyword']} {step['description']}".rstrip()
                    )
            for phase, outcome in attempt["phases"].items():
                if outcome["outcome"] != "passed":
                    lines.append(f"  pytest {phase}: {outcome['outcome']}")
        return "\n".join(lines)

    def owners(self) -> set[str]:
        return {group.owner for group in self._groups.values()}

    def feature_snapshot(self, owner: type[Any]) -> dict[str, Any]:
        owner_name = f"{owner.__module__}.{owner.__qualname__}"
        groups = [group for group in self._groups.values() if group.owner == owner_name]
        records = [self._items[node_id] for group in groups for node_id in group.node_ids]
        return {
            "schemaVersion": 1,
            "feature": owner_name,
            "totalRows": sum(record.index is not None for record in records),
            "selectedRows": sum(record.index is not None and record.selected for record in records),
            "startedRows": sum(record.index is not None and any(a["started"] for a in record.attempts) for record in records),
            "completedRows": sum(record.index is not None and any(a["completed"] for a in record.attempts) for record in records),
            "items": [
                {
                    "nodeId": record.node_id,
                    "group": record.group_key,
                    "exampleIndex": record.example_index,
                    "rowIndex": record.row_index,
                    "index": record.index,
                    "id": record.case_id,
                    "inputs": copy.deepcopy(record.inputs),
                    "selected": record.selected,
                    "started": any(a["started"] for a in record.attempts),
                    "completed": any(a["completed"] for a in record.attempts),
                    "attemptCount": len(record.attempts),
                    "attempts": copy.deepcopy(record.attempts),
                }
                for record in records
            ],
            "groups": [
                {
                    "key": group.key,
                    "method": group.method,
                    "parameters": copy.deepcopy(group.parameters),
                    "declaredRule": group.declared_rule,
                    "template": copy.deepcopy(group.template),
                    "examples": copy.deepcopy(group.example_dtos),
                    "nodeIds": list(group.node_ids),
                }
                for group in groups
            ],
        }


def get_registry(config: Any) -> RunRegistry:
    registry = config.stash.get(_REGISTRY, None)
    if registry is None:
        registry = RunRegistry()
        config.stash[_REGISTRY] = registry
    return registry


def register_item(item: Any, catalog: Any, case: Any | None) -> None:
    get_registry(item.config).register_item(item, catalog, case)


def mark_selected(items: list[Any]) -> None:
    if items:
        get_registry(items[0].config).mark_selected(items)


def begin_attempt(item: Any) -> None:
    get_registry(item.config).begin_attempt(item)


def validate_definition(item: Any, definition: Any) -> None:
    get_registry(item.config).validate_definition(item, definition)


def record_runtime(item: Any, definition: Any, runtime: Any) -> None:
    get_registry(item.config).record_runtime(item, definition, runtime)


def record_phase(item: Any, report: Any) -> None:
    get_registry(item.config).record_phase(item, report)


def format_item_steps(item: Any) -> str:
    return get_registry(item.config).format_item_steps(item)
