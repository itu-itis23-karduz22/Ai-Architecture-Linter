"""Command-line interface for the AI Architecture Linter."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import click

from .ai.review_engine import AIReviewEngine
from .analyzer.base import AnalysisResult
from .analyzer.clean_arch_checker import CleanArchChecker
from .analyzer.solid_checker import SOLIDChecker
from .analyzer.tech_debt_checker import TechDebtChecker
from .report.reporter import Reporter


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except ImportError:
        pass


def _analyze_file(
    path: Path,
    ai_engine: Optional[AIReviewEngine] = None,
) -> AnalysisResult:
    source = path.read_text(encoding="utf-8", errors="replace")
    filename = str(path)

    issues = []
    issues.extend(SOLIDChecker(filename, source).check())
    issues.extend(CleanArchChecker(filename, source).check())
    issues.extend(TechDebtChecker(filename, source).check())

    ai_review = None
    if ai_engine and ai_engine.available:
        ai_review = ai_engine.review(filename, source, issues)

    return AnalysisResult(file=filename, issues=issues, ai_review=ai_review)


def _collect_python_files(paths: List[Path], recursive: bool) -> List[Path]:
    collected: List[Path] = []
    for p in paths:
        if p.is_file() and p.suffix == ".py":
            collected.append(p)
        elif p.is_dir():
            pattern = "**/*.py" if recursive else "*.py"
            collected.extend(sorted(p.glob(pattern)))
    return collected


@click.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    "--recursive", "-r", is_flag=True, default=False,
    help="Recursively scan directories.",
)
@click.option(
    "--format", "-f", "output_format",
    type=click.Choice(["text", "json", "markdown"], case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output", "-o", "output_path",
    type=click.Path(),
    default=None,
    help="Save report to this file (optional).",
)
@click.option(
    "--ai/--no-ai", "use_ai",
    default=True,
    show_default=True,
    help="Enable or disable AI-powered review (requires OPENAI_API_KEY).",
)
@click.option(
    "--model", default="gpt-4o-mini", show_default=True,
    help="OpenAI model to use for AI review.",
)
@click.option(
    "--fail-on-error/--no-fail-on-error",
    default=True,
    show_default=True,
    help="Exit with code 1 if any errors are found.",
)
def main(
    paths: tuple,
    recursive: bool,
    output_format: str,
    output_path: Optional[str],
    use_ai: bool,
    model: str,
    fail_on_error: bool,
) -> None:
    """AI-Powered Architecture Linter — analyse Python files for SOLID,
    Clean Architecture, and technical debt violations."""
    _load_dotenv()

    file_paths = _collect_python_files([Path(p) for p in paths], recursive)
    if not file_paths:
        click.echo("No Python files found.", err=True)
        sys.exit(0)

    ai_engine = AIReviewEngine(model=model) if use_ai else None
    if ai_engine and not ai_engine.available:
        click.echo(
            "⚠️  OPENAI_API_KEY not set — AI review disabled.",
            err=True,
        )

    results: List[AnalysisResult] = []
    with click.progressbar(file_paths, label="Analysing", file=sys.stderr) as bar:
        for fp in bar:
            results.append(_analyze_file(fp, ai_engine))

    reporter = Reporter(results)

    # ---- Output ----
    if output_format == "json":
        report_text = reporter.to_json()
    elif output_format == "markdown":
        report_text = reporter.to_markdown()
    else:
        report_text = _format_text(results)

    if output_path:
        Path(output_path).write_text(report_text, encoding="utf-8")
        click.echo(f"Report saved to {output_path}", err=True)
    else:
        click.echo(report_text)

    # ---- Exit code ----
    if fail_on_error and any(r.error_count > 0 for r in results):
        sys.exit(1)


def _format_text(results: List[AnalysisResult]) -> str:
    """Produce a compact, human-readable text summary."""
    lines: List[str] = []
    total_issues = sum(len(r.issues) for r in results)
    for result in results:
        for issue in result.issues:
            lines.append(
                f"{issue.file}:{issue.line}:{issue.col}: "
                f"[{issue.severity.value.upper()}] "
                f"{issue.category.value}/{issue.rule} {issue.message}"
            )
            if issue.suggestion:
                lines.append(f"  → {issue.suggestion}")
    if total_issues == 0:
        lines.append("✅ No issues found.")
    else:
        errors = sum(r.error_count for r in results)
        warnings = sum(r.warning_count for r in results)
        info = total_issues - errors - warnings
        lines.append(
            f"\n{total_issues} issue(s): "
            f"{errors} error(s), {warnings} warning(s), {info} info."
        )
    return "\n".join(lines)
