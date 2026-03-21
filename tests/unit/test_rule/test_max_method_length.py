import ast
from pathlib import Path

from paladin.rule.max_method_length import MaxMethodLengthRule
from paladin.rule.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_test_source_file(source: str, filename: str = "tests/test_example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_func(num_lines: int, name: str = "foo") -> str:
    """指定行数のトップレベル関数ソースを生成する（def 行 + body 行）"""
    body_lines = num_lines - 1  # def 行を除いた本体の行数
    lines = [f"def {name}():"]
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

    # ── Phase 1: トップレベル関数 ───────────────────────────────────

    def test_check_正常系_上限超過のトップレベル関数で違反を1件返すこと(self):
        # Arrange: デフォルト上限50行に対して51行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(51)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        source = _make_func(51, name="long_func")
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1  # def 文の行番号
        assert violation.rule_id == "max-method-length"
        assert "long_func" in violation.message
        assert "51" in violation.message
        assert "50" in violation.message

    def test_check_正常系_上限以下のトップレベル関数で違反なしを返すこと(self):
        # Arrange: 49行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(49)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_上限ちょうどの関数で違反なしを返すこと(self):
        # Arrange: ちょうど50行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(50)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    # ── Phase 2: クラスメソッド ─────────────────────────────────────

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "MyClass.my_method" in result[0].message

    def test_check_正常系_クラスメソッドが上限以下なら違反なしを返すこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        lines = ["class MyClass:"]
        lines.append("    def short_method(self):")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    # ── Phase 3: async 関数 ─────────────────────────────────────────

    def test_check_正常系_async関数でも違反を検出すること(self):
        # Arrange: async def で51行の関数
        rule = MaxMethodLengthRule()
        lines = ["async def async_long():"]
        for i in range(49):
            lines.append(f"    x_{i} = {i}")
        lines.append("    pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "async_long" in result[0].message

    def test_check_正常系_asyncクラスメソッドでもClassName_method_name形式を使うこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        lines = ["class AsyncClass:"]
        lines.append("    async def async_method(self):")
        for i in range(49):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "AsyncClass.async_method" in result[0].message

    # ── Phase 4: テストファイル判定 ─────────────────────────────────

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限100行に対して101行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(101)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "101" in result[0].message
        assert "100" in result[0].message

    def test_check_正常系_テストファイルでmax_test_lines以下なら違反なしを返すこと(self):
        # Arrange: テストファイルで100行の関数
        rule = MaxMethodLengthRule()
        source = _make_func(100)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: プロダクション上限50行超えだがテスト上限100行以内の51行
        rule = MaxMethodLengthRule()
        source = _make_func(51)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert result == ()

    # ── Phase 5: ネスト関数 ─────────────────────────────────────────

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: outer と inner の両方が違反として報告される
        assert len(result) == 2
        messages = [v.message for v in result]
        assert any("inner" in m for m in messages)
        assert any("outer" in m for m in messages)

    def test_check_正常系_外側関数の行数にネスト関数の行が含まれること(self):
        # Arrange: 外側関数全体が51行以上（ネスト関数含む）
        rule = MaxMethodLengthRule()
        lines = ["def outer():"]
        # 外側全体で51行になるようにネスト関数を内包する
        lines.append("    def inner():")
        for i in range(49):
            lines.append(f"        x_{i} = {i}")
        lines.append("        pass")
        source = "\n".join(lines) + "\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: outer も inner も検査される（inner は51行超えのため違反あり）
        violation_names = {v.message for v in result}
        # inner は50行以上なので違反
        assert any("inner" in m for m in violation_names)

    # ── Phase 6: カスタム上限 ──────────────────────────────────────

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行の関数
        rule = MaxMethodLengthRule(max_lines=10)
        source = _make_func(11)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "10" in result[0].message

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行の関数
        rule = MaxMethodLengthRule(max_test_lines=20)
        source = _make_func(21)
        source_file = _make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert "20" in result[0].message

    # ── Phase 7: エッジケース ─────────────────────────────────────

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        source_file = _make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_関数定義のないコードは空タプルを返すこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        source = "x = 1\ny = 2\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反のreason_suggestionが正しいこと(self):
        # Arrange
        rule = MaxMethodLengthRule()
        source = _make_func(51)
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert "責務の肥大化" in violation.reason
        assert "分割" in violation.suggestion

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: Inner.method が6行（上限5行超え）で違反あり
        assert len(result) == 1
        assert "Inner.method" in result[0].message

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: outer は5行以内なので違反なし、LocalClass.method のみ違反
        messages = [v.message for v in result]
        assert any("LocalClass.method" in m for m in messages)

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
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
