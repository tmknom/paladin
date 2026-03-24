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
            pytest.param("from unittest.mock import patch\n", id="patchのみ"),
            pytest.param("", id="空ソース"),
            pytest.param("import os\n", id="通常import"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = NoMockUsageRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("from unittest.mock import Mock\n", id="from_unittest_mock_import_Mock"),
            pytest.param(
                "from unittest.mock import MagicMock\n",
                id="from_unittest_mock_import_MagicMock",
            ),
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
