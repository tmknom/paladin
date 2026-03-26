"""Versionパッケージの公開API

CLIから `paladin version` コマンドを実行するためのエントリーポイントを提供する。

Note:
    仕様書は未作成のため Docs セクションは省略する。
"""

from paladin.version.provider import VersionOrchestratorProvider

__all__ = [
    "VersionOrchestratorProvider",
]
