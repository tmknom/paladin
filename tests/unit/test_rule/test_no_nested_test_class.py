"""no_nested_test_class モジュールのテスト"""

import ast

from paladin.rule.no_nested_test_class import (
    NestedClassDetector,
    NestedTestClassCollector,
    NoNestedTestClassRule,
)
from paladin.rule.types import DetectionContext
from tests.unit.test_rule.helper import SourceFileFactory


class ClassDefFactory:
    @staticmethod
    def make(name: str, lineno: int = 1) -> ast.ClassDef:
        source = f"class {name}:\n    pass"
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                node.lineno = lineno
                return node
        raise AssertionError(f"ast.ClassDef が見つかりません: {name!r}")


class TestNestedTestClassCollector:
    """NestedTestClassCollector.collect のテスト"""

    def test_collect_正常系_ネストされたClassDefをペアで返すこと(self):
        # Arrange
        source = "class TestOuter:\n    class InnerClass:\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert len(result) == 1
        outer, inner = result[0]
        assert outer.name == "TestOuter"
        assert inner.name == "InnerClass"

    def test_collect_正常系_複数のinnerクラスをすべて収集すること(self):
        # Arrange
        source = (
            "class TestOuter:\n    class InnerA:\n        pass\n    class InnerB:\n        pass\n"
        )
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert len(result) == 2
        inner_names = {inner.name for _, inner in result}
        assert inner_names == {"InnerA", "InnerB"}

    def test_collect_正常系_複数のouterクラスから収集すること(self):
        # Arrange
        source = (
            "class TestFirst:\n"
            "    class InnerA:\n"
            "        pass\n"
            "class TestSecond:\n"
            "    class InnerB:\n"
            "        pass\n"
        )
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert len(result) == 2
        outer_names = {outer.name for outer, _ in result}
        assert outer_names == {"TestFirst", "TestSecond"}

    def test_collect_正常系_トップレベルがClassDef以外のノードはスキップすること(self):
        # Arrange
        source = "def top_level_func():\n    pass\nclass TestOuter:\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_正常系_innerがClassDef以外のノードはスキップすること(self):
        # Arrange
        source = "class TestOuter:\n    def test_something(self):\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_エッジケース_ネストなしで空タプルを返すこと(self):
        # Arrange
        source = "class TestOuter:\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = NestedTestClassCollector.collect(tree)

        # Assert
        assert result == ()


class TestNestedClassDetector:
    """NestedClassDetector.detect のテスト"""

    def test_detect_正常系_Violationが正しく生成されること(self):
        # Arrange
        outer_class = ClassDefFactory.make("TestOuter", lineno=1)
        inner_class = ClassDefFactory.make("InnerClass", lineno=5)
        meta = NoNestedTestClassRule().meta
        source_file = SourceFileFactory.make_test(
            "class TestOuter:\n    class InnerClass:\n        pass"
        )
        ctx = DetectionContext(meta=meta, source_file=source_file)

        # Act
        result = NestedClassDetector.detect(ctx, outer_class, inner_class)

        # Assert
        assert result.rule_id == "no-nested-test-class"
        assert result.line == 5


class TestNoNestedTestClassRuleCheck:
    """NoNestedTestClassRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class TestOuter:\n    class InnerClass:\n        pass\n"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class Outer:\n    class Inner:\n        pass\n"
        source_file = SourceFileFactory.make(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
