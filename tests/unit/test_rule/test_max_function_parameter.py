"""max_function_parameter モジュールのユニットテスト"""

import ast
from pathlib import Path

from paladin.rule.max_function_parameter import (
    DecoratorAllowChecker,
    FunctionCollector,
    FunctionScope,
    MaxFunctionParameterRule,
    ParameterCounter,
    ParameterLimitDetector,
)
from paladin.rule.types import RuleMeta, Violation
from tests.unit.test_rule.helper import make_source_file


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

    def test_collect_正常系_async関数を収集すること(self):
        # Arrange
        source = "async def foo(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].is_method is False

    def test_collect_正常系_ネストクラスのメソッドを収集すること(self):
        # Arrange
        source = "class Outer:\n    class Inner:\n        def m(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].is_method is True

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

    def test_decorator_name_エッジケース_文字列化不能な式でNoneを返すこと(self):
        # Arrange
        decorator = ast.Constant(value=42)

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result is None

    def test_decorator_name_エッジケース_Attribute親が解決不能な場合Noneを返すこと(self):
        # Arrange: Constant(1).foo のような解決不能な Attribute
        decorator = ast.Attribute(value=ast.Constant(value=1), attr="foo", ctx=ast.Load())

        # Act
        result = DecoratorAllowChecker.decorator_name(decorator)

        # Assert
        assert result is None

    def test_is_allowed_正常系_許可リストに完全一致する場合Trueを返すこと(self):
        # Arrange
        source = "@pytest.fixture\ndef f(a, b, c, d): pass"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)

        # Act
        result = DecoratorAllowChecker.is_allowed(node, frozenset({"pytest.fixture"}))

        # Assert
        assert result is True

    def test_is_allowed_正常系_許可リストに含まれない場合Falseを返すこと(self):
        # Arrange
        source = "@dataclass\ndef f(a, b, c, d): pass"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)

        # Act
        result = DecoratorAllowChecker.is_allowed(node, frozenset({"pytest.fixture"}))

        # Assert
        assert result is False

    def test_is_allowed_正常系_decorator_listが空の場合Falseを返すこと(self):
        # Arrange
        source = "def f(a, b, c, d): pass"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)

        # Act
        result = DecoratorAllowChecker.is_allowed(node, frozenset({"pytest.fixture"}))

        # Assert
        assert result is False


