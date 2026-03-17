"""ルール管理・実行

複数 Rule を束ねて管理し、実行・一覧・検索を提供する。
"""

from collections.abc import Mapping
from pathlib import Path

from paladin.rule.protocol import MultiFileRule, Rule
from paladin.rule.types import RuleMeta, SourceFiles, Violation, Violations


class RuleSet:
    """複数 Rule を束ねて管理し、実行・一覧・検索を提供する"""

    def __init__(
        self,
        rules: tuple[Rule, ...],
        multi_file_rules: tuple[MultiFileRule, ...] = (),
    ) -> None:
        """RuleSetを初期化"""
        self._rules = rules
        self._multi_file_rules = multi_file_rules

    @property
    def rule_ids(self) -> frozenset[str]:
        """登録されている全ルールの ID セットを返す"""
        single_ids = frozenset(rule.meta.rule_id for rule in self._rules)
        multi_ids = frozenset(rule.meta.rule_id for rule in self._multi_file_rules)
        return single_ids | multi_ids

    def run(
        self,
        source_files: SourceFiles,
        disabled_rule_ids: frozenset[str] = frozenset(),
        per_file_disabled: Mapping[Path, frozenset[str]] | None = None,
    ) -> Violations:
        """全ファイルに全ルールを適用し、違反を集約して返す

        Args:
            source_files: 検査対象のソースファイル群
            disabled_rule_ids: スキップするルール ID の frozenset
            per_file_disabled: ファイルパスごとの disabled_rule_ids。指定されたファイルはこちらを優先使用する
        """
        violations: list[Violation] = []
        for source_file in source_files:
            effective_disabled = (
                per_file_disabled.get(source_file.file_path, disabled_rule_ids)
                if per_file_disabled is not None
                else disabled_rule_ids
            )
            for rule in self._rules:
                if rule.meta.rule_id in effective_disabled:
                    continue
                violations.extend(rule.check(source_file))
        for multi_rule in self._multi_file_rules:
            if multi_rule.meta.rule_id in disabled_rule_ids:
                continue
            violations.extend(multi_rule.check(source_files))
        return Violations(items=tuple(violations))

    def list_rules(self) -> tuple[RuleMeta, ...]:
        """登録済みルールのメタ情報一覧を返す"""
        return tuple(rule.meta for rule in self._rules) + tuple(
            rule.meta for rule in self._multi_file_rules
        )

    def find_rule(self, rule_id: str) -> RuleMeta | None:
        """指定した rule_id に一致する RuleMeta を返す。存在しない場合は None を返す"""
        for rule in self._rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        for rule in self._multi_file_rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        return None
