"""Listパッケージのオーケストレーター

ルール一覧取得とフォーマットの処理フロー全体を制御する。
"""

from paladin.foundation.log import log
from paladin.list.context import ListContext
from paladin.list.formatter import ListFormatterFactory
from paladin.rule import RuleSet


class ListOrchestrator:
    """ルール一覧取得とフォーマットの処理フローを制御する"""

    def __init__(
        self,
        rule_set: RuleSet,
        formatter: ListFormatterFactory,
    ) -> None:
        """ListOrchestrator を初期化する"""
        self.rule_set = rule_set
        self.formatter = formatter

    @log
    def orchestrate(self, context: ListContext) -> str:
        """全ルール一覧をフォーマットした文字列を返す"""
        rules = self.rule_set.list_rules()
        return self.formatter.format(rules, context.format)
