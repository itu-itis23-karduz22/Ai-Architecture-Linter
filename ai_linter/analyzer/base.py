"""Base classes and data models for the architecture linter."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Category(str, Enum):
    SOLID = "SOLID"
    CLEAN_ARCHITECTURE = "CleanArchitecture"
    TECHNICAL_DEBT = "TechnicalDebt"


@dataclass
class Issue:
    """Represents a single linting issue found in the code."""

    category: Category
    rule: str
    message: str
    severity: Severity
    file: str
    line: int
    col: int = 0
    suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity.value,
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "suggestion": self.suggestion,
        }


@dataclass
class AnalysisResult:
    """Aggregated result from all analyzers."""

    file: str
    issues: List[Issue] = field(default_factory=list)
    ai_review: Optional[str] = None

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
            "ai_review": self.ai_review,
        }


class BaseChecker(ast.NodeVisitor):
    """Base class for all AST-based checkers."""

    def __init__(self, filename: str, source: str) -> None:
        self.filename = filename
        self.source = source
        self.issues: List[Issue] = []
        self._tree: Optional[ast.AST] = None

    def _parse(self) -> bool:
        try:
            self._tree = ast.parse(self.source, filename=self.filename)
            return True
        except SyntaxError:
            return False

    def check(self) -> List[Issue]:
        """Run the checker and return found issues."""
        if not self._parse():
            return []
        self.visit(self._tree)
        return self.issues

    def _add_issue(
        self,
        rule: str,
        message: str,
        severity: Severity,
        category: Category,
        node: ast.AST,
        suggestion: Optional[str] = None,
    ) -> None:
        line = getattr(node, "lineno", 0)
        col = getattr(node, "col_offset", 0)
        self.issues.append(
            Issue(
                category=category,
                rule=rule,
                message=message,
                severity=severity,
                file=self.filename,
                line=line,
                col=col,
                suggestion=suggestion,
            )
        )
