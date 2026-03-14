"""ルールメタ情報の管理

登録済みルールの一覧取得・検索機能を提供する。
"""

from paladin.lint.protocol import Rule
from paladin.lint.types import RuleMeta


class RuleRegistry:
    """登録済みルールのRuleMeta一覧を管理・提供する"""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        """RuleRegistryを初期化"""
        self._rules = rules

    def list_rules(self) -> tuple[RuleMeta, ...]:
        """登録済みルールのメタ情報一覧を返す"""
        return tuple(rule.meta for rule in self._rules)

    def find_rule(self, rule_id: str) -> RuleMeta | None:
        """指定した rule_id に一致する RuleMeta を返す。存在しない場合は None を返す"""
        for rule in self._rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        return None
