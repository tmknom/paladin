"""require-aaa-comment ルールのテスト"""

import ast

import pytest

from paladin.rule.require_aaa_comment import (
    AaaCommentDetector,
    RequireAaaCommentRule,
    TargetMethod,
    TargetMethodCollector,
)
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


class TestTargetMethodCollector:
    """TargetMethodCollector クラスのテスト"""

    def test_collect_正常系_test_プレフィックスのメソッドを収集すること(self):
        # Arrange
        source = "class TestFoo:\n    def test_正常系_何かをすること(self) -> None:\n        pass\n"
        tree = ast.parse(source)

        # Act
        result = TargetMethodCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "test_正常系_何かをすること"

    def test_collect_正常系_test_以外のメソッドを除外すること(self):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def setUp(self) -> None:\n"
            "        pass\n"
            "    def helper(self) -> None:\n"
            "        pass\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        pass\n"
        )
        tree = ast.parse(source)

        # Act
        result = TargetMethodCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "test_正常系_何かをすること"

    def test_collect_正常系_メソッドのlineno_end_linenoが正しいこと(self):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        tree = ast.parse(source)

        # Act
        result = TargetMethodCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].lineno == 2
        assert result[0].end_lineno == 4

    def test_collect_エッジケース_テストメソッドがない場合空タプルを返すこと(self):
        # Arrange
        tree = ast.parse("x = 1\n")

        # Act
        result = TargetMethodCollector.collect(tree)

        # Assert
        assert result == ()

    def test_collect_エッジケース_クラス外のtest_関数も収集すること(self):
        # Arrange
        source = "def test_トップレベル関数(self) -> None:\n    pass\n"
        tree = ast.parse(source)

        # Act
        result = TargetMethodCollector.collect(tree)

        # Assert
        assert len(result) == 1
        assert result[0].name == "test_トップレベル関数"


class TestAaaCommentDetector:
    """AaaCommentDetector クラスのテスト"""

    def test_detect_正常系_Actコメントがない場合Violationを返すこと(self):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        source_file = make_test_source_file(source)
        method = TargetMethod(name="test_正常系_何かをすること", lineno=2, end_lineno=4)

        # Act
        result = AaaCommentDetector.detect(method, source_file, RequireAaaCommentRule().meta)

        # Assert
        assert result is not None
        assert result.line == 2

    def test_detect_正常系_Actコメントがある場合Noneを返すこと(self):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        # Act\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        source_file = make_test_source_file(source)
        method = TargetMethod(name="test_正常系_何かをすること", lineno=2, end_lineno=5)

        # Act
        result = AaaCommentDetector.detect(method, source_file, RequireAaaCommentRule().meta)

        # Assert
        assert result is None

    def test_detect_正常系_ActAndAssertコメントがある場合Noneを返すこと(self):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        # Act & Assert\n"
            "        assert 1 == 1\n"
        )
        source_file = make_test_source_file(source)
        method = TargetMethod(name="test_正常系_何かをすること", lineno=2, end_lineno=4)

        # Act
        result = AaaCommentDetector.detect(method, source_file, RequireAaaCommentRule().meta)

        # Assert
        assert result is None


class TestRequireAaaCommentRuleCheck:
    """RequireAaaCommentRule.check のテスト"""

    @pytest.fixture
    def rule(self) -> RequireAaaCommentRule:
        return RequireAaaCommentRule()

    def test_check_正常系_Actコメントがないテストメソッドで違反を返すこと(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "require-aaa-comment"

    def test_check_正常系_Actコメントがあるテストメソッドで違反なしを返すこと(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        # Act\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ActAndAssertコメントがあるテストメソッドで違反なしを返すこと(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        # Act & Assert\n"
            "        assert 1 == 1\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数のテストメソッドで違反がある場合メソッド数分の違反を返すこと(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_Aをすること(self) -> None:\n"
            "        assert 1 == 1\n"
            "    def test_正常系_Bをすること(self) -> None:\n"
            "        # Act\n"
            "        assert 2 == 2\n"
            "    def test_正常系_Cをすること(self) -> None:\n"
            "        assert 3 == 3\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_エッジケース_テストファイル以外は空タプルを返すこと(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = "class Foo:\n    def test_正常系_何かをすること(self) -> None:\n        pass\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_test_プレフィックスのないメソッドは検査対象外であること(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def setUp(self) -> None:\n"
            "        pass\n"
            "    def helper_method(self) -> None:\n"
            "        pass\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_Arrangeコメントのみでは違反となること(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        # Arrange\n"
            "        x = 1\n"
            "        assert x == 1\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_違反のline番号がdef文の行番号であること(
        self, rule: RequireAaaCommentRule
    ):
        # Arrange
        source = (
            "class TestFoo:\n"
            "    def test_正常系_何かをすること(self) -> None:\n"
            "        x = 1\n"
            "        y = 2\n"
            "        assert x + y == 3\n"
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 2  # def 文は2行目
