from pathlib import Path

import pytest

from paladin.rule.max_method_length import MaxMethodLengthRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file, make_test_source_file


def _make_func(num_lines: int, name: str = "foo") -> str:
    """指定行数のトップレベル関数ソースを生成する（def 行 + body 行）"""
    body_lines = num_lines - 1  # def 行を除いた本体の行数
    lines = [f"def {name}():"]
    for i in range(body_lines - 1):
        lines.append(f"    x_{i} = {i}")
    lines.append("    pass")
    return "\n".join(lines) + "\n"


def _make_func_with_docstring(num_lines: int, docstring_lines: int, name: str = "foo") -> str:
    """指定の物理行数・docstring行数を持つトップレベル関数ソースを生成する

    num_lines: def行を含む物理総行数
    docstring_lines: docstringの行数（1以上）
    """
    lines = [f"def {name}():"]
    # docstring を生成
    if docstring_lines == 1:
        lines.append('    """docstring"""')
    else:
        lines.append('    """')
        for i in range(docstring_lines - 2):
            lines.append(f"    docstring line {i}")
        lines.append('    """')
    # 残りの本体行を埋める（def行 + docstring行 + body行 = num_lines）
    body_lines = num_lines - 1 - docstring_lines
    for i in range(body_lines - 1):
        lines.append(f"    x_{i} = {i}")
    lines.append("    pass")
    return "\n".join(lines) + "\n"


class TestMaxMethodLengthRuleMeta:
    """MaxMethodLengthRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = MaxMethodLengthRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "max-method-length"
        assert result.rule_name == "Max Method Length"


class TestMaxMethodLengthRuleCheck:
    """MaxMethodLengthRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        source = _make_func(51, name="long_func")
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1  # def 文の行番号
        assert violation.rule_id == "max-method-length"

    def test_check_正常系_複数の違反をそれぞれ1件ずつ報告すること(self):
        # Arrange: 2つの長い関数
        rule = MaxMethodLengthRule(max_lines=5)
        lines: list[str] = []
        for func_name in ["func_a", "func_b"]:
            lines.append(f"def {func_name}():")
            for i in range(5):
                lines.append(f"    x_{i} = {i}")
            lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_ネスト関数は独立して検査されること(self):
        # Arrange: ネスト関数 inner が上限超過（51行）であることを確認する
        # outer はネスト関数を含めて53行になり outer 自体も違反するが、
        # inner は独立して検査されるため inner の違反も個別に報告される
        rule = MaxMethodLengthRule()
        lines = ["def outer():"]
        lines.append("    def inner():")
        for i in range(49):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: outer と inner の両方が違反として報告される
        assert len(result) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(_make_func(49), id="上限以下"),
            pytest.param(_make_func(50), id="上限ちょうど"),
            pytest.param("", id="空ソース"),
            pytest.param(
                _make_func_with_docstring(num_lines=55, docstring_lines=5),
                id="docstring除外で上限以下",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = MaxMethodLengthRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(_make_func(51), id="上限超過"),
            pytest.param(
                _make_func_with_docstring(num_lines=61, docstring_lines=10),
                id="docstring除外しても上限超過",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        rule = MaxMethodLengthRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限100行に対して101行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(101)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: プロダクション上限50行超えだがテスト上限100行以内の51行
        rule = MaxMethodLengthRule()
        source = _make_func(51)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert len(result) == 0

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行の関数
        rule = MaxMethodLengthRule(max_lines=10)
        source = _make_func(11)
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行の関数
        rule = MaxMethodLengthRule(max_test_lines=20)
        source = _make_func(21)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_クラスメソッドの違反メッセージにClassName_method_name形式が含まれること(
        self,
    ):
        # Arrange
        rule = MaxMethodLengthRule()
        # クラス定義行 + メソッド51行
        lines = ["class MyClass:"]
        lines.append("    def my_method(self):")
        for i in range(49):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_async関数でも違反を検出すること(self):
        # Arrange: async def で51行の関数
        rule = MaxMethodLengthRule()
        lines = ["async def async_long():"]
        for i in range(49):
            lines.append(f"    x_{i} = {i}")
        lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_クラス内ネストクラスのメソッドを検査すること(self):
        # Arrange: クラス内にネストクラスがある場合（_visit_class の ClassDef ブランチ）
        rule = MaxMethodLengthRule(max_lines=5)
        lines = ["class Outer:"]
        lines.append("    class Inner:")
        lines.append("        def method(self):")
        for i in range(4):
            lines.append(f"            x_{i} = {i}")
        lines.append("            pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: Inner.method が6行（上限5行超え）で違反あり
        assert len(result) == 1

    def test_check_正常系_ネスト関数内のクラス定義のメソッドを検査すること(self):
        # Arrange: 関数内にクラス定義がある場合（_check_function の ClassDef ブランチ）
        # outer は4行（上限5行以内）、LocalClass.method は6行（上限超え）
        rule = MaxMethodLengthRule(max_lines=5)
        lines = ["def outer():"]
        lines.append("    class LocalClass:")
        lines.append("        def method(self):")
        for i in range(4):
            lines.append(f"            x_{i} = {i}")
        lines.append("            pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: outer は5行以内なので違反なし、LocalClass.method のみ違反
        messages = [v.message for v in result]
        assert any("LocalClass.method" in m for m in messages)

    def test_check_正常系_violationメッセージにdocstring除外後の行数が表示されること(self):
        # Arrange: 物理61行・docstring10行 → 実効51行
        rule = MaxMethodLengthRule()
        source = _make_func_with_docstring(num_lines=61, docstring_lines=10, name="long_func")
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: メッセージに実効行数51が含まれ、物理行数61は含まれない
        assert len(result) == 1
        assert "51" in result[0].message
        assert "61" not in result[0].message

    def test_check_正常系_クラスメソッドのdocstringを除外すること(self):
        # Arrange: クラスメソッドが物理55行・docstring5行 → 実効50行（上限ちょうど）
        rule = MaxMethodLengthRule()
        lines = ["class MyClass:"]
        lines.append("    def my_method(self):")
        lines.append('        """')
        for i in range(3):
            lines.append(f"        docstring line {i}")
        lines.append('        """')
        # def行1 + docstring5行 + 残り本体44行 = 50行（上限ちょうど）
        for i in range(43):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_先頭文がExprでない場合はdocstring除外なしで行数計算すること(self):
        # Arrange: 先頭文が代入文（ast.Assign）なので docstring なし → 物理51行がそのまま計上
        rule = MaxMethodLengthRule()
        lines = ["def foo():"]
        lines.append("    x = 0")  # ast.Assign（ast.Exprではない）
        for i in range(49):
            lines.append(f"    y_{i} = {i}")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: docstring除外なし → 物理51行 > 上限50行 → 違反あり
        assert len(result) == 1

    def test_check_正常系_先頭ExprがConstant_str以外の場合はdocstring除外なしで行数計算すること(
        self,
    ):
        # Arrange: 先頭文が ast.Expr(ast.Call) → docstring として扱わない
        rule = MaxMethodLengthRule()
        lines = ["def foo():"]
        lines.append("    print('hello')")  # ast.Expr(ast.Call)
        for i in range(49):
            lines.append(f"    y_{i} = {i}")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: docstring除外なし → 物理51行 > 上限50行 → 違反あり
        assert len(result) == 1