class TestParameterCounter:
    """ParameterCounter.count() のテスト"""

    def test_count_正常系_引数なしで0を返すこと(self):
        # Arrange
        scope = _parse_scope("def f(): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 0

    def test_count_正常系_位置引数のみの場合は引数数を返すこと(self):
        # Arrange
        scope = _parse_scope("def f(a, b, c): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 3

    def test_count_正常系_self付きメソッドはselfを除外すること(self):
        # Arrange
        scope = _parse_scope("def m(self, a, b): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_count_正常系_cls付きクラスメソッドはclsを除外すること(self):
        # Arrange
        scope = _parse_scope("def m(cls, a, b): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_count_正常系_staticmethodはselfを除外しないこと(self):
        # Arrange
        scope = _parse_scope("@staticmethod\ndef m(a, b, c): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 3

    def test_count_正常系_varargを1としてカウントすること(self):
        # Arrange
        scope = _parse_scope("def f(a, *args): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_count_正常系_kwargを1としてカウントすること(self):
        # Arrange
        scope = _parse_scope("def f(a, **kwargs): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_count_正常系_posonlyargsとkwonlyargsを合算すること(self):
        # Arrange
        scope = _parse_scope("def f(a, /, b, *, c): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 3

    def test_count_正常系_vararg_kwarg両方を加算すること(self):
        # Arrange
        scope = _parse_scope("def f(a, *args, **kwargs): pass", is_method=False)

        # Act & Assert
        assert ParameterCounter.count(scope) == 3

    def test_count_正常系_メソッドの第1引数がselfでない場合は除外しないこと(self):
        # Arrange: self/cls 以外の第1引数名は除外しない（仕様通り）
        scope = _parse_scope("def m(other, a): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_count_エッジケース_引数なしのstaticmethodで0を返すこと(self):
        # Arrange
        scope = _parse_scope("@staticmethod\ndef m(): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 0

    def test_count_エッジケース_引数なしのメソッドで0を返すこと(self):
        # Arrange: is_method=True かつ引数なし → _first_positional_name が None を返す
        scope = _parse_scope("def m(): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 0

    def test_count_正常系_posonlyargs先頭がselfの場合除外すること(self):
        # Arrange: def m(self, /, a, b) → posonlyargs に self、self を除外して 2
        scope = _parse_scope("def m(self, /, a, b): pass", is_method=True)

        # Act & Assert
        assert ParameterCounter.count(scope) == 2

    def test_is_static_正常系_staticmethodデコレータでTrueを返すこと(self):
        # Arrange
        source = "@staticmethod\ndef m(a, b): pass"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)

        # Act & Assert
        assert ParameterCounter.is_static(node) is True

    def test_is_static_正常系_デコレータなしでFalseを返すこと(self):
        # Arrange
        source = "def m(a, b): pass"
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)

        # Act & Assert
        assert ParameterCounter.is_static(node) is False


class TestParameterLimitDetector:
    """ParameterLimitDetector.detect() のテスト"""

    def test_detect_正常系_上限以内でNoneを返すこと(self):
        # Arrange
        source_file = make_source_file("def foo(a, b, c): pass")
        scope = _parse_scope("def foo(a, b, c): pass", is_method=False)
        meta = _make_meta()

        # Act
        result = ParameterLimitDetector.detect(
            scope, count=3, limit=3, meta=meta, source_file=source_file
        )

        # Assert
        assert result is None

    def test_detect_正常系_上限超過でViolationを返すこと(self):
        # Arrange
        source_file = make_source_file("def foo(a, b, c, d): pass")
        scope = _parse_scope("def foo(a, b, c, d): pass", is_method=False)
        meta = _make_meta()

        # Act
        result = ParameterLimitDetector.detect(
            scope, count=4, limit=3, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert isinstance(result, Violation)

    def test_detect_正常系_violation_lineがdef文の行番号と一致すること(self):
        # Arrange: 3行目に def が来るソース
        source = "\n\ndef foo(a, b, c, d): pass"
        source_file = make_source_file(source)
        tree = ast.parse(source)
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        scope = FunctionScope(node=node, is_method=False)
        meta = _make_meta()

        # Act
        result = ParameterLimitDetector.detect(
            scope, count=4, limit=3, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert result.line == 3

    def test_detect_正常系_violation_messageに関数名と件数と上限が含まれること(self):
        # Arrange
        source_file = make_source_file("def create_user(a, b, c, d): pass")
        scope = _parse_scope("def create_user(a, b, c, d): pass", is_method=False)
        meta = _make_meta()

        # Act
        result = ParameterLimitDetector.detect(
            scope, count=4, limit=3, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert isinstance(result, Violation)

    def test_detect_正常系_rule_id_rule_name_reason_suggestionが設定されていること(self):
        # Arrange
        source_file = make_source_file("def foo(a, b, c, d): pass")
        scope = _parse_scope("def foo(a, b, c, d): pass", is_method=False)
        meta = _make_meta()

        # Act
        result = ParameterLimitDetector.detect(
            scope, count=4, limit=3, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
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
        assert isinstance(rule.meta, RuleMeta)
        assert rule.meta.config_example is not None
        assert rule.meta.detection_example is not None

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        source = "def foo(a, b, c, d): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].file == Path("example.py")
        assert result[0].line == 1
        assert result[0].rule_id == "max-function-parameter"

    def test_check_正常系_self除外で上限以内なら違反なしを返すこと(self):
        # Arrange: self を除いて3引数 = 上限内
        source = "class C:\n    def m(self, a, b, c): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_staticmethodは第1引数を除外しないこと(self):
        # Arrange: @staticmethod なので除外なし → 4引数で違反
        source = "class C:\n    @staticmethod\n    def m(a, b, c, d): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_pytest_fixtureデコレータ付き関数は違反としないこと(self):
        # Arrange
        source = "@pytest.fixture\ndef f(a, b, c, d, e): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_fixture単独デコレータも違反としないこと(self):
        # Arrange
        source = "@fixture\ndef f(a, b, c, d, e): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_AsyncFunctionDefも違反として検出すること(self):
        # Arrange
        source = "async def f(a, b, c, d): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_parametersが適用されること(self):
        # Arrange: max_parameters=2 で def f(a,b,c) は違反
        source = "def f(a, b, c): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule(max_parameters=2)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムallow_decoratorsを尊重すること(self):
        # Arrange: @dataclass を許可リストに追加
        source = "@dataclass\ndef f(a, b, c, d, e): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule(allow_decorators=("dataclass",))

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数の違反を定義順に報告すること(self):
        # Arrange
        source = "def f1(a, b, c, d): pass\ndef f2(a, b, c, d, e): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        assert result[0].line < result[1].line

    def test_check_正常系_varargとkwargを加算してカウントすること(self):
        # Arrange: def f(a, *args, **kwargs) → 3引数で違反なし
        source_ok = "def f(a, *args, **kwargs): pass"
        # Arrange: def f(a, b, *args, **kwargs) → 4引数で違反
        source_ng = "def f(a, b, *args, **kwargs): pass"
        rule = MaxFunctionParameterRule()

        # Act & Assert
        assert rule.check(make_source_file(source_ok)) == ()
        assert len(rule.check(make_source_file(source_ng))) == 1

    def test_check_正常系_クラスメソッドのcls引数を除外すること(self):
        # Arrange: cls を除いて3引数 = 上限内
        source = "class C:\n    @classmethod\n    def m(cls, a, b, c): pass"
        source_file = make_source_file(source)
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_関数定義なしで空タプルを返すこと(self):
        # Arrange
        source_file = make_source_file("x = 1")
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_引数なしの関数で違反なしを返すこと(self):
        # Arrange
        source_file = make_source_file("def f(): pass")
        rule = MaxFunctionParameterRule()

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()


# --- helpers ---


def _parse_scope(source: str, is_method: bool) -> FunctionScope:
    """テスト用に単一関数の FunctionScope を生成する"""
    tree = ast.parse(source)
    node = tree.body[0]
    assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    return FunctionScope(node=node, is_method=is_method)


def _make_meta() -> RuleMeta:
    """テスト用の RuleMeta を生成する"""
    return MaxFunctionParameterRule().meta
