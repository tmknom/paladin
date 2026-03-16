"""View層の中核

ルール詳細取得とフォーマットの処理フロー全体を制御する。
"""

from paladin.foundation.log import log
from paladin.rule import RuleSet
from paladin.view.context import ViewContext
from paladin.view.formatter import ViewFormatter


class ViewOrchestrator:
    """ルール詳細取得とフォーマットの処理フローを制御する"""

    def __init__(
        self,
        rule_set: RuleSet,
        formatter: ViewFormatter,
    ) -> None:
        """ViewOrchestratorを初期化する"""
        self.rule_set = rule_set
        self.formatter = formatter

    @log
    def orchestrate(self, context: ViewContext) -> str:
        """指定された rule_id のルール詳細をフォーマットした文字列を返す"""
        rule = self.rule_set.find_rule(context.rule_id)
        if rule is None:
            return f"Error: Rule '{context.rule_id}' not found."
        return self.formatter.format(rule)
