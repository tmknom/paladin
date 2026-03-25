from pathlib import Path

import pytest

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


class TestNoMockUsageRuleCheck:
    """NoMockUsageRule.check のテスト"""

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

    def test_check_正常系_MockとMagicMockの同時インポートで2件の違反を返すこと(self):
        # Arrange
        rule = NoMockUsageRule()
        source = "from unittest.mock import Mock, MagicMock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_通常importは違反なしを返すこと(self):
        # Arrange: import os は unittest.mock でないため違反なし（_detect_plain_import の早期リターン）
        rule = NoMockUsageRule()
        source = "import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_別モジュールのfrom_importは違反なしを返すこと(self):
        # Arrange: from os import path は unittest.mock でないため違反なし（_detect_from_import の早期リターン）
        rule = NoMockUsageRule()
        source = "from os import path\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_patchとMockの混合インポートでMockのみ検出すること(self):
        # Arrange: patchとMockの混合でMockのみ検出
        rule = NoMockUsageRule()
        source = "from unittest.mock import patch, Mock\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("import unittest.mock\n", id="import_unittest_mock"),
            pytest.param(
                "def test_foo():\n    from unittest.mock import Mock\n", id="関数内インポート"
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        rule = NoMockUsageRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
