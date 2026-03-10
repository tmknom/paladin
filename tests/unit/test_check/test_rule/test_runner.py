import ast
from pathlib import Path

from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.runner import RuleRunner
from paladin.check.types import ParsedFile, ParsedFiles, Violations


def _make_parsed_file(source: str, filename: str = "__init__.py") -> ParsedFile:
    return ParsedFile(file_path=Path(filename), tree=ast.parse(source))


def _make_parsed_files(*sources_and_names: tuple[str, str]) -> ParsedFiles:
    return ParsedFiles(files=tuple(_make_parsed_file(src, name) for src, name in sources_and_names))


class TestRuleRunner:
    """RuleRunnerクラスのテスト"""

    def test_run_正常系_単一ルールの違反をViolationsとして返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(("from foo import bar\n", "__init__.py"))

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 1

    def test_run_正常系_違反なしの場合に空のViolationsを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(('__all__ = ["Foo"]\n', "__init__.py"))

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_エッジケース_空のParsedFilesで空のViolationsを返すこと(self):
        # Arrange
        rule = RequireAllExportRule()
        runner = RuleRunner(rules=(rule,))
        parsed_files = ParsedFiles(files=())

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 0

    def test_run_正常系_複数ファイルに同じルールを適用して違反を集約すること(self):
        # Arrange
        rule = RequireAllExportRule()
        runner = RuleRunner(rules=(rule,))
        parsed_files = _make_parsed_files(
            ("from foo import bar\n", "__init__.py"),  # 違反あり
            ('__all__ = ["Bar"]\n', "__init__.py"),  # 違反なし
        )

        # Act
        result = runner.run(parsed_files)

        # Assert
        assert isinstance(result, Violations)
        assert len(result) == 1
