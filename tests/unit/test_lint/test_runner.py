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
