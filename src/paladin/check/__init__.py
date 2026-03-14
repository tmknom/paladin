"""静的解析システムの公開API（Check層）

公開APIは `paladin.check` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/check/requirements.md
    - docs/specs/check/design.md
"""

from paladin.check.context import CheckContext
from paladin.check.provider import CheckOrchestratorProvider
from paladin.check.result import CheckReport, CheckStatus, CheckSummary
from paladin.check.types import OutputFormat
from paladin.lint import RuleMeta, Violation, Violations

__all__ = [
    "CheckContext",
    "CheckOrchestratorProvider",
    "CheckReport",
    "CheckStatus",
    "CheckSummary",
    "OutputFormat",
    "RuleMeta",
    "Violation",
    "Violations",
]
