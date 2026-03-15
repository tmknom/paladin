"""ルール詳細表示の公開API（View層）

公開APIは `paladin.view` から import すること(`__all__` のみ互換性対象)。

Docs:
    - docs/specs/rules/requirements.md
    - docs/specs/rules/design.md
"""

from paladin.view.context import ViewContext
from paladin.view.orchestrator import ViewOrchestrator
from paladin.view.provider import ViewOrchestratorProvider

__all__ = [
    "ViewContext",
    "ViewOrchestrator",
    "ViewOrchestratorProvider",
]
