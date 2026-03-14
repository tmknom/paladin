import ast
from pathlib import Path

from paladin.lint.runner import RuleRunner
from paladin.lint.types import Violation, Violations
from paladin.source.types import ParsedFile, ParsedFiles
from tests.unit.test_check.fakes import FakeRule


def _make_parsed_file(source: str, filename: str = "__init__.py") -> ParsedFile:
    return ParsedFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_parsed_files(*sources_and_names: tuple[str, str]) -> ParsedFiles:
    return ParsedFiles(files=tuple(_make_parsed_file(src, name) for src, name in sources_and_names))


def _make_violation(file: str = "src/paladin/__init__.py") -> Violation:
    return Violation(
        file=Path(file),
        line=1,
        column=0,
        rule_id="fake-rule",
        rule_name="Fake Rule",
        message="fake message",
        reason="fake reason",
        suggestion="fake suggestion",
    )


class TestRuleRunner:
    """RuleRunnerクラスのテスト"""

    def test_run_正常系_単一ルールの違反をViolationsとして返すこと(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(("x = 1\n", "__init__.py"))

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 1

    def test_run_正常系_違反なしの場合に空のViolationsを返すこと(self):
        # Arrange
        rule = FakeRule(violations=())
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(("x = 1\n", "__init__.py"))

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_エッジケース_空のParsedFilesで空のViolationsを返すこと(self):
        # Arrange
        rule = FakeRule(violations=(_make_violation(),))
        runner = RuleRunner(rules=(rule,))
        parsed_files = ParsedFiles(files=())

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_正常系_複数ファイルに同じルールを適用して違反を集約すること(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(
            ("x = 1\n", "a/__init__.py"),
            ("y = 2\n", "b/__init__.py"),
        )

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 2

    def test_run_正常系_disabled_rule_idsに該当するルールの違反をスキップすること(self):
        # Arrange
        violation_a = Violation(
            file=Path("src/__init__.py"),
            line=1,
            column=0,
            rule_id="rule-a",
            rule_name="Rule A",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        violation_b = Violation(
            file=Path("src/__init__.py"),
            line=1,
            column=0,
            rule_id="rule-b",
            rule_name="Rule B",
            message="msg",
            reason="reason",
            suggestion="suggestion",
        )
        rule_a = FakeRule(rule_id="rule-a", violations=(violation_a,))
        rule_b = FakeRule(rule_id="rule-b", violations=(violation_b,))
        runner = RuleRunner(rules=(rule_a, rule_b))
        parsed_files = _make_parsed_files(("x = 1\n", "__init__.py"))

        # Act
        result = runner.run(parsed_files, disabled_rule_ids=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 1
        assert result.items[0].rule_id == "rule-b"

    def test_run_エッジケース_disabled_rule_idsが空の場合全ルール実行すること(self):
        # Arrange
        violation = _make_violation()
        rule_a = FakeRule(rule_id="rule-a", violations=(violation,))
        rule_b = FakeRule(rule_id="rule-b", violations=(violation,))
        runner = RuleRunner(rules=(rule_a, rule_b))
        parsed_files = _make_parsed_files(("x = 1\n", "__init__.py"))

        # Act
        result = runner.run(parsed_files, disabled_rule_ids=frozenset())

        # Assert: 両ルールが実行される
        assert len(result) == 2

    def test_run_正常系_disabled_rule_idsのデフォルト値で全ルール実行すること(self):
        # Arrange
        violation = _make_violation()
        rule = FakeRule(violations=(violation,))
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(("x = 1\n", "__init__.py"))

        # Act: デフォルト引数（引数なし）で呼び出す
        result = runner.run(parsed_files)

        # Assert
        assert len(result) == 1

    def test_rule_ids_正常系_登録ルールのIDセットを返すこと(self):
        # Arrange
        rule_a = FakeRule(rule_id="rule-a")
        rule_b = FakeRule(rule_id="rule-b")
        runner = RuleRunner(rules=(rule_a, rule_b))

        # Act
        result = runner.rule_ids

        # Assert
        assert result == frozenset({"rule-a", "rule-b"})
