import ast
from pathlib import Path

import pytest

from paladin.rule.max_class_length import (
    ClassCollector,
    ClassLengthDetector,
    ClassScope,
    MaxClassLengthRule,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file, make_test_source_file


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


class TestClassCollector:
    """ClassCollector.collect のテスト"""

    def test_collect_正常系_トップレベルクラスを収集すること(self):
        # Arrange
        source = "class MyClass:\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = ClassCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], ClassScope)
        assert result[0].node.name == "MyClass"

    def test_collect_正常系_ネストクラスを収集すること(self):
        # Arrange
        source = "class Outer:\n    class Inner:\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = ClassCollector.collect(tree)

        # Assert
        names = {s.node.name for s in result}
        assert names == {"Outer", "Inner"}

    def test_collect_正常系_関数内クラスを収集すること(self):
        # Arrange
        source = "def func():\n    class Local:\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = ClassCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "Local"

    def test_collect_エッジケース_クラスなしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1\ny = 2\n"
        tree = ast.parse(source)

        # Act
        result = ClassCollector.collect(tree)

        # Assert
        assert result == ()


class TestClassLengthDetector:
    """ClassLengthDetector.detect のテスト"""

    def _make_scope(self, source: str) -> ClassScope:
        """ソースからトップレベルの ClassScope を生成する"""
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                return ClassScope(node=node)
        raise ValueError("ClassDef not found")

    def test_detect_正常系_上限以内でNoneを返すこと(self):
        # Arrange
        source = "class MyClass:\n    pass\n"
        scope = self._make_scope(source)
        meta = MaxClassLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = ClassLengthDetector.detect(
            scope, length=limit, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is None

    def test_detect_正常系_上限超過でViolationを返すこと(self):
        # Arrange
        source = "class MyClass:\n    pass\n"
        scope = self._make_scope(source)
        meta = MaxClassLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = ClassLengthDetector.detect(
            scope, length=limit + 1, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None

    def test_detect_正常系_Violationのメッセージにクラス名が含まれること(self):
        # Arrange
        source = "class TargetClass:\n    pass\n"
        scope = self._make_scope(source)
        meta = MaxClassLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = ClassLengthDetector.detect(
            scope, length=limit + 1, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None


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

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = MaxClassLengthRule()
        source = _make_class(201, name="LongClass")
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1  # class 文の行番号
        assert violation.rule_id == "max-class-length"

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
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

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
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: Outer と Inner の両方が違反として報告される
        assert len(result) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(_make_class(199), id="上限以下"),
            pytest.param(_make_class(200), id="上限ちょうど"),
            pytest.param("", id="空ソース"),
            pytest.param("x = 1\ny = 2\n", id="クラス定義なし"),
            pytest.param(
                _make_class_with_docstring(num_lines=205, docstring_lines=5),
                id="docstring除外で上限以下",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = MaxClassLengthRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param(_make_class(201), id="上限超過"),
            pytest.param(
                _make_class_with_docstring(num_lines=211, docstring_lines=10),
                id="docstring除外しても上限超過",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        rule = MaxClassLengthRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限400行に対して401行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(401)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルでmax_test_lines以下なら違反なしを返すこと(self):
        # Arrange: テストファイルで400行のクラス
        rule = MaxClassLengthRule()
        source = _make_class(400)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: プロダクション上限200行超えだがテスト上限400行以内の201行
        rule = MaxClassLengthRule()
        source = _make_class(201)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert len(result) == 0

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行のクラス
        rule = MaxClassLengthRule(max_lines=10)
        source = _make_class(11)
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行のクラス
        rule = MaxClassLengthRule(max_test_lines=20)
        source = _make_class(21)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

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
        source_file = make_source_file(source)

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
        source_file = make_source_file(source)

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
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: InnerLocal が7行（上限5行超え）で違反あり
        messages = [v.message for v in result]
        assert any("InnerLocal" in m for m in messages)

    def test_check_正常系_先頭文がExprでない場合はdocstring除外なしで行数計算すること(self):
        # Arrange: 先頭文が代入文（ast.Assign）なので docstring なし → 物理201行がそのまま計上
        rule = MaxClassLengthRule()
        lines = ["class MyClass:"]
        lines.append("    x = 0")  # ast.Assign（ast.Exprではない）
        for i in range(199):
            lines.append(f"    y_{i} = {i}")
        source = "\n".join(lines) + "\n"
        source_file = make_source_file(source)

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
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: docstring除外なし → 物理201行 > 上限200行 → 違反あり
        assert len(result) == 1
