"""Rules層の中核

ルール一覧取得とフォーマットの処理フロー全体を制御する。
"""

from paladin.foundation.log import log
from paladin.lint import RuleRegistry
from paladin.rules.context import RulesContext
from paladin.rules.detail_formatter import RulesDetailFormatter
from paladin.rules.formatter import RulesFormatter


class RulesOrchestrator:
    """ルール一覧取得とフォーマットの処理フローを制御する"""

    def __init__(
        self,
        registry: RuleRegistry,
        formatter: RulesFormatter,
        detail_formatter: RulesDetailFormatter,
    ) -> None:
        """RulesOrchestratorを初期化する"""
        self.registry = registry
        self.formatter = formatter
        self.detail_formatter = detail_formatter

    @log
    def orchestrate(self, context: RulesContext) -> str:
        """コンテキストに応じてルール一覧または詳細をフォーマットした文字列を返す"""
        if context.rule_id is None:
            rules = self.registry.list_rules()
            return self.formatter.format(rules)

        rule = self.registry.find_rule(context.rule_id)
        if rule is None:
            return f"Error: Rule '{context.rule_id}' not found."
        return self.detail_formatter.format(rule)
