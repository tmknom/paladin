"""Checkパッケージのルールフィルタリング

設定ファイルの rules セクションに基づいてルールの有効/無効を管理する。
"""

import logging

from paladin.rule import Rule

logger = logging.getLogger(__name__)


class RuleFilter:
    """設定ファイルの rules セクションに基づいてルールの有効/無効を解決するフィルター"""

    def resolve_disabled_rules(
        self,
        rules: dict[str, bool],
        known_rule_ids: frozenset[str],
        select_rules: frozenset[str] = frozenset(),
    ) -> frozenset[str]:
        """設定ファイルの rules から無効ルール ID を解決する

        Args:
            rules: ルール ID をキー、有効/無効を値とする dict
            known_rule_ids: 既知のルール ID セット
            select_rules: 適用を限定するルールID群（空の場合は全ルール適用）

        Returns:
            無効化されたルール ID の frozenset。未知のルール ID は警告して除外する
        """
        disabled: set[str] = set()
        disabled.update(self._resolve_select_disabled(select_rules, known_rule_ids))
        disabled.update(self._resolve_rules_disabled(rules, known_rule_ids))
        return frozenset(disabled)

    def _resolve_select_disabled(
        self, select_rules: frozenset[str], known_rule_ids: frozenset[str]
    ) -> frozenset[str]:
        if not select_rules:
            return frozenset()
        for rule_id in select_rules - known_rule_ids:
            logger.warning("Unknown rule ID in --rule: %s", rule_id)
        return known_rule_ids - select_rules

    def _resolve_rules_disabled(
        self, rules: dict[str, bool], known_rule_ids: frozenset[str]
    ) -> frozenset[str]:
        disabled: set[str] = set()
        for rule_id, enabled in rules.items():
            if enabled:
                continue
            if rule_id not in known_rule_ids:
                logger.warning("Unknown rule ID in [tool.paladin.rules]: %s", rule_id)
                continue
            disabled.add(rule_id)
        return frozenset(disabled)

    def filter(
        self,
        rules: tuple[Rule, ...],
        disabled_rule_ids: frozenset[str],
    ) -> tuple[Rule, ...]:
        """無効ルール ID に該当するルールを除外したタプルを返す

        Args:
            rules: フィルタリング対象のルールタプル
            disabled_rule_ids: 無効化するルール ID の frozenset

        Returns:
            有効なルールのみを含むタプル
        """
        return tuple(rule for rule in rules if rule.meta.rule_id not in disabled_rule_ids)
