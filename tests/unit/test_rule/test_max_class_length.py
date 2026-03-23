import ast
from pathlib import Path

from paladin.rule.max_class_length import MaxClassLengthRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_test_source_file(source: str, filename: str = "tests/test_example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_class(num_lines: int, name: str = "MyClass") -> str:
    """指定行数のトップレベルクラスソースを生成する（class 行 + body 行）"""
    body_lines = num_lines - 1  # class 行を除いた本体の行数
    lines = [f"class {name}:"]
    for i in range(body_lines - 1):
        lines.append(f"    x_{i} = {i}")
    lines.append("    pass")
    return "\n".join(lines) + "\n"


def _make_class_with_docstring(num_lines: int, docstring_lines: int, name: str = "MyClass") -> str:
    """指定の物理行数・docstring行数を持つトップレベルクラスソースを生成する

    num_lines: class行を含む物理総行数
    docstring_lines: docstringの行数（1以上）
    """
    lines = [f"class {name}:"]
    # docstring を生成
    if docstring_lines == 1:
        lines.append('    """docstring"""')
    else:
        lines.append('    """')
        for i in range(docstring_lines - 2):
            lines.append(f"    docstring line {i}")
        lines.append('    """')
    # 残りの本体行を埋める（class行 + docstring行 + body行 = num_lines）
    body_lines = num_lines - 1 - docstring_lines
    for i in range(body_lines - 1):
        lines.append(f"    x_{i} = {i}")
    lines.append("    pass")
    return "\n".join(lines) + "\n"


class TestMaxClassLengthRuleMeta:
    """MaxClassLengthRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = MaxClassLengthRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "max-class-length"
        assert result.rule_name == "Max Class Length"


class TestMaxClassLengthRuleCheck:
    """MaxClassLengthRule.check のテスト"""

    # ── Phase 1: 基本検出 ────────────────────────────────────────────

    def test_check_正常系_上限超過のトップレベルクラスで違反を1件返すこと(self):
        # Arrange: デフォルト上限200行に対して201行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(201)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = MaxClassLengthRule()
        source = _make_class(201, name="LongClass")
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1  # class 文の行番号
        assert violation.rule_id == "max-class-length"
        assert "LongClass" in violation.message
        assert "201" in violation.message
        assert "200" in violation.message

    def test_check_正常系_上限以下のトップレベルクラスで違反なしを返すこと(self):
        # Arrange: 199行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(199)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_上限ちょうどのクラスで違反なしを返すこと(self):
        # Arrange: ちょうど200行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(200)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    # ── Phase 2: テストファイル判定 ─────────────────────────────────

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限400行に対して401行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(401)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "401" in result[0].message
        assert "400" in result[0].message

    def test_check_正常系_テストファイルでmax_test_lines以下なら違反なしを返すこと(self):
        # Arrange: テストファイルで400行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(400)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: プロダクション上限200行超えだがテスト上限400行以内の201行
        rule = MaxClassLengthRule()
        source = _make_class(201)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert result == ()

    # ── Phase 3: ネスト・再帰探索 ───────────────────────────────────

    def test_check_正常系_ネストされたクラスは独立して検査されること(self):
        # Arrange: ネストクラス Inner が上限超過（201行）、外側 Outer は全体でさらに大きい
        rule = MaxClassLengthRule(max_lines=10)
        # Outer は12行、Inner は11行（上限10行超え）
        lines = ["class Outer:"]
        lines.append("    class Inner:")
        for i in range(9):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: Outer と Inner の両方が違反として報告される
        assert len(result) == 2
        messages = [v.message for v in result]
        assert any("Inner" in m for m in messages)
        assert any("Outer" in m for m in messages)

    def test_check_正常系_外側クラスの行数にネストクラスの行が含まれること(self):
        # Arrange: 外側クラス全体が上限超過（ネストクラス含む）
        rule = MaxClassLengthRule(max_lines=10)
        # Outer は12行（上限10行超え）、Inner は5行（上限以内）
        lines = ["class Outer:"]
        lines.append("    class Inner:")
        for i in range(3):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        for i in range(6):
            lines.append(f"    y_{i} = {i}")
        lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: Outer が上限超過で違反あり
        messages = [v.message for v in result]
        assert any("Outer" in m for m in messages)

    def test_check_正常系_関数内のクラス定義を検査すること(self):
        # Arrange: トップレベル関数内にクラス定義がある場合
        rule = MaxClassLengthRule(max_lines=5)
        lines = ["def outer_func():"]
        lines.append("    class LocalClass:")
        for i in range(5):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: LocalClass が7行（上限5行超え）で違反あり
        messages = [v.message for v in result]
        assert any("LocalClass" in m for m in messages)

    def test_check_正常系_メソッド内のクラス定義を検査すること(self):
        # Arrange: クラスメソッド内にクラス定義がある場合
        rule = MaxClassLengthRule(max_lines=5)
        lines = ["class Outer:"]
        lines.append("    def method(self):")
        lines.append("        class InnerLocal:")
        for i in range(5):
            lines.append(f"            x_{i} = {i}")
        lines.append("            pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: InnerLocal が7行（上限5行超え）で違反あり
        messages = [v.message for v in result]
        assert any("InnerLocal" in m for m in messages)

    # ── Phase 4: カスタム上限・エッジケース ─────────────────────────

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行のクラス
        rule = MaxClassLengthRule(max_lines=10)
        source = _make_class(11)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "10" in result[0].message

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行のクラス
        rule = MaxClassLengthRule(max_test_lines=20)
        source = _make_class(21)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "20" in result[0].message

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = MaxClassLengthRule()
        source_file = _make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_クラス定義のないコードは空タプルを返すこと(self):
        # Arrange
        rule = MaxClassLengthRule()
        source = "x = 1\ny = 2\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反のreason_suggestionが正しいこと(self):
        # Arrange
        rule = MaxClassLengthRule()
        source = _make_class(201)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert "責務の肥大化" in violation.reason
        assert "分割" in violation.suggestion

    def test_check_正常系_複数の違反をそれぞれ1件ずつ報告すること(self):
        # Arrange: 2つの長いクラス
        rule = MaxClassLengthRule(max_lines=5)
        lines: list[str] = []
        for class_name in ["ClassA", "ClassB"]:
            lines.append(f"class {class_name}:")
            for i in range(5):
                lines.append(f"    x_{i} = {i}")
            lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    # ── Phase 5: docstring 除外 ──────────────────────────────────────

    def test_check_正常系_docstringを除外すると上限内に収まるクラスは違反なしを返すこと(self):
        # Arrange: 物理205行・docstring5行 → 実効200行（上限ちょうど）
        rule = MaxClassLengthRule()
        source = _make_class_with_docstring(num_lines=205, docstring_lines=5)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_docstringを除外しても上限超過するクラスは違反を返すこと(self):
        # Arrange: 物理211行・docstring10行 → 実効201行（上限200を超過）
        rule = MaxClassLengthRule()
        source = _make_class_with_docstring(num_lines=211, docstring_lines=10)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_先頭文がExprでない場合はdocstring除外なしで行数計算すること(self):
        # Arrange: 先頭文が代入文（ast.Assign）なので docstring なし → 物理201行がそのまま計上
        rule = MaxClassLengthRule()
        lines = ["class MyClass:"]
        lines.append("    x = 0")  # ast.Assign（ast.Exprではない）
        for i in range(199):
            lines.append(f"    y_{i} = {i}")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: docstring除外なし → 物理201行 > 上限200行 → 違反あり
        assert len(result) == 1

    def test_check_正常系_先頭ExprがConstant_str以外の場合はdocstring除外なしで行数計算すること(
        self,
    ):
        # Arrange: 先頭文が ast.Expr(ast.Call) → docstring として扱わない
        rule = MaxClassLengthRule()
        lines = ["class MyClass:"]
        lines.append("    print('hello')")  # ast.Expr(ast.Call)
        for i in range(199):
            lines.append(f"    y_{i} = {i}")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: docstring除外なし → 物理201行 > 上限200行 → 違反あり
        assert len(result) == 1
