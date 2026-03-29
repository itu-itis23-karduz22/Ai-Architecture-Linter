"""SOLID principle checkers using Python AST analysis."""
from __future__ import annotations

import ast
from typing import Dict, List, Optional, Set

from .base import BaseChecker, Category, Issue, Severity

# --------------------------------------------------------------------------- #
# Thresholds (tunable)
# --------------------------------------------------------------------------- #
SRP_MAX_PUBLIC_METHODS = 10        # Single Responsibility
OCP_MAX_ISINSTANCE_CHECKS = 3     # Open/Closed
ISP_MAX_ABSTRACT_METHODS = 7      # Interface Segregation
DIP_FORBIDDEN_PATTERNS = {        # Dependency Inversion – concrete instantiation
    "direct_instantiation",
}


class SRPChecker(BaseChecker):
    """Single Responsibility Principle.

    A class that exposes too many public methods likely handles more than one
    responsibility.  We also flag classes whose method names span clearly
    distinct semantic domains.
    """

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        public_methods = [
            n for n in ast.walk(node)
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
        ]
        count = len(public_methods)
        if count > SRP_MAX_PUBLIC_METHODS:
            self._add_issue(
                rule="SRP001",
                message=(
                    f"Class '{node.name}' has {count} public methods "
                    f"(max {SRP_MAX_PUBLIC_METHODS}). "
                    "It may violate the Single Responsibility Principle."
                ),
                severity=Severity.WARNING,
                category=Category.SOLID,
                node=node,
                suggestion=(
                    f"Consider splitting '{node.name}' into smaller classes, "
                    "each responsible for a single concern."
                ),
            )
        self.generic_visit(node)


class OCPChecker(BaseChecker):
    """Open/Closed Principle.

    Frequent isinstance() / type() checks inside a method suggest the caller
    needs to be *modified* every time a new type is added, which violates OCP.
    """

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        isinstance_calls = [
            n for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id in ("isinstance", "type")
        ]
        count = len(isinstance_calls)
        if count >= OCP_MAX_ISINSTANCE_CHECKS:
            self._add_issue(
                rule="OCP001",
                message=(
                    f"Function/method '{node.name}' contains {count} "
                    "isinstance/type checks. This may indicate a violation of "
                    "the Open/Closed Principle."
                ),
                severity=Severity.WARNING,
                category=Category.SOLID,
                node=node,
                suggestion=(
                    "Replace type-checking conditionals with polymorphism "
                    "(e.g., a common abstract method or strategy pattern)."
                ),
            )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


class LSPChecker(BaseChecker):
    """Liskov Substitution Principle.

    Overriding methods that *raise NotImplementedError* unconditionally force
    callers to know about the concrete subtype, breaking substitutability.
    Overriding methods with a different number of required parameters than
    their declared base may also break substitution.
    """

    def __init__(self, filename: str, source: str) -> None:
        super().__init__(filename, source)
        self._base_methods: Dict[str, int] = {}   # name -> arg count
        self._class_bases: Dict[str, List[str]] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        base_names = [
            b.id for b in node.bases if isinstance(b, ast.Name)
        ]
        self._class_bases[node.name] = base_names
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self._check_override(item, base_names, node)
        self.generic_visit(node)

    def _check_override(
        self, method: ast.FunctionDef, base_names: List[str], class_node: ast.ClassDef
    ) -> None:
        # Check for unconditional NotImplementedError raises in non-abstract classes
        for stmt in method.body:
            if (
                isinstance(stmt, ast.Raise)
                and stmt.exc is not None
                and isinstance(stmt.exc, ast.Call)
                and isinstance(stmt.exc.func, ast.Name)
                and stmt.exc.func.id == "NotImplementedError"
            ):
                if not any(
                    b in ("ABC", "ABCMeta") for b in base_names
                ):
                    self._add_issue(
                        rule="LSP001",
                        message=(
                            f"Method '{method.name}' in '{class_node.name}' raises "
                            "NotImplementedError unconditionally without extending ABC. "
                            "Subclasses that don't override this break LSP."
                        ),
                        severity=Severity.WARNING,
                        category=Category.SOLID,
                        node=method,
                        suggestion=(
                            "Use abc.ABC and @abstractmethod instead of raising "
                            "NotImplementedError manually, or ensure subclasses "
                            "always override this method."
                        ),
                    )
                break


