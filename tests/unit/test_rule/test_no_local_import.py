from pathlib import Path

from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


class TestNoLocalImportRuleMeta:
    """NoLocalImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-local-import"
        assert result.rule_name == "No Local Import"
        assert result.summary == "ローカルインポートの使用を禁止する"
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoLocalImportRuleCheck:
    """NoLocalImportRule.check のテスト"""

    def test_check_正常系_関数内importで違反を1件返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_関数内from_importで違反を1件返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    from os import path\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 2
        assert violation.column == 4
        assert violation.rule_id == "no-local-import"
        assert violation.rule_name == "No Local Import"

    def test_check_正常系_クラス直下importで違反を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "class Foo:\n    import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "クラス Foo 内に import 文があります"

    def test_check_正常系_メソッド内importでメソッドスコープの違反を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "class Foo:\n    def bar(self):\n        import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "メソッド Foo.bar 内に import 文があります"

    def test_check_正常系_ネスト関数内importで最内スコープの違反を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def outer():\n    def inner():\n        import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "関数 inner 内に import 文があります"

    def test_check_正常系_async_def内importで違反を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "async def foo():\n    import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "関数 foo 内に import 文があります"

    def test_check_正常系_複数箇所の違反をすべて返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\ndef bar():\n    from sys import argv\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_トップレベルimportは違反なしを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "import os\nfrom sys import argv\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_TYPE_CHECKINGブロック内importは違反なしを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = (
            "from __future__ import annotations\n"
            "TYPE_CHECKING = False\n"
            "if TYPE_CHECKING:\n"
            "    import os\n"
        )
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_TYPE_CHECKING属性アクセス形式も違反なしを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = (
            "from __future__ import annotations\n"
            "import typing\n"
            "if typing.TYPE_CHECKING:\n"
            "    import os\n"
        )
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source_file = make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_importを含まないソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    x = 1\n    return x\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
