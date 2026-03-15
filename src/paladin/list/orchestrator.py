"""List層の中核

ルール一覧取得とフォーマットの処理フロー全体を制御する。
"""

from paladin.foundation.log import log
from paladin.lint import RuleRegistry
from paladin.list.context import ListContext
from paladin.list.formatter import ListFormatter


class ListOrchestrator:
    """ルール一覧取得とフォーマットの処理フローを制御する"""

    def __init__(
        self,
        registry: RuleRegistry,
        formatter: ListFormatter,
    ) -> None:
        """ListOrchestratorを初期化する"""
        self.registry = registry
        self.formatter = formatter

    @log
    def orchestrate(self, context: ListContext) -> str:
        """全ルール一覧をフォーマットした文字列を返す"""
        rules = self.registry.list_rules()
        return self.formatter.format(rules)