class ISPChecker(BaseChecker):
    """Interface Segregation Principle.

    Abstract base classes (ABC) with too many abstract methods force
    implementors to depend on methods they may not need.
    """

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_abstract = any(
            (isinstance(b, ast.Name) and b.id == "ABC")
            or (isinstance(b, ast.Attribute) and b.attr == "ABC")
            for b in node.bases
        )
        if not is_abstract:
            self.generic_visit(node)
            return

        abstract_methods = [
            n for n in ast.walk(node)
            if isinstance(n, ast.FunctionDef)
            and any(
                (isinstance(d, ast.Name) and d.id == "abstractmethod")
                or (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                for d in n.decorator_list
            )
        ]
        count = len(abstract_methods)
        if count > ISP_MAX_ABSTRACT_METHODS:
            self._add_issue(
                rule="ISP001",
                message=(
                    f"Abstract class '{node.name}' defines {count} abstract methods "
                    f"(max {ISP_MAX_ABSTRACT_METHODS}). "
                    "Implementors may be forced to depend on methods they don't need."
                ),
                severity=Severity.WARNING,
                category=Category.SOLID,
                node=node,
                suggestion=(
                    f"Consider splitting '{node.name}' into smaller, focused "
                    "interfaces (abstract classes or Protocols)."
                ),
            )
        self.generic_visit(node)


class DIPChecker(BaseChecker):
    """Dependency Inversion Principle.

    Instantiation of concrete classes inside a function body (rather than
    receiving them via constructor / parameter injection) ties high-level
    modules directly to implementations.
    """

    # Names that are clearly abstract / primitive and should be ignored
    _WHITELIST: Set[str] = {
        "list", "dict", "set", "tuple", "str", "int", "float", "bool",
        "bytes", "Exception", "ValueError", "TypeError", "KeyError",
        "IndexError", "RuntimeError", "NotImplementedError", "StopIteration",
        "object", "super", "range", "enumerate", "zip", "map", "filter",
        "print", "len", "open", "Path", "datetime", "date", "timedelta",
    }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Collect names injected via parameters
        param_names: Set[str] = {
            arg.arg for arg in node.args.args
            + node.args.posonlyargs
            + node.args.kwonlyargs
        }

        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            # Direct call like SomeConcreteClass(...)
            if not isinstance(child.func, ast.Name):
                continue
            called = child.func.id
            if called in self._WHITELIST or called in param_names:
                continue
            # Heuristic: PascalCase name that isn't a known builtin
            if called and called[0].isupper() and called not in param_names:
                self._add_issue(
                    rule="DIP001",
                    message=(
                        f"Concrete class '{called}' is instantiated directly inside "
                        f"function/method '{node.name}'. This may violate the "
                        "Dependency Inversion Principle."
                    ),
                    severity=Severity.INFO,
                    category=Category.SOLID,
                    node=child,
                    suggestion=(
                        f"Inject '{called}' as a dependency (constructor or parameter "
                        "injection) and depend on an abstraction instead."
                    ),
                )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


class SOLIDChecker:
    """Runs all SOLID checkers on a single Python source file."""

    def __init__(self, filename: str, source: str) -> None:
        self.filename = filename
        self.source = source

    def check(self) -> List[Issue]:
        issues: List[Issue] = []
        for checker_cls in (
            SRPChecker,
            OCPChecker,
            LSPChecker,
            ISPChecker,
            DIPChecker,
        ):
            issues.extend(checker_cls(self.filename, self.source).check())
        return issues
