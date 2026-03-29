"""AI-powered code review engine using OpenAI."""
from __future__ import annotations

import os
from typing import List, Optional

from ..analyzer.base import Issue

_SYSTEM_PROMPT = """\
You are an expert software architect and code reviewer specialising in:
- SOLID principles (SRP, OCP, LSP, ISP, DIP)
- Clean Architecture (Entities → Use Cases → Interfaces → Infrastructure)
- Technical debt detection and remediation

You are reviewing a Python source file as part of an automated pull-request \
review pipeline.  The static analyser has already identified the following \
issues.  Your job is to:

1. Confirm or contextualise each static analysis finding.
2. Identify any additional *architectural* concerns not captured by the \
   static rules.
3. Suggest concrete, actionable refactoring steps.
4. Be concise and constructive — focus on the most important issues first.

Respond in plain Markdown so the output can be posted directly as a \
pull-request review comment.
"""


def _build_user_prompt(filename: str, source: str, issues: List[Issue]) -> str:
    issues_text = "\n".join(
        f"- [{i.severity.value.upper()}] {i.category.value}/{i.rule} "
        f"(line {i.line}): {i.message}"
        for i in issues
    )
    # Truncate very large files to avoid token limit issues
    max_source_chars = 8000
    truncated = source[:max_source_chars]
    if len(source) > max_source_chars:
        truncated += "\n\n# ... (file truncated for brevity) ..."

    return (
        f"## File: `{filename}`\n\n"
        f"### Static Analysis Findings\n\n"
        f"{issues_text or '(none)'}\n\n"
        f"### Source Code\n\n"
        f"```python\n{truncated}\n```\n\n"
        "Please provide your architectural review."
    )


class AIReviewEngine:
    """Wraps the OpenAI chat-completion API to produce architectural reviews.

    If no API key is available the engine gracefully returns *None*, allowing
    the rest of the pipeline to continue with static-analysis results only.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> None:
        self._model = model
        self._client = None
        key = api_key or os.getenv("OPENAI_API_KEY")
        if key:
            try:
                from openai import OpenAI  # type: ignore
                self._client = OpenAI(api_key=key)
            except ImportError:
                pass

    @property
    def available(self) -> bool:
        return self._client is not None

    def review(
        self,
        filename: str,
        source: str,
        issues: List[Issue],
    ) -> Optional[str]:
        """Return an AI-generated review string, or *None* on failure."""
        if not self.available:
            return None
        user_prompt = _build_user_prompt(filename, source, issues)
        try:
            response = self._client.chat.completions.create(  # type: ignore
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception:  # noqa: BLE001
            return None
