"""ルール適用

全ルールを全ファイルへ適用し違反を集約する。
"""

from paladin.lint.protocol import Rule
from paladin.lint.types import Violation, Violations
from paladin.source.types import ParsedFiles


class RuleRunner:
    """複数Ruleを束ねてParsedFilesの各ファイルに適用し、Violationsを返す"""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        """RuleRunnerを初期化"""
        self._rules = rules

    @property
    def rule_ids(self) -> frozenset[str]:
        """登録されている全ルールの ID セットを返す"""
        return frozenset(rule.meta.rule_id for rule in self._rules)

    def run(
        self,
        parsed_files: ParsedFiles,
        disabled_rule_ids: frozenset[str] = frozenset(),
    ) -> Violations:
        """全ファイルに全ルールを適用し、違反を集約して返す

        Args:
            parsed_files: 解析済みファイル群
            disabled_rule_ids: スキップするルール ID の frozenset
        """
        violations: list[Violation] = []
        for parsed_file in parsed_files:
            for rule in self._rules:
                if rule.meta.rule_id in disabled_rule_ids:
                    continue
                violations.extend(rule.check(parsed_file))
        return Violations(items=tuple(violations))
