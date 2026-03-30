import ast
from pathlib import Path

from paladin.rule.max_method_length import (
    FunctionCollector,
    FunctionScope,
    MaxMethodLengthRule,
    MethodLengthDetector,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


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

    def test_check_違反なしのケースで空を返すこと_docstring除外で上限以下(self) -> None:
        # Arrange
        rule = MaxMethodLengthRule()
        source = _make_func_with_docstring(num_lines=55, docstring_lines=5)
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_違反ありのケースで1件返すこと_docstring除外しても上限超過(self) -> None:
        # Arrange
        rule = MaxMethodLengthRule()
        source = _make_func_with_docstring(num_lines=61, docstring_lines=10)
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


class TestMethodLengthDetector:
    """MethodLengthDetector.detect のテスト"""

    def _make_scope(self, source: str) -> FunctionScope:
        """ソースから最初の FunctionScope を返す"""
        scopes = FunctionCollector.collect(ast.parse(source))
        if not scopes:
            raise ValueError("FunctionDef not found")
        return scopes[0]

    def test_detect_正常系_上限以内でNoneを返すこと(self):
        # Arrange
        source = "def foo(): pass"
        scope = self._make_scope(source)
        meta = MaxMethodLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = MethodLengthDetector.detect(
            scope, length=limit, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is None

    def test_detect_正常系_上限超過でViolationを返すこと(self):
        # Arrange
        source = "def foo(): pass"
        scope = self._make_scope(source)
        meta = MaxMethodLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = MethodLengthDetector.detect(
            scope, length=limit + 1, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None

    def test_detect_正常系_メソッドのViolationメッセージにクラス名_メソッド名が含まれること(self):
        # Arrange
        source = "class MyClass:\n    def method(self): pass"
        scope = self._make_scope(source)
        meta = MaxMethodLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = MethodLengthDetector.detect(
            scope, length=limit + 1, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert "MyClass.method" in result.message

    def test_detect_正常系_関数のViolationメッセージに関数名のみが含まれること(self):
        # Arrange
        source = "def standalone(): pass"
        scope = self._make_scope(source)
        meta = MaxMethodLengthRule().meta
        source_file = make_source_file(source)
        limit = 10

        # Act
        result = MethodLengthDetector.detect(
            scope, length=limit + 1, limit=limit, meta=meta, source_file=source_file
        )

        # Assert
        assert result is not None
        assert "standalone" in result.message


class TestFunctionCollector:
    """FunctionCollector.collect のテスト"""

    def test_collect_正常系_トップレベル関数を収集すること(self):
        # Arrange
        source = "def foo(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], FunctionScope)
        assert result[0].node.name == "foo"
        assert result[0].class_name is None

    def test_collect_正常系_メソッドをクラス名付きで収集すること(self):
        # Arrange
        source = "class MyClass:\n    def method(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "method"
        assert result[0].class_name == "MyClass"

    def test_collect_正常系_ネスト関数をclass_name_Noneで収集すること(self):
        # Arrange
        source = "def outer():\n    def inner(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert: outer (class_name=None) と inner (class_name=None) の2件
        assert len(result) == 2
        names = {scope.node.name for scope in result}
        assert names == {"outer", "inner"}
        for scope in result:
            assert scope.class_name is None

    def test_collect_正常系_ネストクラスのメソッドを収集すること(self):
        # Arrange
        source = "class Outer:\n    class Inner:\n        def method(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].node.name == "method"
        assert result[0].class_name == "Inner"

    def test_collect_正常系_関数内クラスのメソッドを収集すること(self):
        # Arrange
        source = "def outer():\n    class Local:\n        def method(self): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert: outer (class_name=None) と Local.method (class_name="Local") の2件
        assert len(result) == 2
        outer_scope = next(s for s in result if s.node.name == "outer")
        method_scope = next(s for s in result if s.node.name == "method")
        assert outer_scope.class_name is None
        assert method_scope.class_name == "Local"

    def test_collect_正常系_async関数を収集すること(self):
        # Arrange
        source = "async def foo(): pass"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], FunctionScope)
        assert result[0].node.name == "foo"
        assert result[0].class_name is None

    def test_collect_エッジケース_関数なしで空タプルを返すこと(self):
        # Arrange
        source = "x = 1"
        tree = ast.parse(source)

        # Act
        result = FunctionCollector.collect(tree)

        # Assert
        assert result == ()
