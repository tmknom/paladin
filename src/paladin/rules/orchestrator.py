"""RulesOrchestratorの実装"""

from paladin.check.rule.registry import RuleRegistry
from paladin.foundation.log import log
from paladin.rules.formatter import RulesFormatter


class RulesOrchestrator:
    """ルール一覧取得とフォーマットの処理フローを制御する"""

    def __init__(self, registry: RuleRegistry, formatter: RulesFormatter) -> None:
        """RulesOrchestratorを初期化する"""
        self.registry = registry
        self.formatter = formatter

    @log
    def orchestrate(self) -> str:
        """登録済みルールの一覧をフォーマットした文字列を返す"""
        rules = self.registry.list_rules()
        return self.formatter.format(rules)
