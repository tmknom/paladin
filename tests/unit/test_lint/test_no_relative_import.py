import ast
from pathlib import Path

from paladin.lint.no_relative_import import NoRelativeImportRule
from paladin.lint.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestNoRelativeImportRuleMeta:
    """NoRelativeImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-relative-import"
        assert result.rule_name == "No Relative Import"
        assert result.summary == "相対インポートの使用を禁止する"
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoRelativeImportRuleCheck:
    """NoRelativeImportRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source_file = _make_source_file("from .module import Foo\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-relative-import"
        assert violation.rule_name == "No Relative Import"

    def test_check_正常系_絶対インポートのみの場合は空タプルを返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source_file = _make_source_file("from myapp.module import Foo\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数の相対インポートでそれぞれ個別の違反を返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source = "from . import Foo\nfrom ..bar import Baz\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_importノードは検出対象外であること(self):
        # Arrange
        rule = NoRelativeImportRule()
        source_file = _make_source_file("import os\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source_file = _make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
