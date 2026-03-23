from pathlib import Path

from paladin.rule.no_mock_usage import NoMockUsageRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


class TestNoMockUsageRuleMeta:
    """NoMockUsageRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoMockUsageRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-mock-usage"
        assert result.rule_name == "No Mock Usage"
        assert result.summary != ""
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoMockUsageRuleCheck:
    """NoMockUsageRule.check のテスト"""

    def test_check_正常系_from_unittest_mock_import_Mockを検出すること(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import Mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "no-mock-usage"
        assert result[0].message == "Mock のインポートは禁止されています"
        assert result[0].line == 1

    def test_check_正常系_from_unittest_mock_import_MagicMockを検出すること(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import MagicMock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "MagicMock のインポートは禁止されています"

    def test_check_正常系_import_unittest_mockを検出すること(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "import unittest.mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "unittest.mock のインポートは禁止されています"

    def test_check_正常系_MockとMagicMockの同時インポートで2件の違反を返すこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import Mock, MagicMock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_patchのみのインポートは検出しないこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import patch\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_patchとMockの混合インポートでMockのみ検出すること(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import patch, Mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "Mock のインポートは禁止されています"

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import Mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-mock-usage"
        assert violation.rule_name == "No Mock Usage"
        assert violation.reason != ""
        assert violation.suggestion != ""

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source_file = make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_通常のimport文は検出しないこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_関数内のインポートも検出すること(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "def test_foo():\n    from unittest.mock import Mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].message == "Mock のインポートは禁止されています"
        assert result[0].line == 2
