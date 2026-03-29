"""Tests for Technical Debt checker."""
from __future__ import annotations

from pathlib import Path

import pytest

from ai_linter.analyzer.tech_debt_checker import TechDebtChecker

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# TD001 – TODO / FIXME comments
# ---------------------------------------------------------------------------

class TestTodoComments:
    def test_todo_detected(self):
        code = "# TODO: do something\nx = 1\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD001" and "TODO" in i.message for i in issues)

    def test_fixme_detected(self):
        code = "# FIXME: broken logic\nx = 1\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD001" for i in issues)

    def test_hack_detected(self):
        code = "# HACK: temporary workaround\nx = 1\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD001" for i in issues)

    def test_no_false_positive(self):
        code = "# This is a normal comment\nx = 1\n"
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD001" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_tech_debt.py"
        source = fixture.read_text()
        issues = TechDebtChecker(str(fixture), source).check()
        assert any(i.rule == "TD001" for i in issues)


# ---------------------------------------------------------------------------
# TD002 – Long function
# ---------------------------------------------------------------------------

class TestLongFunction:
    def _make_long_function(self, n_lines: int) -> str:
        body = "\n".join(f"    x_{i} = {i}" for i in range(n_lines))
        return f"def long_func():\n{body}\n    return x_{n_lines - 1}\n"

    def test_short_function_ok(self):
        code = self._make_long_function(20)
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD002" for i in issues)

    def test_long_function_flagged(self):
        code = self._make_long_function(60)
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD002" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_tech_debt.py"
        source = fixture.read_text()
        issues = TechDebtChecker(str(fixture), source).check()
        assert any(i.rule == "TD002" for i in issues)


# ---------------------------------------------------------------------------
# TD003 – Large class
# ---------------------------------------------------------------------------

class TestLargeClass:
    def _make_class(self, n_methods: int) -> str:
        methods = "\n".join(
            f"    def method_{i}(self):\n        return {i}\n"
            for i in range(n_methods)
        )
        return f"class BigClass:\n{methods}\n"

    def test_small_class_ok(self):
        code = self._make_class(5)
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD003" for i in issues)

    def test_large_class_flagged(self):
        # 60 methods × 3 lines each = 180 lines + overhead → well over 300
        methods = "\n".join(
            f"    def method_{i}(self):\n        pass\n        pass\n        pass\n        pass\n        pass\n"
            for i in range(60)
        )
        code = f"class HugeClass:\n{methods}\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD003" for i in issues)


# ---------------------------------------------------------------------------
# TD004 – Magic numbers
# ---------------------------------------------------------------------------

class TestMagicNumbers:
    def test_whitelisted_numbers_ok(self):
        code = "x = 0\ny = 1\nz = -1\n"
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD004" for i in issues)

    def test_magic_number_in_expression_flagged(self):
        code = "def calc(x):\n    return x * 42\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD004" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_tech_debt.py"
        source = fixture.read_text()
        issues = TechDebtChecker(str(fixture), source).check()
        assert any(i.rule == "TD004" for i in issues)


# ---------------------------------------------------------------------------
# TD005 – Long parameter list
# ---------------------------------------------------------------------------

class TestLongParamList:
    def test_short_params_ok(self):
        code = "def func(a, b, c): pass\n"
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD005" for i in issues)

    def test_long_params_flagged(self):
        code = "def func(a, b, c, d, e, f): pass\n"
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD005" for i in issues)

    def test_self_excluded(self):
        code = "class C:\n    def method(self, a, b, c, d, e): pass\n"
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD005" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_tech_debt.py"
        source = fixture.read_text()
        issues = TechDebtChecker(str(fixture), source).check()
        assert any(i.rule == "TD005" for i in issues)


# ---------------------------------------------------------------------------
# TD006 – Deep nesting
# ---------------------------------------------------------------------------

class TestDeepNesting:
    def test_shallow_nesting_ok(self):
        code = """
def func(data):
    if data:
        for x in data:
            if x:
                pass
"""
        issues = TechDebtChecker("test.py", code).check()
        assert not any(i.rule == "TD006" for i in issues)

    def test_deep_nesting_flagged(self):
        code = """
def func(data):
    if data:
        for x in data:
            if x:
                for y in x:
                    if y:
                        pass
"""
        issues = TechDebtChecker("test.py", code).check()
        assert any(i.rule == "TD006" for i in issues)

    def test_fixture_file(self):
        fixture = FIXTURES_DIR / "sample_tech_debt.py"
        source = fixture.read_text()
        issues = TechDebtChecker(str(fixture), source).check()
        assert any(i.rule == "TD006" for i in issues)


# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------

class TestGeneral:
    def test_syntax_error_returns_no_crash(self):
        code = "def broken(:\n    pass\n"
        issues = TechDebtChecker("test.py", code).check()
        # Should not raise; may return 0 or more issues
        assert isinstance(issues, list)

    def test_empty_file(self):
        issues = TechDebtChecker("test.py", "").check()
        assert issues == []
