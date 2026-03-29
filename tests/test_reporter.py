"""Tests for the Reporter (JSON and Markdown output)."""
from __future__ import annotations

import json

from ai_linter.analyzer.base import AnalysisResult, Category, Issue, Severity
from ai_linter.report.reporter import Reporter


def _make_result(n_errors: int = 0, n_warnings: int = 1) -> AnalysisResult:
    issues = []
    for i in range(n_errors):
        issues.append(
            Issue(
                category=Category.CLEAN_ARCHITECTURE,
                rule="CA001",
                message="Error message",
                severity=Severity.ERROR,
                file="src/domain/user.py",
                line=i + 1,
                suggestion="Fix it",
            )
        )
    for i in range(n_warnings):
        issues.append(
            Issue(
                category=Category.SOLID,
                rule="SRP001",
                message="Warning message",
                severity=Severity.WARNING,
                file="src/domain/user.py",
                line=i + 10,
            )
        )
    return AnalysisResult(file="src/domain/user.py", issues=issues)


class TestReporter:
    def test_json_valid_structure(self):
        result = _make_result(n_errors=1, n_warnings=2)
        reporter = Reporter([result])
        data = json.loads(reporter.to_json())
        assert "summary" in data
        assert "files" in data
        assert data["summary"]["total_errors"] == 1
        assert data["summary"]["total_warnings"] == 2

    def test_json_empty(self):
        reporter = Reporter([])
        data = json.loads(reporter.to_json())
        assert data["summary"]["files_analysed"] == 0
        assert data["summary"]["total_issues"] == 0

    def test_markdown_contains_filename(self):
        result = _make_result()
        reporter = Reporter([result])
        md = reporter.to_markdown()
        assert "src/domain/user.py" in md

    def test_markdown_no_issues_message(self):
        result = AnalysisResult(file="clean.py", issues=[])
        reporter = Reporter([result])
        md = reporter.to_markdown()
        assert "No issues found" in md

    def test_markdown_contains_rule(self):
        result = _make_result(n_errors=1)
        reporter = Reporter([result])
        md = reporter.to_markdown()
        assert "CA001" in md

    def test_ai_review_in_markdown(self):
        result = AnalysisResult(
            file="src/domain/user.py",
            issues=[],
            ai_review="## AI Review\nLooks good!",
        )
        reporter = Reporter([result])
        md = reporter.to_markdown()
        assert "Looks good!" in md

    def test_summary_counts(self):
        r1 = _make_result(n_errors=2, n_warnings=3)
        r2 = _make_result(n_errors=1, n_warnings=1)
        reporter = Reporter([r1, r2])
        data = json.loads(reporter.to_json())
        assert data["summary"]["total_errors"] == 3
        assert data["summary"]["total_warnings"] == 4
        assert data["summary"]["files_analysed"] == 2
