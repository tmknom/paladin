"""対象列挙システムの公開API(Check層)

公開APIは `paladin.check` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/intro/requirements.md
    - docs/intro/roadmap.md
"""

from paladin.check.context import CheckContext
from paladin.check.formatter import CheckReportFormatter
from paladin.check.provider import CheckOrchestratorProvider
from paladin.check.types import (
    CheckReport,
    CheckStatus,
    CheckSummary,
    RuleMeta,
    Violation,
    Violations,
)

__all__ = [
    "CheckContext",
    "CheckOrchestratorProvider",
    "CheckReport",
    "CheckReportFormatter",
    "CheckStatus",
    "CheckSummary",
    "RuleMeta",
    "Violation",
    "Violations",
]
