"""Report generation: JSON and Markdown output formats."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..analyzer.base import AnalysisResult, Severity

# ---------------------------------------------------------------------------
# Emoji / symbol helpers
# ---------------------------------------------------------------------------
_SEVERITY_EMOJI = {
    Severity.ERROR: "🔴",
    Severity.WARNING: "🟡",
    Severity.INFO: "🔵",
}


def _severity_emoji(sev: str) -> str:
    try:
        return _SEVERITY_EMOJI[Severity(sev)]
    except (KeyError, ValueError):
        return "⚪"


class Reporter:
    """Converts a list of :class:`AnalysisResult` objects into reports."""

    def __init__(self, results: List[AnalysisResult]) -> None:
        self.results = results

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    def to_json(self) -> str:
        data = {
            "summary": self._summary(),
            "files": [r.to_dict() for r in self.results],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Markdown (suitable for GitHub PR comments)
    # ------------------------------------------------------------------
    def to_markdown(self) -> str:
        lines: List[str] = []
        summary = self._summary()

        lines.append("# 🏗️ AI Architecture Linter Report\n")
        lines.append(
            f"**Files analysed:** {summary['files_analysed']}  \n"
            f"**Total issues:** {summary['total_issues']}  \n"
            f"🔴 Errors: {summary['total_errors']}  \n"
            f"🟡 Warnings: {summary['total_warnings']}  \n"
            f"🔵 Info: {summary['total_info']}  \n"
        )
        lines.append("\n---\n")

        for result in self.results:
            if not result.issues and not result.ai_review:
                continue

            lines.append(f"## 📄 `{result.file}`\n")

            if result.issues:
                lines.append("### Static Analysis\n")
                lines.append("| Sev | Rule | Line | Message |")
                lines.append("|-----|------|------|---------|")
                for issue in result.issues:
                    emoji = _severity_emoji(issue.severity)
                    lines.append(
                        f"| {emoji} | `{issue.rule}` | {issue.line} "
                        f"| {issue.message} |"
                    )
                lines.append("")

                # Suggestions
                suggestions = [
                    (i.rule, i.suggestion)
                    for i in result.issues
                    if i.suggestion
                ]
                if suggestions:
                    lines.append("#### 💡 Suggestions\n")
                    for rule, sug in suggestions:
                        lines.append(f"- **`{rule}`**: {sug}")
                    lines.append("")

            if result.ai_review:
                lines.append("### 🤖 AI Review\n")
                lines.append(result.ai_review)
                lines.append("")

            lines.append("---\n")

        if not any(r.issues or r.ai_review for r in self.results):
            lines.append("✅ **No issues found!** Your code looks clean.\n")

        return "\n".join(lines)

    def save_markdown(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _summary(self) -> dict:
        total_issues = sum(len(r.issues) for r in self.results)
        total_errors = sum(r.error_count for r in self.results)
        total_warnings = sum(r.warning_count for r in self.results)
        total_info = total_issues - total_errors - total_warnings
        return {
            "files_analysed": len(self.results),
            "total_issues": total_issues,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
        }
