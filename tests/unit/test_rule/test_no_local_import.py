from pathlib import Path

import pytest

from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file


class TestNoLocalImportRuleMeta:
    """NoLocalImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoLocalImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-local-import"
        assert result.rule_name == "No Local Import"


class TestNoLocalImportRuleCheck:
    """NoLocalImportRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 2
        assert violation.column == 4
        assert violation.rule_id == "no-local-import"
        assert violation.rule_name == "No Local Import"

    def test_check_正常系_複数箇所の違反をすべて返すこと(self):
        # Arrange
        rule = NoLocalImportRule()
        source = "def foo():\n    import os\ndef bar():\n    from sys import argv\n"
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("import os\nfrom sys import argv\n", id="トップレベルimport"),
            pytest.param(
                "from __future__ import annotations\n"
                "TYPE_CHECKING = False\n"
                "if TYPE_CHECKING:\n"
                "    import os\n",
                id="TYPE_CHECKINGブロック",
            ),
            pytest.param(
                "from __future__ import annotations\n"
                "import typing\n"
                "if typing.TYPE_CHECKING:\n"
                "    import os\n",
                id="TYPE_CHECKING属性",
            ),
            pytest.param("", id="空ソース"),
            pytest.param("def foo():\n    x = 1\n    return x\n", id="importなし"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        rule = NoLocalImportRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("def foo():\n    import os\n", id="関数内import"),
            pytest.param("def foo():\n    from os import path\n", id="関数内from_import"),
            pytest.param("class Foo:\n    import os\n", id="クラス直下import"),
            pytest.param(
                "class Foo:\n    def bar(self):\n        import os\n", id="メソッド内import"
            ),
            pytest.param(
                "def outer():\n    def inner():\n        import os\n", id="ネスト関数内import"
            ),
            pytest.param("async def foo():\n    import os\n", id="async_def内import"),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        rule = NoLocalImportRule()
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
