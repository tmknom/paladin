"""require-docstring ルールのテスト"""

import ast

import pytest

from paladin.rule.require_docstring import (
    ClassDocstringDetector,
    DocstringChecker,
    ModuleDocstringDetector,
    RequireDocstringRule,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


class TestDocstringChecker:
    """DocstringChecker クラスのテスト"""

    def test_has_docstring_正常系_docstringがある場合Trueを返すこと(self):
        # Arrange
        tree = ast.parse('"""docstring"""\nx = 1')

        # Act / Assert
        assert DocstringChecker.has_docstring(tree.body) is True

    def test_has_docstring_正常系_docstringがない場合Falseを返すこと(self):
        # Arrange
        tree = ast.parse("x = 1")

        # Act / Assert
        assert DocstringChecker.has_docstring(tree.body) is False

    def test_has_docstring_エッジケース_bodyが空の場合Falseを返すこと(self):
        # Act / Assert
        assert DocstringChecker.has_docstring([]) is False

    def test_is_empty_source_正常系_空文字列でTrueを返すこと(self):
        # Act / Assert
        assert DocstringChecker.is_empty_source("") is True

    def test_is_empty_source_正常系_空白のみでTrueを返すこと(self):
        # Act / Assert
        assert DocstringChecker.is_empty_source("   \n  ") is True

    def test_is_empty_source_正常系_コードがある場合Falseを返すこと(self):
        # Act / Assert
        assert DocstringChecker.is_empty_source("x = 1") is False


class TestModuleDocstringDetector:
    """ModuleDocstringDetector クラスのテスト"""

    @pytest.fixture
    def meta(self) -> RuleMeta:
        return RequireDocstringRule().meta

    def test_detect_正常系_docstringがない場合Violationを返すこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file("x = 1\n")

        # Act
        result = ModuleDocstringDetector.detect(source_file, meta)

        # Assert
        assert result is not None
        assert result.line == 1
        assert "example.py" in result.message

    def test_detect_正常系_docstringがある場合Noneを返すこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file('"""doc"""\nx = 1\n')

        # Act
        result = ModuleDocstringDetector.detect(source_file, meta)

        # Assert
        assert result is None

    def test_detect_エッジケース_空ファイルの場合Noneを返すこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file("")

        # Act
        result = ModuleDocstringDetector.detect(source_file, meta)

        # Assert
        assert result is None

    def test_detect_エッジケース_空白のみのファイルの場合Noneを返すこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file("   \n  \n")

        # Act
        result = ModuleDocstringDetector.detect(source_file, meta)

        # Assert
        assert result is None

    def test_detect_正常系_Violationのフィールド値が正しいこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file("x = 1\n")

        # Act
        result = ModuleDocstringDetector.detect(source_file, meta)

        # Assert
        assert result is not None
        assert result.rule_id == "require-docstring"
        assert "example.py" in result.message
        assert "モジュール" in result.reason
        assert result.suggestion != ""


class TestClassDocstringDetector:
    """ClassDocstringDetector クラスのテスト"""

    @pytest.fixture
    def meta(self) -> RuleMeta:
        return RequireDocstringRule().meta

    def _get_class_node(self, source: str) -> ast.ClassDef:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return node
        raise ValueError("ClassDef not found")

    def test_detect_正常系_クラスにdocstringがない場合Violationを返すこと(self, meta: RuleMeta):
        # Arrange
        source = "class Foo:\n    pass\n"
        source_file = make_source_file(source)
        class_node = self._get_class_node(source)

        # Act
        result = ClassDocstringDetector.detect(class_node, source_file, meta)

        # Assert
        assert result is not None
        assert result.line == class_node.lineno

    def test_detect_正常系_クラスにdocstringがある場合Noneを返すこと(self, meta: RuleMeta):
        # Arrange
        source = 'class Foo:\n    """doc"""\n    pass\n'
        source_file = make_source_file(source)
        class_node = self._get_class_node(source)

        # Act
        result = ClassDocstringDetector.detect(class_node, source_file, meta)

        # Assert
        assert result is None

    def test_detect_正常系_Violationのmessageにクラス名が含まれること(self, meta: RuleMeta):
        # Arrange
        source = "class Foo:\n    pass\n"
        source_file = make_source_file(source)
        class_node = self._get_class_node(source)

        # Act
        result = ClassDocstringDetector.detect(class_node, source_file, meta)

        # Assert
        assert result is not None
        assert "Foo" in result.message


class TestRequireDocstringRuleMeta:
    """RequireDocstringRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = RequireDocstringRule()

        # Act / Assert
        assert isinstance(rule.meta, RuleMeta)
        assert rule.meta.rule_id == "require-docstring"


class TestRequireDocstringRuleCheck:
    """RequireDocstringRule.check のテスト"""

    @pytest.fixture
    def rule(self) -> RequireDocstringRule:
        return RequireDocstringRule()

    def test_check_正常系_モジュールdocstringがない場合に違反を返すこと(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source_file = make_source_file("x = 1\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "require-docstring"

    def test_check_正常系_クラスdocstringがない場合に違反を返すこと(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = '"""module doc"""\n\nclass Foo:\n    pass\n'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "Foo" in result[0].message

    def test_check_正常系_モジュールとクラス両方にdocstringがない場合に2件の違反を返すこと(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = "class Foo:\n    pass\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_全てにdocstringがある場合に違反なしを返すこと(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = '"""module doc"""\n\nclass Foo:\n    """class doc"""\n    pass\n'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_複数クラスにdocstringがない場合にクラス数分の違反を返すこと(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = '"""module doc"""\n\nclass Foo:\n    pass\n\nclass Bar:\n    pass\n'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_エッジケース_ネストしたクラスのdocstringも検査すること(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = (
            '"""module doc"""\n\n'
            "class Outer:\n"
            '    """outer doc"""\n\n'
            "    class Inner:\n"
            "        pass\n"
        )
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "Inner" in result[0].message

    def test_check_エッジケース_テストファイルはdocstringチェック対象外であること(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = "class TestFoo:\n    pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        # テストファイルはモジュール docstring もクラス docstring も検査しない
        assert result == ()

    def test_check_エッジケース_空ファイルは違反なしを返すこと(self, rule: RequireDocstringRule):
        # Arrange
        source_file = make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_違反のline番号がclass文の行番号であること(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source = '"""module doc"""\n\n\nclass Foo:\n    pass\n'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 4  # class Foo は4行目

    def test_check_正常系_モジュールdocstring違反のline番号が1であること(
        self, rule: RequireDocstringRule
    ):
        # Arrange
        source_file = make_source_file("x = 1\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 1
