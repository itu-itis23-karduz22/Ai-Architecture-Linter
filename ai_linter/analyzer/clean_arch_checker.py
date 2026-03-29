"""Clean Architecture layer violation checker.

Clean Architecture defines four concentric layers (inner → outer):
  1. Entities   (domain)
  2. Use Cases  (application)
  3. Interfaces (adapters / controllers)
  4. Infrastructure (frameworks, DB, HTTP, …)

The Dependency Rule: source-code dependencies must point *inward only*.
An inner layer MUST NOT import from an outer layer.

This checker detects violations by examining ``import`` and ``from … import``
statements and comparing source/target layer indices.

Layer detection is based on the path of each Python file:

  Layer keyword         Directory / module keywords
  ─────────────────     ──────────────────────────────────
  ENTITIES (0)          domain, entities, models
  USE_CASES (1)         use_cases, usecases, application, services
  INTERFACES (2)        interfaces, adapters, controllers, presenters, views
  INFRASTRUCTURE (3)    infrastructure, infra, frameworks, db, repositories,
                        external, api, web, persistence
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import BaseChecker, Category, Issue, Severity

# ---------------------------------------------------------------------------
# Layer definitions
# ---------------------------------------------------------------------------
_LAYER_KEYWORDS: List[Tuple[int, List[str]]] = [
    (0, ["domain", "entities", "entity", "model", "models"]),
    (1, ["use_case", "use_cases", "usecases", "usecase", "application", "service", "services"]),
    (2, ["interface", "interfaces", "adapter", "adapters", "controller", "controllers",
         "presenter", "presenters", "view", "views"]),
    (3, ["infrastructure", "infra", "framework", "frameworks", "db", "database",
         "repository", "repositories", "external", "api", "web", "persistence",
         "storage", "cache", "messaging"]),
]

_LAYER_NAMES = {0: "Entities", 1: "UseCases", 2: "Interfaces", 3: "Infrastructure"}


def _detect_layer(path_str: str) -> Optional[int]:
    """Return the layer index for a file path, or None if unknown."""
    normalized = path_str.lower().replace("\\", "/").replace("-", "_")
    parts = normalized.split("/")
    # Walk from innermost directory outward
    for part in reversed(parts):
        for layer_idx, keywords in _LAYER_KEYWORDS:
            for kw in keywords:
                if kw in part:
                    return layer_idx
    return None


def _detect_import_layer(module_name: str) -> Optional[int]:
    """Return layer index for an imported module name, or None if unknown."""
    normalized = module_name.lower().replace("-", "_")
    parts = normalized.split(".")
    for part in reversed(parts):
        for layer_idx, keywords in _LAYER_KEYWORDS:
            for kw in keywords:
                if kw in part:
                    return layer_idx
    return None


class CleanArchChecker(BaseChecker):
    """Detects import-level Clean Architecture layer violations."""

    def __init__(self, filename: str, source: str) -> None:
        super().__init__(filename, source)
        self._source_layer = _detect_layer(filename)

    def check(self) -> List[Issue]:
        if self._source_layer is None:
            # Cannot determine layer – skip
            return []
        return super().check()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module(alias.name, node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self._check_module(node.module, node)

    def _check_module(self, module: str, node: ast.AST) -> None:
        target_layer = _detect_import_layer(module)
        if target_layer is None:
            return
        if target_layer > self._source_layer:  # type: ignore[operator]
            src_name = _LAYER_NAMES[self._source_layer]  # type: ignore[index]
            tgt_name = _LAYER_NAMES[target_layer]
            self._add_issue(
                rule="CA001",
                message=(
                    f"[{src_name}] imports from [{tgt_name}] (module: '{module}'). "
                    "Inner layers must not depend on outer layers."
                ),
                severity=Severity.ERROR,
                category=Category.CLEAN_ARCHITECTURE,
                node=node,
                suggestion=(
                    f"Move the dependency on '{module}' behind an abstraction "
                    f"(interface/port) defined in the [{src_name}] layer and "
                    "inject the concrete implementation from outside."
                ),
            )
