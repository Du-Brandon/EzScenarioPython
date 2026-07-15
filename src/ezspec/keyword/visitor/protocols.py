"""Visitor contracts used by Feature, Rule, Scenario, and Step objects."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SpecificationElement(Protocol):
    def getName(self) -> str: ...

    def accept(self, visitor: "SpecificationElementVisitor") -> None: ...


@runtime_checkable
class SpecificationElementVisitor(Protocol):
    def visit(self, element: SpecificationElement) -> None: ...
