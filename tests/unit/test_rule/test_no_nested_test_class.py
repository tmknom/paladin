"""no_nested_test_class モジュールのテスト"""

import ast

from paladin.rule.no_nested_test_class import NestedClassDetector, NoNestedTestClassRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


def _make_class_def(name: str, lineno: int = 1) -> ast.ClassDef:
    """テスト用の ast.ClassDef ノードを生成する"""
    source = f"class {name}:\n    pass"
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            node.lineno = lineno
            return node
    raise AssertionError(f"ast.ClassDef が見つかりません: {name!r}")


def _make_meta() -> RuleMeta:
    return RuleMeta(
        rule_id="no-nested-test-class",
        rule_name="No Nested Test Class",
        summary="テストクラス内へのクラスのネストを禁止する",
        intent="テストクラスのネストは可読性を下げるため、フラットな構造を維持する",
        guidance="テストファイル内のトップレベルクラスの body に ClassDef が存在する場合に違反を検出する",
        suggestion="ネストされたクラスをトップレベルのテストクラスとして独立させてください",
    )


class TestNestedClassDetector:
    """NestedClassDetector のテスト"""

    def test_detect_正常系_Violationが正しく生成されること(self):
        # Arrange
        outer_class = _make_class_def("TestOuter", lineno=1)
        inner_class = _make_class_def("InnerClass", lineno=5)
        meta = _make_meta()
        source_file = make_test_source_file("class TestOuter:\n    class InnerClass:\n        pass")

        # Act
        result = NestedClassDetector.detect(outer_class, inner_class, meta, source_file)

        # Assert
        assert result.rule_id == "no-nested-test-class"
        assert "TestOuter" in result.message
        assert "InnerClass" in result.message
        assert result.line == 5


class TestNoNestedTestClassRuleCheck:
    """NoNestedTestClassRule.check のテスト"""

    def test_check_正常系_ネストされたクラスを違反として検出すること(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class TestOuter:\n    class InnerClass:\n        pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-nested-test-class"

    def test_check_正常系_複数のネストクラスをすべて検出すること(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = (
            "class TestOuter:\n    class InnerA:\n        pass\n    class InnerB:\n        pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_複数のトップレベルクラスのネストをすべて検出すること(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = (
            "class TestFirst:\n"
            "    class InnerA:\n"
            "        pass\n"
            "class TestSecond:\n"
            "    class InnerB:\n"
            "        pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class Outer:\n    class Inner:\n        pass\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ネストなしのテストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class TestFlat:\n    def test_something(self):\n        pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_トップレベルClassDef以外のノードはスキップすること(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "def top_level_func():\n    pass\nclass TestOuter:\n    def test_something(self):\n        pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反の行番号がネストされたclass文の行番号であること(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = (
            "class TestOuter:\n    class InnerA:\n        pass\n    class InnerB:\n        pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        lines = {v.line for v in result}
        assert 2 in lines
        assert 4 in lines

    def test_check_エッジケース_クラス内のメソッド定義は違反としないこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class TestOuter:\n    def test_something(self):\n        pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_空のクラスは違反としないこと(self):
        # Arrange
        rule = NoNestedTestClassRule()
        source = "class TestOuter:\n    pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
