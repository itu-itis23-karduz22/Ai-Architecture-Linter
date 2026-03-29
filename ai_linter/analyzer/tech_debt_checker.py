"""Technical Debt detector.

Detects common technical debt indicators in Python source files:

  TD001  TODO / FIXME / HACK / XXX comment
  TD002  Long function (> MAX_FUNCTION_LINES lines)
  TD003  Large class (> MAX_CLASS_LINES lines)
  TD004  Magic number (numeric literal that is not 0, 1, or a named constant)
  TD005  Long parameter list (> MAX_PARAMS parameters)
  TD006  Deeply nested code (nesting depth > MAX_NESTING_DEPTH)
"""
from __future__ import annotations

import ast
import re
import tokenize
import io
from typing import List

from .base import BaseChecker, Category, Issue, Severity

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
MAX_FUNCTION_LINES = 50
MAX_CLASS_LINES = 300
MAX_PARAMS = 5
MAX_NESTING_DEPTH = 4
# Common numeric literals that are semantically self-evident and rarely
# represent accidental "magic" values:
#   0, 1, -1  – identity / sentinel values
#   2         – halving, doubling, parity checks
#   100       – percentage base (x / 100, x * 100)
MAGIC_NUMBER_WHITELIST = {0, 1, -1, 2, 100}

_DEBT_COMMENT_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)

# Nesting-inducing statement types
_NESTING_TYPES = (
    ast.If, ast.For, ast.While, ast.With,
    ast.Try, ast.ExceptHandler,
)


class TechDebtChecker(BaseChecker):
    """Detects common technical debt indicators."""

    # ------------------------------------------------------------------
    # Comment scanning (uses tokenizer, not AST)
    # ------------------------------------------------------------------
    def check(self) -> List[Issue]:
        self._scan_comments()
        if not self._parse():
            return self.issues
        self.visit(self._tree)
        return self.issues

    def _scan_comments(self) -> None:
        try:
            tokens = tokenize.generate_tokens(io.StringIO(self.source).readline)
            for tok_type, tok_string, tok_start, _, _ in tokens:
                if tok_type == tokenize.COMMENT:
                    match = _DEBT_COMMENT_RE.search(tok_string)
                    if match:
                        keyword = match.group(1).upper()
                        # Create a lightweight placeholder node for line tracking
                        self.issues.append(
                            Issue(
                                category=Category.TECHNICAL_DEBT,
                                rule="TD001",
                                message=(
                                    f"{keyword} comment found: {tok_string.strip()}"
                                ),
                                severity=Severity.INFO,
                                file=self.filename,
                                line=tok_start[0],
                                col=tok_start[1],
                                suggestion=(
                                    "Resolve or create a tracked issue for this "
                                    f"{keyword} before merging."
                                ),
                            )
                        )
        except tokenize.TokenError:
            pass

    # ------------------------------------------------------------------
    # Long function
    # ------------------------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        lines = (node.end_lineno or node.lineno) - node.lineno + 1
        if lines > MAX_FUNCTION_LINES:
            self._add_issue(
                rule="TD002",
                message=(
                    f"Function/method '{node.name}' is {lines} lines long "
                    f"(max {MAX_FUNCTION_LINES})."
                ),
                severity=Severity.WARNING,
                category=Category.TECHNICAL_DEBT,
                node=node,
                suggestion=(
                    f"Break '{node.name}' into smaller, focused functions."
                ),
            )
        self._check_params(node)
        self._check_nesting(node.body, current_depth=0)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    # ------------------------------------------------------------------
    # Large class
    # ------------------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        lines = (node.end_lineno or node.lineno) - node.lineno + 1
        if lines > MAX_CLASS_LINES:
            self._add_issue(
                rule="TD003",
                message=(
                    f"Class '{node.name}' is {lines} lines long "
                    f"(max {MAX_CLASS_LINES})."
                ),
                severity=Severity.WARNING,
                category=Category.TECHNICAL_DEBT,
                node=node,
                suggestion=(
                    f"Consider splitting '{node.name}' into multiple smaller classes."
                ),
            )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Magic numbers
    # ------------------------------------------------------------------
    def visit_Constant(self, node: ast.Constant) -> None:
        if not isinstance(node.value, (int, float)):
            return
        if isinstance(node.value, bool):
            return
        if node.value in MAGIC_NUMBER_WHITELIST:
            return
        # Only flag when the literal is NOT the right-hand side of an
        # assignment to a module/class-level name (i.e., a named constant).
        parent = getattr(node, "_parent", None)
        if isinstance(parent, ast.Assign):
            # If it's a simple assignment at module scope, it's a named const
            return
        if isinstance(parent, (ast.AugAssign, ast.AnnAssign)):
            return
        self._add_issue(
            rule="TD004",
            message=f"Magic number '{node.value}' found.",
            severity=Severity.INFO,
            category=Category.TECHNICAL_DEBT,
            node=node,
            suggestion=(
                f"Replace the literal '{node.value}' with a named constant "
                "to improve readability and maintainability."
            ),
        )

    def _parse(self) -> bool:
        ok = super()._parse()
        if ok:
            self._set_parents(self._tree)
        return ok

    def _set_parents(self, tree: ast.AST) -> None:
        """Annotate each node with a _parent reference."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child._parent = node  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Long parameter list
    # ------------------------------------------------------------------
    def _check_params(self, node: ast.FunctionDef) -> None:
        all_args = (
            node.args.args
            + node.args.posonlyargs
            + node.args.kwonlyargs
        )
        # Exclude 'self' and 'cls'
        params = [a for a in all_args if a.arg not in ("self", "cls")]
        if len(params) > MAX_PARAMS:
            self._add_issue(
                rule="TD005",
                message=(
                    f"Function/method '{node.name}' has {len(params)} parameters "
                    f"(max {MAX_PARAMS})."
                ),
                severity=Severity.WARNING,
                category=Category.TECHNICAL_DEBT,
                node=node,
                suggestion=(
                    "Introduce a parameter object or data class to group "
                    "related parameters together."
                ),
            )

    # ------------------------------------------------------------------
    # Deep nesting
    # ------------------------------------------------------------------
    def _check_nesting(self, stmts: list, current_depth: int) -> None:
        for stmt in stmts:
            if isinstance(stmt, _NESTING_TYPES):
                depth = current_depth + 1
                if depth >= MAX_NESTING_DEPTH:
                    self._add_issue(
                        rule="TD006",
                        message=(
                            f"Nesting depth {depth} exceeds maximum "
                            f"({MAX_NESTING_DEPTH})."
                        ),
                        severity=Severity.WARNING,
                        category=Category.TECHNICAL_DEBT,
                        node=stmt,
                        suggestion=(
                            "Reduce nesting by extracting inner blocks into "
                            "separate functions or using early returns / guard clauses."
                        ),
                    )
                child_bodies = []
                for attr in ("body", "orelse", "finalbody", "handlers"):
                    val = getattr(stmt, attr, [])
                    if isinstance(val, list):
                        child_bodies.extend(val)
                    elif val:
                        child_bodies.append(val)
                self._check_nesting(child_bodies, depth)
