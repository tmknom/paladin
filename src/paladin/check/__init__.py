"""静的解析システムの公開API（Check層）

公開APIは `paladin.check` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/intro/requirements.md
    - docs/intro/roadmap.md
"""

from paladin.check.context import CheckContext
from paladin.check.provider import CheckOrchestratorProvider
from paladin.check.result import CheckReport, CheckStatus, CheckSummary
from paladin.check.rule.types import RuleMeta, Violation, Violations
from paladin.check.types import OutputFormat

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
