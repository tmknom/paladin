"""Check層のルール適用

パイプライン第3段階として、全ルールを全ファイルへ適用し違反を集約する。
"""

from paladin.check.rule.protocol import Rule
from paladin.check.rule.types import Violation, Violations
from paladin.check.types import ParsedFiles


class RuleRunner:
    """複数Ruleを束ねてParsedFilesの各ファイルに適用し、Violationsを返す"""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        """RuleRunnerを初期化"""
        self._rules = rules

    def run(self, parsed_files: ParsedFiles) -> Violations:
        """全ファイルに全ルールを適用し、違反を集約して返す"""
        violations: list[Violation] = []
        for parsed_file in parsed_files:
            for rule in self._rules:
                violations.extend(rule.check(parsed_file))
        return Violations(items=tuple(violations))
