from pathlib import Path

import pytest

from paladin.rule.no_deep_nesting import NoDeepNestingRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


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

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                "def foo():\n    if True:\n        if True:\n            pass\n",
                id="2段階以下のネスト",
            ),
            pytest.param(
                "def outer():\n"
                "    if True:\n"
                "        if True:\n"
                "            def inner():\n"
                "                if True:\n"
                "                    pass\n",
                id="ネスト関数の深度非引き継ぎ",
            ),
            pytest.param(
                "def foo():\n"
                "    if True:\n"
                "        if True:\n"
                "            result = [x for x in [] if x > 0]\n",
                id="内包表記",
            ),
            pytest.param("", id="空のソースコード"),
            pytest.param(
                "def foo():\n"
                "    for x in items:\n"
                "        if cond_a:\n"
                "            do_a()\n"
                "        elif cond_b:\n"
                "            do_b()\n"
                "        elif cond_c:\n"
                "            do_c()\n",
                id="elifは深度を増やさない",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = NoDeepNestingRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(
                "def foo():\n"
                "    if True:\n"
                "        if True:\n"
                "            if True:\n"
                "                pass\n",
                id="3段階ifネスト",
            ),
            pytest.param(
                "def foo():\n"
                "    if True:\n"
                "        if True:\n"
                "            if True:\n"
                "                if True:\n"
                "                    pass\n",
                id="4段階ifネスト",
            ),
            pytest.param(
                "def foo():\n"
                "    for x in []:\n"
                "        for y in []:\n"
                "            for z in []:\n"
                "                pass\n",
                id="forループ3段階",
            ),
            pytest.param(
                "def foo():\n"
                "    while True:\n"
                "        while True:\n"
                "            while True:\n"
                "                pass\n",
                id="whileループ3段階",
            ),
            pytest.param(
                "def foo():\n"
                "    with open('a') as a:\n"
                "        with open('b') as b:\n"
                "            with open('c') as c:\n"
                "                pass\n",
                id="with文3段階",
            ),
            pytest.param(
                "def foo():\n"
                "    try:\n"
                "        try:\n"
                "            try:\n"
                "                pass\n"
                "            except Exception:\n"
                "                pass\n"
                "        except Exception:\n"
                "            pass\n"
                "    except Exception:\n"
                "        pass\n",
                id="try_except3段階",
            ),
            pytest.param(
                "def foo():\n"
                "    if True:\n"
                "        for x in []:\n"
                "            while True:\n"
                "                pass\n",
                id="if_else混在3段階",
            ),
            pytest.param(
                "async def foo():\n"
                "    async for x in []:\n"
                "        async for y in []:\n"
                "            async for z in []:\n"
                "                pass\n",
                id="async_for3段階",
            ),
            pytest.param(
                "async def foo():\n"
                "    async with open('a') as a:\n"
                "        async with open('b') as b:\n"
                "            async with open('c') as c:\n"
                "                pass\n",
                id="async_with3段階",
            ),
            pytest.param(
                "class MyClass:\n"
                "    def my_method(self):\n"
                "        if True:\n"
                "            if True:\n"
                "                if True:\n"
                "                    pass\n",
                id="クラスメソッド3段階",
            ),
            pytest.param(
                "def outer():\n"
                "    if True:\n"
                "        if True:\n"
                "            def inner():\n"
                "                if True:\n"
                "                    if True:\n"
                "                        if True:\n"
                "                            pass\n",
                id="ネスト関数独立スコープ",
            ),
            pytest.param(
                "def outer():\n"
                "    if True:\n"
                "        if True:\n"
                "            class Inner:\n"
                "                def method(self):\n"
                "                    if True:\n"
                "                        if True:\n"
                "                            if True:\n"
                "                                pass\n",
                id="ネストクラス独立スコープ",
            ),
            pytest.param(
                "def foo():\n"
                "    if True:\n"
                "        if True:\n"
                "            if True:\n"
                "                pass\n"
                "    if True:\n"
                "        if True:\n"
                "            if True:\n"
                "                if True:\n"
                "                    pass\n",
                id="1関数1違反",
            ),
            pytest.param(
                "def foo():\n"
                "    for x in items:\n"
                "        if cond_a:\n"
                "            pass\n"
                "        else:\n"
                "            for y in items:\n"
                "                if cond_b:\n"
                "                    pass\n",
                id="else内ネスト",
            ),
            pytest.param(
                "def foo():\n"
                "    for x in items:\n"
                "        if cond_a:\n"
                "            pass\n"
                "    else:\n"
                "        for y in items:\n"
                "            if cond_b:\n"
                "                pass\n",
                id="for_else",
            ),
            pytest.param(
                "def foo():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        finally:\n"
                "            if True:\n"
                "                pass\n"
                "    finally:\n"
                "        pass\n",
                id="try_finally",
            ),
            pytest.param(
                "class Outer:\n"
                "    class Inner:\n"
                "        def method(self):\n"
                "            if True:\n"
                "                if True:\n"
                "                    if True:\n"
                "                        pass\n",
                id="クラス内クラス",
            ),
            pytest.param(
                "def foo():\n"
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
                id="try_else",
            ),
            pytest.param(
                "def foo(x):\n"
                "    if True:\n"
                "        if True:\n"
                "            match x:\n"
                "                case 1:\n"
                "                    pass\n",
                id="match文",
            ),
            pytest.param(
                "async def foo():\n"
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
                id="try_except_star",
            ),
            pytest.param(
                "def foo():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        except* ValueError as eg:\n"
                "            pass\n"
                "        else:\n"
                "            if True:\n"
                "                pass\n"
                "    except* ValueError as eg:\n"
                "        pass\n",
                id="try_except_star_else",
            ),
            pytest.param(
                "def foo():\n"
                "    try:\n"
                "        try:\n"
                "            pass\n"
                "        except* ValueError as eg:\n"
                "            pass\n"
                "        finally:\n"
                "            if True:\n"
                "                pass\n"
                "    except* ValueError as eg:\n"
                "        pass\n",
                id="try_except_star_finally",
            ),
            pytest.param(
                "def foo():\n"
                "    if cond_a:\n"
                "        pass\n"
                "    elif cond_b:\n"
                "        for x in items:\n"
                "            if cond_c:\n"
                "                pass\n",
                id="elif内ネスト",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        rule = NoDeepNestingRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
