import ast
from pathlib import Path

import pytest

from paladin.rule.no_deep_nesting import (
    FunctionCollector,
    FunctionScope,
    NestingCalculator,
    NestingDetector,
    NoDeepNestingRule,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


class TestFunctionCollector:
    """FunctionCollector.collect のテスト"""

    def test_collect_正常系_トップレベル関数を収集すること(self):
        # Arrange
        source = "def foo():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "foo"
        assert result[0].class_name is None

    def test_collect_正常系_メソッドをクラス名付きで収集すること(self):
        # Arrange
        source = "class MyClass:\n    def method(self):\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "method"
        assert result[0].class_name == "MyClass"

    def test_collect_正常系_ネスト関数を独立スコープとして収集すること(self):
        # Arrange
        source = "def outer():\n    def inner():\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 2
        names = {s.node.name for s in result}
        assert names == {"outer", "inner"}
        inner_scope = next(s for s in result if s.node.name == "inner")
        assert inner_scope.class_name is None

    def test_collect_正常系_ネストクラス内のメソッドを収集すること(self):
        # Arrange
        source = "class Outer:\n    class Inner:\n        def method(self):\n            pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "method"
        assert result[0].class_name == "Inner"

    def test_collect_正常系_関数内クラスのメソッドを収集すること(self):
        # Arrange
        source = "def outer():\n    class Local:\n        def method(self):\n            pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 2
        names = {s.node.name for s in result}
        assert names == {"outer", "method"}
        method_scope = next(s for s in result if s.node.name == "method")
        assert method_scope.class_name == "Local"

    def test_collect_正常系_async関数を収集すること(self):
        # Arrange
        source = "async def foo():\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "foo"
        assert result[0].class_name is None

    def test_collect_エッジケース_関数なしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1\n"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert result == ()

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                "def outer():\n    with open('f') as f:\n        def inner(): pass\n",
                id="with（Withブランチ）",
            ),
            pytest.param(
                "def outer():\n"
                "    try:\n"
                "        def inner(): pass\n"
                "    except Exception:\n"
                "        pass\n",
                id="try（Tryブランチ）",
            ),
            pytest.param(
                "def outer():\n    for x in []:\n        pass\n    else:\n        def inner(): pass\n",
                id="for_else（orelseブランチ）",
            ),
            pytest.param(
                "def outer():\n"
                "    try:\n"
                "        pass\n"
                "    except Exception:\n"
                "        pass\n"
                "    else:\n"
                "        def inner(): pass\n",
                id="try_else（orelseブランチ）",
            ),
            pytest.param(
                "def outer():\n    try:\n        pass\n    finally:\n        def inner(): pass\n",
                id="try_finally（finalbodyブランチ）",
            ),
            pytest.param(
                "def outer(x):\n    match x:\n        case 1:\n            def inner(): pass\n",
                id="match（Matchブランチ）",
            ),
        ],
    )
    def test_collect_正常系_制御構造内のネスト関数を収集すること(self, source: str) -> None:
        # Arrange
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        names = {s.node.name for s in result}
        assert "inner" in names


