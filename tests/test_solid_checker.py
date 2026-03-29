"""Tests for SOLID principle checkers."""
from __future__ import annotations

from pathlib import Path

import pytest

from ai_linter.analyzer.solid_checker import (
    DIPChecker,
    ISPChecker,
    LSPChecker,
    OCPChecker,
    SOLIDChecker,
    SRPChecker,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _src(code: str) -> str:
    return code


# ---------------------------------------------------------------------------
# SRP
# ---------------------------------------------------------------------------

class TestSRP:
    def test_no_violation_small_class(self):
        code = """
class SmallClass:
    def method_a(self): pass
    def method_b(self): pass
"""
        issues = SRPChecker("test.py", _src(code)).check()
        assert not issues

    def test_violation_large_class(self):
        methods = "\n".join(
            f"    def method_{i}(self): pass" for i in range(12)
        )
        code = f"class BigClass:\n{methods}\n"
        issues = SRPChecker("test.py", _src(code)).check()
        assert any(i.rule == "SRP001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = SRPChecker(str(fixture), source).check()
        assert any(i.rule == "SRP001" for i in issues), (
            "Expected SRP001 from fixture"
        )

    def test_private_methods_not_counted(self):
        methods = "\n".join(
            f"    def _method_{i}(self): pass" for i in range(15)
        )
        code = f"class PrivateMethods:\n{methods}\n"
        issues = SRPChecker("test.py", _src(code)).check()
        assert not any(i.rule == "SRP001" for i in issues)


# ---------------------------------------------------------------------------
# OCP
# ---------------------------------------------------------------------------

class TestOCP:
    def test_no_violation_no_isinstance(self):
        code = """
def render(shape):
    shape.draw()
"""
        issues = OCPChecker("test.py", _src(code)).check()
        assert not issues

    def test_violation_isinstance_chain(self):
        code = """
def process(obj):
    if isinstance(obj, A):
        pass
    elif isinstance(obj, B):
        pass
    elif isinstance(obj, C):
        pass
"""
        issues = OCPChecker("test.py", _src(code)).check()
        assert any(i.rule == "OCP001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = OCPChecker(str(fixture), source).check()
        assert any(i.rule == "OCP001" for i in issues)


# ---------------------------------------------------------------------------
# LSP
# ---------------------------------------------------------------------------

class TestLSP:
    def test_no_violation_abc_class(self):
        code = """
from abc import ABC, abstractmethod
class Base(ABC):
    @abstractmethod
    def work(self):
        raise NotImplementedError
"""
        issues = LSPChecker("test.py", _src(code)).check()
        assert not any(i.rule == "LSP001" for i in issues)

    def test_violation_not_implemented_without_abc(self):
        code = """
class Worker:
    def work(self):
        raise NotImplementedError("override me")
"""
        issues = LSPChecker("test.py", _src(code)).check()
        assert any(i.rule == "LSP001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = LSPChecker(str(fixture), source).check()
        assert any(i.rule == "LSP001" for i in issues)


# ---------------------------------------------------------------------------
# ISP
# ---------------------------------------------------------------------------

class TestISP:
    def test_no_violation_small_interface(self):
        code = """
from abc import ABC, abstractmethod
class SmallInterface(ABC):
    @abstractmethod
    def method_a(self): ...
    @abstractmethod
    def method_b(self): ...
"""
        issues = ISPChecker("test.py", _src(code)).check()
        assert not issues

    def test_violation_fat_interface(self):
        abstract_methods = "\n".join(
            f"    @abstractmethod\n    def method_{i}(self): ..." for i in range(9)
        )
        code = f"from abc import ABC, abstractmethod\nclass FatABC(ABC):\n{abstract_methods}\n"
        issues = ISPChecker("test.py", _src(code)).check()
        assert any(i.rule == "ISP001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = ISPChecker(str(fixture), source).check()
        assert any(i.rule == "ISP001" for i in issues)

    def test_non_abc_not_flagged(self):
        code = """
class NotABC:
    def method_a(self): ...
    def method_b(self): ...
    def method_c(self): ...
"""
        issues = ISPChecker("test.py", _src(code)).check()
        assert not issues


# ---------------------------------------------------------------------------
# DIP
# ---------------------------------------------------------------------------

class TestDIP:
    def test_no_violation_with_injection(self):
        code = """
class UserService:
    def __init__(self, repo):
        self.repo = repo

    def get_user(self, user_id):
        return self.repo.find(user_id)
"""
        issues = DIPChecker("test.py", _src(code)).check()
        assert not any(i.rule == "DIP001" for i in issues)

    def test_violation_direct_instantiation(self):
        code = """
class ConcreteRepo:
    pass

class UserService:
    def get_user(self, user_id):
        repo = ConcreteRepo()
        return repo.find(user_id)
"""
        issues = DIPChecker("test.py", _src(code)).check()
        assert any(i.rule == "DIP001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = DIPChecker(str(fixture), source).check()
        assert any(i.rule == "DIP001" for i in issues)

    def test_builtins_not_flagged(self):
        code = """
def get_names():
    return list()
"""
        issues = DIPChecker("test.py", _src(code)).check()
        assert not any(i.rule == "DIP001" for i in issues)


# ---------------------------------------------------------------------------
# SOLIDChecker (integration)
# ---------------------------------------------------------------------------

class TestSOLIDChecker:
    def test_returns_multiple_rule_types(self):
        fixture = FIXTURES_DIR / "sample_srp_violation.py"
        source = fixture.read_text()
        issues = SOLIDChecker(str(fixture), source).check()
        rules_found = {i.rule for i in issues}
        # At minimum SRP001 and OCP001 should be present
        assert "SRP001" in rules_found
        assert "OCP001" in rules_found

    def test_clean_code_has_no_solid_violations(self):
        code = """
from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def find(self, id): ...

class UserService:
    def __init__(self, repo: Repository):
        self._repo = repo

    def get_user(self, user_id: int):
        return self._repo.find(user_id)
"""
        issues = SOLIDChecker("clean.py", code).check()
        solid_issues = [i for i in issues if i.rule.startswith(("SRP", "OCP", "LSP", "ISP"))]
        assert not solid_issues
