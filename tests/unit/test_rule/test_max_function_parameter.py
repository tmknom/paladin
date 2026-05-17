"""max_function_parameter モジュールのユニットテスト"""

import ast
from pathlib import Path

import pytest

from paladin.rule.max_function_parameter import (
    DecoratorAllowChecker,
    FunctionCollector,
    FunctionScope,
    MaxFunctionParameterRule,
    ParameterCounter,
    ParameterLimitDetector,
)
from paladin.rule.types import DetectionContext
from tests.unit.test_rule.helper import SourceFileFactory


class FunctionScopeBuilder:
    @staticmethod
    def parse(source: str, is_method: bool) -> FunctionScope:
        tree = ast.parse(source)
        node = tree.body[0]
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        return FunctionScope(node=node, is_method=is_method)


class TestFunctionCollector:
    """FunctionCollector.collect() のテスト"""

    def test_collect_正常系_トップレベル関数を収集すること(self):
        # Arrange
        source = "def foo(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].is_method is False
        assert result[0].node.name == "foo"

    def test_collect_正常系_クラス内メソッドをis_method_Trueで収集すること(self):
        # Arrange
        source = "class C:\n    def m(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].is_method is True
        assert result[0].node.name == "m"

    def test_collect_正常系_関数内クラスのメソッドをis_method_Trueで収集すること(self):
        # Arrange
        source = "def outer():\n    class Local:\n        def m(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 2
        outer_scope = next(s for s in result if s.node.name == "outer")
        m_scope = next(s for s in result if s.node.name == "m")
        assert outer_scope.is_method is False
        assert m_scope.is_method is True

    def test_collect_正常系_ネストクラスのメソッドを収集すること(self):
        # Arrange
        source = "class Outer:\n    class Inner:\n        def m(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].is_method is True

    def test_collect_正常系_ネスト関数をis_method_Falseで収集すること(self):
        # Arrange
        source = "def outer():\n    def inner(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 2
        names = {s.node.name for s in result}
        assert names == {"outer", "inner"}
        for scope in result:
            assert scope.is_method is False

    def test_collect_エッジケース_関数なしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert result == ()


class TestDecoratorAllowChecker:
    """DecoratorAllowChecker のテスト"""

    def test_decorator_name_正常系_Name表記の名前を返すこと(self):
        # Arrange
        node = ast.parse("@fixture\ndef f(): pass").body[0]
        assert isinstance(node, ast.FunctionDef)
        decorator: ast.expr = node.decorator_list[0]

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "fixture"

    def test_decorator_name_正常系_Attribute表記のドット連結を返すこと(self):
        # Arrange
        node = ast.parse("@pytest.fixture\ndef f(): pass").body[0]
        assert isinstance(node, ast.FunctionDef)
        decorator: ast.expr = node.decorator_list[0]

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "pytest.fixture"

    def test_decorator_name_正常系_Call表記のfuncを再帰的に文字列化すること(self):
        # Arrange
        node = ast.parse('@pytest.fixture(scope="module")\ndef f(): pass').body[0]
        assert isinstance(node, ast.FunctionDef)
        decorator: ast.expr = node.decorator_list[0]

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result == "pytest.fixture"

    @pytest.mark.parametrize(
        "decorator",
        [
            ast.Constant(value=42),
            ast.Attribute(value=ast.Constant(value=1), attr="foo", ctx=ast.Load()),
        ],
        ids=["Constant式", "解決不能Attribute"],
    )
    def test_decorator_name_エッジケース_文字列化不能な式でNoneを返すこと(
        self, decorator: ast.expr
    ):
        # Arrange: Constant と Attribute(Constant, attr) はどちらも解決不能

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result is None


class TestParameterCounter:
    """ParameterCounter.count() のテスト"""

    @pytest.mark.parametrize(
        ("source", "is_method", "expected"),
        [
            ("def f(): pass", False, 0),
            ("def f(a, b, c): pass", False, 3),
            ("def m(self, a, b): pass", True, 2),
            ("def m(cls, a, b): pass", True, 2),
            ("@staticmethod\ndef m(a, b, c): pass", True, 3),
            ("def f(a, *args): pass", False, 2),
            ("def f(a, **kwargs): pass", False, 2),
            ("def f(a, /, b, *, c): pass", False, 3),
            ("def f(a, *args, **kwargs): pass", False, 3),
            ("def m(other, a): pass", True, 2),
            ("@staticmethod\ndef m(): pass", True, 0),
            ("def m(): pass", True, 0),
            ("def m(self, /, a, b): pass", True, 2),
        ],
        ids=[
            "引数なし",
            "位置引数のみ",
            "self除外",
            "cls除外",
            "staticmethodはselfを除外しない",
            "varargを1としてカウント",
            "kwargを1としてカウント",
            "posonlyargsとkwonlyargsを合算",
            "vararg_kwarg両方を加算",
            "メソッドの第1引数がselfでない場合は除外しない",
            "引数なしstaticmethodで0",
            "引数なしメソッドで0",
            "posonlyargs先頭がselfの場合除外",
        ],
    )
    def test_count_正常系(self, source: str, is_method: bool, expected: int):
        # Act & Assert
        scope = FunctionScopeBuilder.parse(source, is_method=is_method)
        assert ParameterCounter.count(scope) == expected