class TestNestingCalculator:
    """NestingCalculator.calc_max_depth のテスト"""

    def _parse_func_body(self, source: str) -> list[ast.stmt]:
        """関数の body を返す"""
        tree = ast.parse(source)
        func = tree.body[0]
        assert isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef))
        return func.body

    def test_calc_max_depth_正常系_ifネストの深度を返すこと(self):
        # Arrange: if True: if True: if True: pass
        source = (
            "def f():\n    if True:\n        if True:\n            if True:\n                pass\n"
        )
        stmts = self._parse_func_body(source)

        # Act
        result = NestingCalculator.calc_max_depth(stmts)

        # Assert
        assert result == 3

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                "def f():\n    for x in []:\n        for y in []:\n            pass\n",
                id="for",
            ),
            pytest.param(
                "def f():\n    while True:\n        while True:\n            pass\n",
                id="while",
            ),
            pytest.param(
                "def f():\n    with open('a'):\n        with open('b'):\n            pass\n",
                id="with",
            ),
            pytest.param(
                "def f():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        except Exception:\n"
                "            pass\n"
                "    except Exception:\n"
                "        pass\n",
                id="try_except",
            ),
        ],
    )
    def test_calc_max_depth_正常系_2段ネストの深度を返すこと(self, source: str) -> None:
        # Arrange
        stmts = self._parse_func_body(source)

        # Act
        result = NestingCalculator.calc_max_depth(stmts)

        # Assert
        assert result == 2

    def test_calc_max_depth_正常系_ネスト関数を深度に含めないこと(self):
        # Arrange: if True: def inner(): if True: if True: if True: pass
        source = (
            "def f():\n"
            "    if True:\n"
            "        def inner():\n"
            "            if True:\n"
            "                if True:\n"
            "                    if True:\n"
            "                        pass\n"
        )
        stmts = self._parse_func_body(source)

        # Act
        result = NestingCalculator.calc_max_depth(stmts)

        # Assert
        assert result == 1

    def test_calc_max_depth_正常系_ネストクラスを深度に含めないこと(self):
        # Arrange: if True: class Inner: def method(self): pass
        source = (
            "def f():\n"
            "    if True:\n"
            "        class Inner:\n"
            "            def method(self):\n"
            "                pass\n"
        )
        stmts = self._parse_func_body(source)

        # Act
        result = NestingCalculator.calc_max_depth(stmts)

        # Assert
        assert result == 1

    @pytest.mark.parametrize(
        ("source", "expected_depth"),
        [
            pytest.param(
                "def f():\n"
                "    for x in items:\n"
                "        if cond_a:\n"
                "            pass\n"
                "        else:\n"
                "            for y in items:\n"
                "                if cond_b:\n"
                "                    pass\n",
                4,
                id="else内ネスト",
            ),
            pytest.param(
                "def f():\n"
                "    for x in items:\n"
                "        if cond_a:\n"
                "            pass\n"
                "    else:\n"
                "        for y in items:\n"
                "            if cond_b:\n"
                "                pass\n",
                3,
                id="for_else",
            ),
            pytest.param(
                "def f():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        finally:\n"
                "            if True:\n"
                "                pass\n"
                "    finally:\n"
                "        pass\n",
                3,
                id="try_finally",
            ),
            pytest.param(
                "def f():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        except Exception:\n"
                "            pass\n"
                "        else:\n"
                "            if True:\n"
                "                pass\n"
                "    except Exception:\n"
                "        pass\n",
                3,
                id="try_else",
            ),
            pytest.param(
                "def f(x):\n"
                "    if True:\n"
                "        if True:\n"
                "            match x:\n"
                "                case 1:\n"
                "                    pass\n",
                3,
                id="match文",
            ),
            pytest.param(
                "async def f():\n"
                "    try:\n"
                "        try:\n"
                "            try:\n"
                "                pass\n"
                "            except* ValueError as eg:\n"
                "                pass\n"
                "        except* ValueError as eg:\n"
                "            pass\n"
                "    except* ValueError as eg:\n"
                "        pass\n",
                3,
                id="try_except_star",
            ),
            pytest.param(
                "def f():\n"
                "    if cond_a:\n"
                "        pass\n"
                "    elif cond_b:\n"
                "        for x in items:\n"
                "            if cond_c:\n"
                "                pass\n",
                3,
                id="elif内ネスト",
            ),
        ],
    )
    def test_calc_max_depth_正常系_各制御構造の深度を返すこと(
        self, source: str, expected_depth: int
    ) -> None:
        # Arrange
        stmts = self._parse_func_body(source)

        # Act
        result = NestingCalculator.calc_max_depth(stmts)

        # Assert
        assert result == expected_depth


class TestNestingDetector:
    """NestingDetector.detect のテスト"""

    def _make_scope(self, source: str, class_name: str | None = None) -> FunctionScope:
        """テスト用の FunctionScope を生成する"""
        tree = ast.parse(source)
        func = tree.body[0]
        assert isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef))
        return FunctionScope(node=func, class_name=class_name)

    def test_detect_正常系_閾値未満でNoneを返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source_file = make_source_file("def foo():\n    pass\n")
        scope = self._make_scope("def foo():\n    pass\n")

        # Act
        result = NestingDetector.detect(
            scope, depth=2, threshold=3, meta=rule.meta, source_file=source_file
        )

        # Assert
        assert result is None

    def test_detect_正常系_メソッドのViolationメッセージにクラス名_メソッド名が含まれること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source_file = make_source_file("def method():\n    pass\n")
        scope = self._make_scope("def method():\n    pass\n", class_name="MyClass")

        # Act
        result = NestingDetector.detect(
            scope, depth=3, threshold=3, meta=rule.meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert "メソッド MyClass.method" in result.message

    def test_detect_正常系_関数のViolationメッセージに関数名のみが含まれること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source_file = make_source_file("def foo():\n    pass\n")
        scope = self._make_scope("def foo():\n    pass\n", class_name=None)

        # Act
        result = NestingDetector.detect(
            scope, depth=3, threshold=3, meta=rule.meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert "関数 foo" in result.message


class TestNoDeepNestingRuleMeta:
    """NoDeepNestingRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-deep-nesting"
        assert result.rule_name == "No Deep Nesting"


class TestNoDeepNestingRuleCheck:
    """NoDeepNestingRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
        )
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1  # def 文の行番号
        assert violation.rule_id == "no-deep-nesting"
        assert "関数 foo" in violation.message
        assert "3" in violation.message

    def test_check_正常系_複数メソッドで違反があるクラスは違反メソッド分の件数を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "class MyClass:\n"
            "    def method_ok(self):\n"
            "        if True:\n"
            "            pass\n"
            "    def method_bad1(self):\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    pass\n"
            "    def method_bad2(self):\n"
            "        for x in []:\n"
            "            for y in []:\n"
            "                for z in []:\n"
            "                    pass\n"
        )
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
