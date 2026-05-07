"""no_frozen_instance_test モジュールのテスト"""

from paladin.rule.no_frozen_instance_test import (
    FrozenInstanceTestDetector,
    NoFrozenInstanceTestRule,
)
from tests.unit.test_rule.helper import AstNodeExtractor, SourceFileFactory


class TestFrozenInstanceTestDetector:
    """FrozenInstanceTestDetector のテスト"""

    def test_detect_正常系_FrozenInstanceError以外の例外はNoneを返すこと(self):
        # Arrange
        source = "pytest.raises(ValueError)"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_引数なしのpytest_raisesはNoneを返すこと(self):
        # Arrange
        source = "pytest.raises()"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_pytest_raises以外の呼び出しはNoneを返すこと(self):
        # Arrange
        source = "some_func(FrozenInstanceError)"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_raises以外の属性名はNoneを返すこと(self):
        # Arrange
        source = "pytest.other(FrozenInstanceError)"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_pytest以外のオブジェクトのraisesはNoneを返すこと(self):
        # Arrange
        source = "other.raises(FrozenInstanceError)"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None

    def test_detect_正常系_ネストした属性呼び出しはNoneを返すこと(self):
        # Arrange
        source = "a.b.raises(FrozenInstanceError)"
        node = AstNodeExtractor.first_call(source)
        meta = NoFrozenInstanceTestRule().meta
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = FrozenInstanceTestDetector.detect(node, meta, source_file)

        # Assert
        assert result is None


class TestNoFrozenInstanceTestRuleCheck:
    """NoFrozenInstanceTestRule.check のテスト"""

    def test_check_正常系_dataclasses経由のFrozenInstanceError違反を検出すること(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = "pytest.raises(dataclasses.FrozenInstanceError)"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-frozen-instance-test"

    def test_check_正常系_直接インポートのFrozenInstanceError違反を検出すること(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = "pytest.raises(FrozenInstanceError)"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-frozen-instance-test"

    def test_check_正常系_両パターンを同時に検出すること(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = (
            "pytest.raises(dataclasses.FrozenInstanceError)\npytest.raises(FrozenInstanceError)\n"
        )
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        assert all(v.rule_id == "no-frozen-instance-test" for v in result)

    def test_check_正常系_非テストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = "pytest.raises(FrozenInstanceError)"
        source_file = SourceFileFactory.make(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反なしのテストファイルは空タプルを返すこと(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = "pytest.raises(ValueError)"
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_違反の行番号が正しいこと(self):
        # Arrange
        rule = NoFrozenInstanceTestRule()
        source = (
            "x = 1\n"
            "pytest.raises(dataclasses.FrozenInstanceError)\n"
            "y = 2\n"
            "pytest.raises(FrozenInstanceError)\n"
        )
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2
        lines = {v.line for v in result}
        assert 2 in lines
        assert 4 in lines
