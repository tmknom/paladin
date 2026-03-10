"""RuleRegistryの実装"""

from paladin.check.rule.protocol import Rule
from paladin.check.types import RuleMeta


class RuleRegistry:
    """登録済みルールのRuleMeta一覧を管理・提供する"""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        """RuleRegistryを初期化"""
        self._rules = rules

    def list_rules(self) -> tuple[RuleMeta, ...]:
        """登録済みルールのメタ情報一覧を返す"""
        return tuple(rule.meta for rule in self._rules)
