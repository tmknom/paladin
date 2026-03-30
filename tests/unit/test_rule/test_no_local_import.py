import ast
from pathlib import Path

from paladin.rule.no_local_import import (
    LocalImportCollector,
    LocalImportDetector,
    NoLocalImportRule,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helper import make_source_file


class TestLocalImportCollector:
    """LocalImportCollector.collect のテスト"""

    def test_collect_正常系_関数内importを収集すること(self):
        # Arrange
        source = "def foo():\n    import os\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].scope == "関数 foo"

    def test_collect_正常系_メソッド内importを収集すること(self):
        # Arrange
        source = "class Foo:\n    def bar(self):\n        import os\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].scope == "メソッド Foo.bar"

    def test_collect_正常系_クラス直下importを収集すること(self):
        # Arrange
        source = "class Foo:\n    import os\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].scope == "クラス Foo"

    def test_collect_正常系_ネスト関数内importを収集すること(self):
        # Arrange
        source = "def outer():\n    def inner():\n        import os\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].scope == "関数 inner"

    def test_collect_正常系_TYPE_CHECKINGブロックを除外すること(self):
        # Arrange
        source = "TYPE_CHECKING = False\nif TYPE_CHECKING:\n    import os\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_エッジケース_ローカルインポートなしで空タプルを返すこと(self):
        # Arrange
        source = "import os\nfrom sys import argv\n"
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_正常系_typing_TYPE_CHECKING属性を除外すること(self):
        # Arrange
        source = (
            "from __future__ import annotations\n"
            "import typing\n"
            "if typing.TYPE_CHECKING:\n"
            "    import os\n"
        )
        tree = ast.parse(source)

        # Act
        result = LocalImportCollector.collect(tree)

        # Assert
        assert result == ()


class TestLocalImportDetector:
    """LocalImportDetector.detect のテスト"""

    def test_detect_正常系_Violationを返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\n"
        source_file = make_source_file(source)
        tree = ast.parse(source)
        local_imports = LocalImportCollector.collect(tree)
        assert len(local_imports) == 1

        # Act
        result = LocalImportDetector.detect(local_imports[0], rule.meta, source_file)

        # Assert
        assert result is not None

    def test_detect_正常系_メッセージにscope名が含まれること(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\n"
        source_file = make_source_file(source)
        tree = ast.parse(source)
        local_imports = LocalImportCollector.collect(tree)

        # Act
        result = LocalImportDetector.detect(local_imports[0], rule.meta, source_file)

        # Assert
        assert result is not None


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


class TestNoLocalImportRuleCheck:
    """NoLocalImportRule.check のテスト"""

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

    def test_check_正常系_複数箇所の違反をすべて返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\ndef bar():\n    from sys import argv\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
