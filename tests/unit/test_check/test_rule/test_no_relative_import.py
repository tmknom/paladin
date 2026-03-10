import ast
from pathlib import Path

from paladin.check.rule.no_relative_import import NoRelativeImportRule
from paladin.check.types import ParsedFile, RuleMeta


def _make_parsed_file(source: str, filename: str = "example.py") -> ParsedFile:
    return ParsedFile(file_path=Path(filename), tree=ast.parse(source))


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


class TestNoRelativeImportRuleCheck:
    """NoRelativeImportRule.check のテスト"""

    def test_check_正常系_単一の相対インポートで違反を1件返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("from . import Foo\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("from .module import Foo\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-relative-import"
        assert violation.rule_name == "No Relative Import"
        assert violation.message == "相対インポートが使用されている（from .module import ...）"
        assert (
            violation.reason
            == "相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる"
        )
        assert (
            violation.suggestion
            == "プロジェクトルートからの絶対インポートに書き換える（例：from myapp.services.data import DataLoader）"
        )

    def test_check_正常系_絶対インポートのみの場合は空タプルを返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("from myapp.module import Foo\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数の相対インポートでそれぞれ個別の違反を返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source = "from . import Foo\nfrom ..bar import Baz\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_importノードは検出対象外であること(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("import os\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_level2以上のドット表記が正しいこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("from ..module import Bar\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1
        assert "..module" in result[0].message

    def test_check_エッジケース_moduleがNoneの場合ドットのみのメッセージになること(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("from . import Foo\n")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result[0].message == "相対インポートが使用されている（from . import ...）"

    def test_check_エッジケース_ネストされたスコープ内の相対インポートも検出すること(self):
        # Arrange
        rule = NoRelativeImportRule()
        source = "if True:\n    from . import Foo\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        parsed_file = _make_parsed_file("")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()
