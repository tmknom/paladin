"""Checkパッケージの公開API

CLIから静的解析を実行するためのエントリーポイントを提供する。

Docs:
    - docs/specs/check/requirements.md
    - docs/specs/check/design.md
"""

from paladin.check.context import CheckContext
from paladin.check.provider import CheckOrchestratorProvider

__all__ = [
    "CheckContext",
    "CheckOrchestratorProvider",
]
