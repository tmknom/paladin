"""no_test_method_docstring モジュールのテスト"""

import ast

from paladin.rule.no_test_method_docstring import (
    NoTestMethodDocstringRule,
    TestMethodDocstringDetector,
)
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


def _make_function_node(source: str) -> ast.FunctionDef:
    """ソースコードから最初の ast.FunctionDef を取り出す"""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            return node
    raise AssertionError(f"ast.FunctionDef が見つかりません: {source!r}")


class TestTestMethodDocstringDetector:
    """TestMethodDocstringDetector のテスト"""

    def test_detect_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        source = 'def test_something():\n    """docstring"""\n    pass\n'
        node = _make_function_node(source)
        meta = NoTestMethodDocstringRule().meta
        source_file = make_test_source_file(source)

        # Act
        result = TestMethodDocstringDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None
        assert result.rule_id == "no-test-method-docstring"
        assert result.line == 1

    def test_detect_正常系_docstringなしのテストメソッドでNoneを返すこと(self):
        # Arrange
        source = "def test_something():\n    pass\n"
        node = _make_function_node(source)
        meta = NoTestMethodDocstringRule().meta
        source_file = make_test_source_file(source)

        # Act
        result = TestMethodDocstringDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_エッジケース_bodyが空の関数でNoneを返すこと(self):
        # Arrange
        # ast.parse では body が空の FunctionDef は生成できないため、手動で構築する
        node = ast.FunctionDef(
            name="test_something",
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[],
            decorator_list=[],
            returns=None,
            lineno=1,
            col_offset=0,
        )
        meta = NoTestMethodDocstringRule().meta
        source_file = make_test_source_file("")

        # Act
        result = TestMethodDocstringDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_エッジケース_Exprだが非Constant式の場合にNoneを返すこと(self):
        # Arrange
        # body[0] が ast.Expr だが value が ast.Name（変数参照）の場合
        source = "def test_something():\n    some_var\n"
        node = _make_function_node(source)
        meta = NoTestMethodDocstringRule().meta
        source_file = make_test_source_file(source)

        # Act
        result = TestMethodDocstringDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_エッジケース_Exprだが文字列定数でない場合にNoneを返すこと(self):
        # Arrange
        source = "def test_something():\n    42\n"
        node = _make_function_node(source)
        meta = NoTestMethodDocstringRule().meta
        source_file = make_test_source_file(source)

        # Act
        result = TestMethodDocstringDetector.detect(node, meta, source_file)

        # Assert
        assert result is None


class TestNoTestMethodDocstringRuleCheck:
    """NoTestMethodDocstringRule.check のテスト"""

    def test_check_正常系_docstringありのテストメソッドを違反として検出すること(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = 'def test_something():\n    """docstring"""\n    pass\n'
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-test-method-docstring"

    def test_check_正常系_複数のdocstringありテストメソッドを全件検出すること(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = (
            "def test_first():\n"
            '    """first docstring"""\n'
            "    pass\n"
            "\n"
            "def test_second():\n"
            '    """second docstring"""\n'
            "    pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = 'def test_something():\n    """docstring"""\n    pass\n'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_docstringなしのテストメソッドは空タプルを返すこと(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = "def test_something():\n    pass\n"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_testプレフィックスのないメソッドは検査対象外であること(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = (
            "def setUp():\n"
            '    """setUp docstring"""\n'
            "    pass\n"
            "\n"
            "def helper_method():\n"
            '    """helper docstring"""\n'
            "    pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_クラスのdocstringは検査対象外であること(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = (
            "class TestSomething:\n"
            '    """クラスの docstring"""\n'
            "\n"
            "    def test_method(self):\n"
            "        pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反の行番号がdef文の行番号であること(self):
        # Arrange
        rule = NoTestMethodDocstringRule()
        source = 'x = 1\n\ndef test_something():\n    """docstring"""\n    pass\n'
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 3


class TestNoTestMethodDocstringRuleMeta:
    """NoTestMethodDocstringRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報が正しいこと(self):
        # Arrange
        rule = NoTestMethodDocstringRule()

        # Act
        meta = rule.meta

        # Assert
        assert meta.rule_id == "no-test-method-docstring"
        assert meta.rule_name == "No Test Method Docstring"
