"""RequireEmptyTestInitRuleクラスのテスト"""

import pytest

from paladin.rule.require_empty_test_init import RequireEmptyTestInitRule
from tests.unit.test_rule.helper import make_source_file, make_test_source_file


class TestRequireEmptyTestInitRuleCheck:
    """RequireEmptyTestInitRuleクラスのcheckメソッドのテスト"""

    def test_check_正常系_テストinit_pyにコードがある場合に違反を1件返すこと(self):
        # Arrange
        rule = RequireEmptyTestInitRule()
        source_file = make_test_source_file("import os\n", "tests/__init__.py")

        # Act
        violations = rule.check(source_file)

        # Assert
        assert len(violations) == 1
        assert violations[0].rule_id == "require-empty-test-init"
        assert violations[0].line == 1

    def test_check_正常系_テストinit_pyが空の場合に違反なしを返すこと(self):
        # Arrange
        rule = RequireEmptyTestInitRule()
        source_file = make_test_source_file("", "tests/__init__.py")

        # Act
        violations = rule.check(source_file)

        # Assert
        assert len(violations) == 0

    @pytest.mark.parametrize(
        ("source", "filename"),
        [
            pytest.param("import os\n", "src/__init__.py", id="非テストのinit_py"),
            pytest.param("import os\n", "tests/test_example.py", id="テストの非init_py"),
            pytest.param("import os\n", "src/module.py", id="非テストの非init_py"),
        ],
    )
    def test_check_エッジケース_非対象ファイルの場合に違反なしを返すこと(
        self, source: str, filename: str
    ):
        # Arrange
        rule = RequireEmptyTestInitRule()
        source_file = make_source_file(source, filename)

        # Act
        violations = rule.check(source_file)

        # Assert
        assert len(violations) == 0

    def test_check_エッジケース_空白のみのテストinit_pyで違反なしを返すこと(self):
        # Arrange
        rule = RequireEmptyTestInitRule()
        source_file = make_test_source_file("  \n\n  ", "tests/__init__.py")

        # Act
        violations = rule.check(source_file)

        # Assert
        assert len(violations) == 0