class TestParameterLimitDetector:
    """ParameterLimitDetector.detect() のテスト"""

    def test_detect_正常系_上限以内でNoneを返すこと(self):
        # Arrange
        source_file = SourceFileFactory.make("def foo(a, b, c): pass")
        scope = FunctionScopeBuilder.parse("def foo(a, b, c): pass", is_method=False)
        ctx = DetectionContext(meta=MaxFunctionParameterRule().meta, source_file=source_file)

        # Act
        result = ParameterLimitDetector.detect(scope, count=3, limit=3, ctx=ctx)

        # Assert
        assert result is None

    def test_detect_正常系_上限超過でViolationを返すこと(self):
        # Arrange
        source_file = SourceFileFactory.make("def foo(a, b, c, d): pass")
        scope = FunctionScopeBuilder.parse("def foo(a, b, c, d): pass", is_method=False)
        ctx = DetectionContext(meta=MaxFunctionParameterRule().meta, source_file=source_file)

        # Act
        result = ParameterLimitDetector.detect(scope, count=4, limit=3, ctx=ctx)

        # Assert
        assert result is not None

    def test_detect_正常系_violationのフィールド値が正しいこと(self):
        # Arrange: 3行目に def が来るソース
        source = "\n\ndef foo(a, b, c, d): pass"
        source_file = SourceFileFactory.make(source)
        tree = ast.parse(source)
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        scope = FunctionScope(node=node, is_method=False)
        ctx = DetectionContext(meta=MaxFunctionParameterRule().meta, source_file=source_file)

        # Act
        result = ParameterLimitDetector.detect(scope, count=4, limit=3, ctx=ctx)

        # Assert
        assert result is not None
        assert result.line == 3
        assert result.rule_id == "max-function-parameter"
        assert result.rule_name == "Max Function Parameter"
        assert result.reason != ""
        assert result.suggestion != ""


class TestMaxFunctionParameterRule:
    """MaxFunctionParameterRule のテスト"""

    def test_meta_正常系_メタ情報が正しく設定されていること(self):
        # Arrange
        rule = MaxFunctionParameterRule()

        # Act & Assert
        assert rule.meta.rule_id == "max-function-parameter"
        assert rule.meta.rule_name == "Max Function Parameter"
        assert rule.meta.config_example is not None
        assert rule.meta.detection_example is not None

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        source = "def foo(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].file == Path("example.py")
        assert result[0].line == 1
        assert result[0].rule_id == "max-function-parameter"

    def test_check_正常系_self除外で上限以内なら違反なしを返すこと(self):
        # Arrange: self を除いて4引数 = 上限内
        source = "class C:\n    def m(self, a, b, c, d): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_staticmethodは第1引数を除外しないこと(self):
        # Arrange: @staticmethod なので除外なし → 5引数で違反
        source = "class C:\n    @staticmethod\n    def m(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_pytest_fixtureデコレータ付き関数は違反としないこと(self):
        # Arrange
        source = "@pytest.fixture\ndef f(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_fixture単独デコレータも違反としないこと(self):
        # Arrange
        source = "@fixture\ndef f(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_AsyncFunctionDefも違反として検出すること(self):
        # Arrange
        source = "async def f(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_parametersが適用されること(self):
        # Arrange: max_parameters=2 で def f(a,b,c) は違反
        source = "def f(a, b, c): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule(max_parameters=2)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムallow_decoratorsを尊重すること(self):
        # Arrange: @dataclass を許可リストに追加
        source = "@dataclass\ndef f(a, b, c, d, e): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule(allow_decorators=("dataclass",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数の違反を定義順に報告すること(self):
        # Arrange
        source = "def f1(a, b, c, d, e): pass\ndef f2(a, b, c, d, e, f): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        assert result[0].line < result[1].line

    def test_check_正常系_varargとkwargを加算してカウントすること(self):
        # Arrange: def f(a, b, *args, **kwargs) → 4引数で違反なし
        source_ok = "def f(a, b, *args, **kwargs): pass"
        # Arrange: def f(a, b, c, *args, **kwargs) → 5引数で違反
        source_ng = "def f(a, b, c, *args, **kwargs): pass"
        rule = MaxFunctionParameterRule()

        # Act & Assert
        assert rule.check(SourceFileFactory.make(source_ok)) == ()
        assert len(rule.check(SourceFileFactory.make(source_ng))) == 1

    def test_check_正常系_クラスメソッドのcls引数を除外すること(self):
        # Arrange: cls を除いて4引数 = 上限内
        source = "class C:\n    @classmethod\n    def m(cls, a, b, c, d): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_引数なしの関数で違反なしを返すこと(self):
        # Arrange
        source_file = SourceFileFactory.make("def f(): pass")
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_app_commandデコレータ付き関数は違反としないこと(self):
        # Arrange
        source = "@app.command()\ndef check(ctx, targets, format, rule): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_app_callbackデコレータ付き関数は違反としないこと(self):
        # Arrange
        source = "@app.callback()\ndef main(ctx, verbose, config, output): pass"
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    @pytest.mark.parametrize(
        ("source", "expected_count"),
        [
            ("class C:\n    def __init__(self, a, b, c, d, e, f): pass", 0),
            ("def __init__(a, b, c, d, e, f): pass", 0),
            ("class C:\n    def __call__(self, a, b, c, d, e): pass", 1),
        ],
        ids=["クラスの__init__", "トップレベル__init__", "ダンダーは__init__のみ除外"],
    )
    def test_check_正常系___init__は常に違反としないこと(self, source: str, expected_count: int):
        # Arrange
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == expected_count

    def test_check_正常系___init__と通常メソッド混在で__init__のみ除外すること(self):
        # Arrange: __init__ は除外され、通常メソッドのみ違反検出
        source = (
            "class C:\n"
            "    def __init__(self, a, b, c, d, e, f): pass\n"
            "    def process(self, a, b, c, d, e): pass\n"
        )
        source_file = SourceFileFactory.make(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 3
