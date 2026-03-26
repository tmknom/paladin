"""Versionパッケージのオーケストレーター

バージョン取得の処理フロー全体を制御する。
"""

from paladin.foundation.log import log
from paladin.version.resolver import VersionResolver


class VersionOrchestrator:
    """バージョン文字列取得の処理フローを制御する"""

    def __init__(self, resolver: VersionResolver) -> None:
        """VersionOrchestratorを初期化する"""
        self.resolver = resolver

    @log
    def orchestrate(self) -> str:
        """バージョン文字列を返す"""
        return self.resolver.resolve()
