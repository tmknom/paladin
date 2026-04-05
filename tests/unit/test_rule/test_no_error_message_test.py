"""no_error_message_test モジュールのテスト"""

import ast

import pytest

from paladin.rule.no_error_message_test import (
    NoErrorMessageTestRule,
    PytestRaisesMatchDetector,
    StrExcInfoValueDetector,
)
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


def _make_call_node(source: str) -> ast.Call:
    """ソースコードから最初の ast.Call ノードを取り出す"""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            return node
    raise AssertionError(f"ast.Call が見つかりません: {source!r}")


def _make_meta() -> RuleMeta:
    return NoErrorMessageTestRule().meta


class TestPytestRaisesMatchDetector:
    """PytestRaisesMatchDetector のテスト"""

    def test_detect_正常系_pytest_raises_matchを検出すること(self):
        # Arrange
        source = 'pytest.raises(ValueError, match="msg")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None
        assert result.rule_id == "no-error-message-test"
        assert result.line == 1

    def test_detect_正常系_matchが正規表現でも検出すること(self):
        # Arrange
        source = r'pytest.raises(ValueError, match=r"msg.*")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None

    def test_detect_正常系_matchなしのpytest_raisesはNoneを返すこと(self):
        # Arrange
        source = "pytest.raises(ValueError)"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_pytest_raises以外の呼び出しはNoneを返すこと(self):
        # Arrange
        source = 'some_func(match="msg")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_raises以外の属性名はNoneを返すこと(self):
        # Arrange
        source = 'pytest.other(match="msg")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_pytest以外のオブジェクトのraisesはNoneを返すこと(self):
        # Arrange
        source = 'other.raises(match="msg")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_ネストした属性呼び出しはNoneを返すこと(self):
        # Arrange
        source = 'a.b.raises(match="msg")'
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = PytestRaisesMatchDetector.detect(node, meta, source_file)

        # Assert
        assert result is None


class TestStrExcInfoValueDetector:
    """StrExcInfoValueDetector のテスト"""

    def test_detect_正常系_str_exc_info_valueを検出すること(self):
        # Arrange
        source = "str(exc_info.value)"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None
        assert result.rule_id == "no-error-message-test"
        assert result.line == 1

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("str(e.value)", id="e.value"),
            pytest.param("str(error.value)", id="error.value"),
        ],
    )
    def test_detect_正常系_任意の変数名でも検出すること(self, source: str):
        # Arrange
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("str(123)", id="literal"),
            pytest.param("str(some_var)", id="name"),
        ],
    )
    def test_detect_正常系_str呼び出しだが引数がAttribute以外はNoneを返すこと(self, source: str):
        # Arrange
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_str以外のName呼び出しはNoneを返すこと(self):
        # Arrange
        source = "repr(exc_info.value)"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_str引数なしはNoneを返すこと(self):
        # Arrange
        source = "str()"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_valueのオブジェクトがNameでない場合はNoneを返すこと(self):
        # Arrange
        source = "str(a.b.value)"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_attrがvalue以外はNoneを返すこと(self):
        # Arrange
        source = "str(exc_info.args)"
        node = _make_call_node(source)
        meta = _make_meta()
        source_file = make_test_source_file(source)

        # Act
        result = StrExcInfoValueDetector.detect(node, meta, source_file)

        # Assert
        assert result is None


class TestNoErrorMessageTestRuleMeta:
    """NoErrorMessageTestRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoErrorMessageTestRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-error-message-test"
        assert result.rule_name == "No Error Message Test"


class TestNoErrorMessageTestRuleCheck:
    """NoErrorMessageTestRule.check のテスト"""

    def test_check_正常系_pytest_raises_match違反を検出すること(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = 'pytest.raises(ValueError, match="msg")'
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-error-message-test"

    def test_check_正常系_str_exc_info_value違反を検出すること(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = 'assert "msg" in str(exc_info.value)'
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-error-message-test"

    def test_check_正常系_両パターンを同時に検出すること(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = 'pytest.raises(ValueError, match="msg")\nassert "msg" in str(exc_info.value)\n'
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = 'pytest.raises(ValueError, match="msg")'
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反なしのテストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = "pytest.raises(ValueError)"
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反の行番号が正しいこと(self):
        # Arrange
        rule = NoErrorMessageTestRule()
        source = (
            "x = 1\n"
            'pytest.raises(ValueError, match="msg")\n'
            "y = 2\n"
            'assert "msg" in str(exc_info.value)\n'
        )
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        lines = {v.line for v in result}
        assert 2 in lines
        assert 4 in lines
