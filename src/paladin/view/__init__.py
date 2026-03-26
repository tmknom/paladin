"""Viewパッケージの公開API

CLIからルール詳細表示を実行するためのエントリーポイントを提供する。

Docs:
    - docs/specs/view/requirements.md
    - docs/specs/view/design.md
"""

from paladin.view.context import ViewContext
from paladin.view.provider import ViewOrchestratorProvider

__all__ = [
    "ViewContext",
    "ViewOrchestratorProvider",
]
