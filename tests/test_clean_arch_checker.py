"""Tests for Clean Architecture layer violation checker."""
from __future__ import annotations

from pathlib import Path

import pytest

from ai_linter.analyzer.clean_arch_checker import (
    CleanArchChecker,
    _detect_import_layer,
    _detect_layer,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Layer detection helpers
# ---------------------------------------------------------------------------

class TestDetectLayer:
    def test_domain_path(self):
        assert _detect_layer("src/domain/user.py") == 0

    def test_entities_path(self):
        assert _detect_layer("src/entities/order.py") == 0

    def test_use_cases_path(self):
        assert _detect_layer("src/use_cases/create_order.py") == 1

    def test_application_path(self):
        assert _detect_layer("src/application/service.py") == 1

    def test_interfaces_path(self):
        assert _detect_layer("src/interfaces/http_controller.py") == 2

    def test_infrastructure_path(self):
        assert _detect_layer("src/infrastructure/database.py") == 3

    def test_unknown_path_returns_none(self):
        assert _detect_layer("src/utils/helper.py") is None


class TestDetectImportLayer:
    def test_domain_import(self):
        assert _detect_import_layer("domain.user") == 0

    def test_infrastructure_import(self):
        assert _detect_import_layer("infrastructure.database") == 3

    def test_unknown_import(self):
        assert _detect_import_layer("os.path") is None

    def test_use_cases_import(self):
        assert _detect_import_layer("use_cases.create_user") == 1


# ---------------------------------------------------------------------------
# CleanArchChecker
# ---------------------------------------------------------------------------

class TestCleanArchChecker:
    def test_no_violation_unknown_layer_file(self):
        """Files whose layer cannot be determined are silently skipped."""
        code = "from infrastructure.db import Repo\n"
        issues = CleanArchChecker("src/utils/helper.py", code).check()
        assert not issues

    def test_no_violation_correct_direction(self):
        """Infrastructure importing from domain – allowed (outer → inner)."""
        code = "from domain.user import User\n"
        issues = CleanArchChecker("src/infrastructure/repo.py", code).check()
        assert not any(i.rule == "CA001" for i in issues)

    def test_violation_inner_imports_outer(self):
        """Domain importing from infrastructure – VIOLATION."""
        code = "from infrastructure.database import Session\n"
        issues = CleanArchChecker("src/domain/user.py", code).check()
        assert any(i.rule == "CA001" for i in issues)

    def test_violation_use_cases_imports_infrastructure(self):
        """Use cases should not import infrastructure."""
        code = "import infrastructure.db\n"
        issues = CleanArchChecker("src/use_cases/create_order.py", code).check()
        assert any(i.rule == "CA001" for i in issues)

    def test_fixture_domain_file(self):
        fixture = FIXTURES_DIR / "domain" / "sample_clean_arch_violation.py"
        source = fixture.read_text()
        issues = CleanArchChecker(str(fixture), source).check()
        assert any(i.rule == "CA001" for i in issues)

    def test_no_violation_same_layer(self):
        """Importing within the same layer is allowed."""
        code = "from domain.order import Order\n"
        issues = CleanArchChecker("src/domain/user.py", code).check()
        assert not any(i.rule == "CA001" for i in issues)

    def test_violation_severity_is_error(self):
        """Layer violations should be reported as errors."""
        from ai_linter.analyzer.base import Severity
        code = "from infrastructure.database import Session\n"
        issues = CleanArchChecker("src/domain/user.py", code).check()
        assert all(i.severity == Severity.ERROR for i in issues if i.rule == "CA001")
