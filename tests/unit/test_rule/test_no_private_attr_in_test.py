"""no_private_attr_in_test モジュールのテスト"""

from paladin.rule.no_private_attr_in_test import (
    NoPrivateAttrInTestRule,
    PrivateAttrDetector,
)
from tests.unit.test_rule.helper import AstNodeExtractor, SourceFileFactory


class TestPrivateAttrDetector:
    """PrivateAttrDetector のテスト"""

    def test_detect_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        source = "obj._private_attr"
        node = AstNodeExtractor.first_attribute(source)
        meta = NoPrivateAttrInTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = PrivateAttrDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None
        assert result.rule_id == "no-private-attr-in-test"
        assert result.line == 1

    def test_detect_正常系_ダンダー属性はNoneを返すこと(self):
        # Arrange
        source = "obj.__dunder__"
        node = AstNodeExtractor.first_attribute(source)
        meta = NoPrivateAttrInTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = PrivateAttrDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_selfのプライベート属性はNoneを返すこと(self):
        # Arrange
        source = "self._helper"
        node = AstNodeExtractor.first_attribute(source)
        meta = NoPrivateAttrInTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = PrivateAttrDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_アンダースコアなしの属性はNoneを返すこと(self):
        # Arrange
        source = "obj.public_attr"
        node = AstNodeExtractor.first_attribute(source)
        meta = NoPrivateAttrInTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = PrivateAttrDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_ネストした属性アクセスで違反を返すこと(self):
        # Arrange
        source = "obj._rule_set._executed"
        node = AstNodeExtractor.first_attribute(source)
        meta = NoPrivateAttrInTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = PrivateAttrDetector.detect(node, meta, source_file)

        # Assert
        assert result is not None


class TestNoPrivateAttrInTestRuleCheck:
    """NoPrivateAttrInTestRule.check のテスト"""

    def test_check_正常系_プライベート属性アクセスを違反として検出すること(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "obj._private"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-private-attr-in-test"

    def test_check_正常系_複数のプライベート属性アクセスを全件検出すること(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "obj._first\nobj._second\n"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "obj._private"
        source_file = SourceFileFactory.make(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反なしのテストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "obj.public_attr"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_selfのプライベート属性は除外されること(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "self._helper"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ダンダー属性は除外されること(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "obj.__init__"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反の行番号が正しいこと(self):
        # Arrange
        rule = NoPrivateAttrInTestRule()
        source = "x = 1\nobj._first\ny = 2\nobj._second\n"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        lines = {v.line for v in result}
        assert 2 in lines
        assert 4 in lines
