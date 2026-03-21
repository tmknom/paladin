import ast
from pathlib import Path

from paladin.rule.no_deep_nesting import NoDeepNestingRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


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

    # ── Phase 1: 基本 ──────────────────────────────────────────────

    def test_check_正常系_3段階ネストで違反を1件返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

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
        source_file = _make_source_file(source)

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

    def test_check_正常系_4段階ネストで最大深度が正しく報告されること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "4" in result[0].message

    def test_check_正常系_2段階以下のネストは違反なしを返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = "def foo():\n    if True:\n        if True:\n            pass\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ネストなしの関数は違反なしを返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = "def foo():\n    pass\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    # ── Phase 2: 複合文種類別 ──────────────────────────────────────

    def test_check_正常系_forループの3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    for x in []:\n"
            "        for y in []:\n"
            "            for z in []:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_whileループの3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    while True:\n"
            "        while True:\n"
            "            while True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_with文の3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    with open('a') as a:\n"
            "        with open('b') as b:\n"
            "            with open('c') as c:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_try_except文の3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
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
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_if_else混在の3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        for x in []:\n"
            "            while True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_async_for文の3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "async def foo():\n"
            "    async for x in []:\n"
            "        async for y in []:\n"
            "            async for z in []:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_async_with文の3段階ネストで違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "async def foo():\n"
            "    async with open('a') as a:\n"
            "        async with open('b') as b:\n"
            "            async with open('c') as c:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    # ── Phase 3: スコープ・クラス ──────────────────────────────────

    def test_check_正常系_クラスメソッドの3段階ネストでメソッドスコープの違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "class MyClass:\n"
            "    def my_method(self):\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "メソッド MyClass.my_method" in result[0].message

    def test_check_正常系_トップレベル関数の3段階ネストで関数スコープの違反を返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def my_func():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "関数 my_func" in result[0].message

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_async_defメソッドでも違反を検出すること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "class MyClass:\n"
            "    async def my_method(self):\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "メソッド MyClass.my_method" in result[0].message

    # ── Phase 4: ネスト関数・内包表記 ─────────────────────────────

    def test_check_正常系_ネスト関数は独立スコープとして検査されること(self):
        # Arrange
        rule = NoDeepNestingRule()
        # 外側: depth=2（違反なし）、内側ネスト関数: depth=3（違反あり）
        source = (
            "def outer():\n"
            "    if True:\n"
            "        if True:\n"
            "            def inner():\n"
            "                if True:\n"
            "                    if True:\n"
            "                        if True:\n"
            "                            pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "関数 inner" in result[0].message

    def test_check_正常系_ネスト関数の深度が外側を引き継がないこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        # 外側: depth=2（違反なし）、内側ネスト関数: depth=1（違反なし）
        source = (
            "def outer():\n"
            "    if True:\n"
            "        if True:\n"
            "            def inner():\n"
            "                if True:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ネストクラスは独立スコープとして扱われること(self):
        # Arrange
        rule = NoDeepNestingRule()
        # 外側関数: depth=2（違反なし）、ネストクラスのメソッド: depth=3（違反あり）
        source = (
            "def outer():\n"
            "    if True:\n"
            "        if True:\n"
            "            class Inner:\n"
            "                def method(self):\n"
            "                    if True:\n"
            "                        if True:\n"
            "                            if True:\n"
            "                                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "メソッド Inner.method" in result[0].message

    def test_check_正常系_内包表記はネスト深度に含まれないこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        # if+if のネスト(depth=2)の中に内包表記 → 内包表記はカウントしないので違反なし
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            result = [x for x in [] if x > 0]\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ジェネレータ式はネスト深度に含まれないこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            result = list(x for x in [] if x > 0)\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    # ── Phase 5: エッジケース ─────────────────────────────────────

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source_file = _make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_関数定義のないコードは空タプルを返すこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = "x = 1\ny = 2\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_1つの関数につき違反は1件のみ報告されること(self):
        # Arrange
        rule = NoDeepNestingRule()
        # 同じ関数内でdepth=3の箇所とdepth=4の箇所が両方ある → 1件のみ（最大値=4）
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "4" in result[0].message

    def test_check_正常系_else内のネストでも深度がカウントされること(self):
        # Arrange
        rule = NoDeepNestingRule()
        # else ブランチは if と同一深度（+0）。else 内のネスト自体が深度を積む
        # for(depth 1) → if/else(depth 1) → for(depth 2) → if(depth 3) → 違反あり
        source = (
            "def foo():\n"
            "    for x in items:\n"
            "        if cond_a:\n"
            "            pass\n"
            "        else:\n"
            "            for y in items:\n"
            "                if cond_b:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_for_else文のelseブランチが深度カウントされること(self):
        # Arrange
        # for...else の orelse ブランチ（for の orelse は for と同一深度）
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    for x in items:\n"
            "        if cond_a:\n"
            "            pass\n"
            "    else:\n"
            "        for y in items:\n"
            "            if cond_b:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_try_finally文の深度がカウントされること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    try:\n"
            "        try:\n"
            "            pass\n"
            "        finally:\n"
            "            if True:\n"
            "                pass\n"
            "    finally:\n"
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_診断メッセージにscopeとdepthが含まれること(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def my_func():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        expected_message = "関数 my_func 内のネストが 3 段階に達している（最大: 3）"
        assert violation.message == expected_message

    def test_check_正常系_reasonとsuggestionが正しいこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        source = (
            "def foo():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert (
            violation.reason
            == "深いネストはテスタビリティを下げ、手続き的にロジックを持たせすぎている兆候である"
        )
        assert (
            violation.suggestion
            == "ネストの深い処理をプライベートメソッドに切り出すか、クラス設計を見直してください"
        )

    # ── Phase 6: カバレッジ補完テスト ─────────────────────────────

    def test_check_正常系_クラス内クラスのメソッドで違反を検出すること(self):
        # Arrange
        # _visit_class が直接クラス内クラス（ast.ClassDef in class body）を処理する経路（lines 68-70）
        rule = NoDeepNestingRule()
        source = (
            "class Outer:\n"
            "    class Inner:\n"
            "        def method(self):\n"
            "            if True:\n"
            "                if True:\n"
            "                    if True:\n"
            "                        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "メソッド Inner.method" in result[0].message

    def test_check_正常系_try_else文の深度がカウントされること(self):
        # Arrange
        # ast.Try の orelse ブランチ（line 184）
        rule = NoDeepNestingRule()
        source = (
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
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_match文の3段階ネストで違反を返すこと(self):
        # Arrange
        # ast.Match ブランチ（lines 192-194）
        rule = NoDeepNestingRule()
        source = (
            "def foo(x):\n"
            "    if True:\n"
            "        if True:\n"
            "            match x:\n"
            "                case 1:\n"
            "                    pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_try_except_star文の3段階ネストで違反を返すこと(self):
        # Arrange
        # ast.TryStar ブランチ（lines 188-190, _collect_try_like_stmts lines 136-145）
        rule = NoDeepNestingRule()
        source = (
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
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_try_except_star_else文の深度がカウントされること(self):
        # Arrange
        # _collect_try_like_stmts の orelse ブランチ（line 142）
        rule = NoDeepNestingRule()
        source = (
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
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_try_except_star_finally文の深度がカウントされること(self):
        # Arrange
        # _collect_try_like_stmts の finalbody ブランチ（line 145）
        rule = NoDeepNestingRule()
        source = (
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
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    # ── Phase 7: elif 深度カウント ────────────────────────────────

    def test_check_正常系_elifは深度を増やさないこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        # for(depth 1) → if/elif/elif(depth 2) → depth 2 のみ → 違反なし
        source = (
            "def foo():\n"
            "    for x in items:\n"
            "        if cond_a:\n"
            "            do_a()\n"
            "        elif cond_b:\n"
            "            do_b()\n"
            "        elif cond_c:\n"
            "            do_c()\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_elif内のネストで違反を検出すること(self):
        # Arrange
        rule = NoDeepNestingRule()
        # if(depth 1) → elif(depth 1) → for(depth 2) → if(depth 3) → 違反あり
        source = (
            "def foo():\n"
            "    if cond_a:\n"
            "        pass\n"
            "    elif cond_b:\n"
            "        for x in items:\n"
            "            if cond_c:\n"
            "                pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_長いelifチェーンでも深度が増えないこと(self):
        # Arrange
        rule = NoDeepNestingRule()
        # 5分岐の if/elif/elif/elif/else でも depth 1 → 違反なし
        source = (
            "def foo():\n"
            "    if cond_a:\n"
            "        pass\n"
            "    elif cond_b:\n"
            "        pass\n"
            "    elif cond_c:\n"
            "        pass\n"
            "    elif cond_d:\n"
            "        pass\n"
            "    else:\n"
            "        pass\n"
        )
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
