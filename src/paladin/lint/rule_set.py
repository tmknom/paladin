"""ルール管理・実行

複数 Rule を束ねて管理し、実行・一覧・検索を提供する。
"""

from paladin.lint.protocol import Rule
from paladin.lint.types import RuleMeta, SourceFiles, Violation, Violations


class RuleSet:
    """複数 Rule を束ねて管理し、実行・一覧・検索を提供する"""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        """RuleSetを初期化"""
        self._rules = rules

    @property
    def rule_ids(self) -> frozenset[str]:
        """登録されている全ルールの ID セットを返す"""
        return frozenset(rule.meta.rule_id for rule in self._rules)

    def run(
        self,
        source_files: SourceFiles,
        disabled_rule_ids: frozenset[str] = frozenset(),
    ) -> Violations:
        """全ファイルに全ルールを適用し、違反を集約して返す

        Args:
            source_files: 検査対象のソースファイル群
            disabled_rule_ids: スキップするルール ID の frozenset
        """
        violations: list[Violation] = []
        for source_file in source_files:
            for rule in self._rules:
                if rule.meta.rule_id in disabled_rule_ids:
                    continue
                violations.extend(rule.check(source_file))
        return Violations(items=tuple(violations))

    def list_rules(self) -> tuple[RuleMeta, ...]:
        """登録済みルールのメタ情報一覧を返す"""
        return tuple(rule.meta for rule in self._rules)

    def find_rule(self, rule_id: str) -> RuleMeta | None:
        """指定した rule_id に一致する RuleMeta を返す。存在しない場合は None を返す"""
        for rule in self._rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        return None
