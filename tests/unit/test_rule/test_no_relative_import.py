from pathlib import Path

import pytest

from paladin.rule.no_relative_import import NoRelativeImportRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


class TestNoRelativeImportRuleMeta:
    """NoRelativeImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-relative-import"
        assert result.rule_name == "No Relative Import"


class TestNoRelativeImportRuleCheck:
    """NoRelativeImportRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source_file = make_source_file("from .module import Foo\n")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-relative-import"
        assert violation.rule_name == "No Relative Import"

    def test_check_正常系_複数の相対インポートでそれぞれ個別の違反を返すこと(self):
        # Arrange
        rule = NoRelativeImportRule()
        source = "from . import Foo\nfrom ..bar import Baz\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("from myapp.module import Foo\n", id="絶対インポートのみ"),
            pytest.param("import os\n", id="importノード"),
            pytest.param("", id="空ソース"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = NoRelativeImportRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0
