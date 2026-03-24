from pathlib import Path

import pytest

from paladin.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.rule.types import RuleMeta, SourceFiles
from tests.unit.test_rule.helpers import make_source_file, make_source_files


def _rule_with_prepare(source_files: SourceFiles) -> RequireQualifiedThirdPartyRule:
    """prepare() を呼んで root_packages を自動導出したルールを返す"""
    rule = RequireQualifiedThirdPartyRule()
    rule.prepare(source_files)
    return rule


class TestRequireQualifiedThirdPartyRuleMeta:
    """RequireQualifiedThirdPartyRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "require-qualified-third-party"
        assert result.rule_name == "Require Qualified Third Party"


class TestRequireQualifiedThirdPartyRuleCheck:
    """RequireQualifiedThirdPartyRule.check のテスト"""

    def test_check_正常系_from_importの違反フィールド値が正しいこと(self):
        # Arrange
        source_files = make_source_files(
            ("from requests import get\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/paladin/example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"

    def test_check_正常系_import_asの違反フィールド値が正しいこと(self):
        # Arrange
        source_files = make_source_files(
            ("import requests as req\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/paladin/example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"

    def test_check_正常系_from_importで複数名をインポートした場合に名前ごとに個別の違反を返すこと(
        self,
    ):
        # Arrange
        source_files = make_source_files(
            ("from requests import get, post\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 2

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("from os.path import join\n", id="標準ライブラリのfrom_import"),
            pytest.param("from paladin.check import Rule\n", id="ルートパッケージのfrom_import"),
            pytest.param("from . import utils\n", id="相対インポート"),
            pytest.param("import os as operating_system\n", id="標準ライブラリのimport_as"),
            pytest.param("import paladin as p\n", id="ルートパッケージのimport_as"),
            pytest.param("import requests\n", id="通常のimport文"),
            pytest.param(
                "from tests.unit.fakes import InMemoryFsReader\n",
                id="testsパッケージのfrom_import",
            ),
            pytest.param("", id="空ソース"),
            pytest.param("x = 1\n", id="importなし"),
            pytest.param("from . import utils\n", id="node_moduleがNoneの相対インポート"),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(self, source: str) -> None:
        # Arrange
        source_files = make_source_files(("", "src/paladin/module.py"))
        source_file = make_source_file(source, "src/paladin/example.py")
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_複数のroot_packagesで除外できること(self):
        # Arrange: src/paladin/ と src/mylib/ の両方がルートパッケージとして導出される
        source_files = make_source_files(
            ("from mylib import foo\n", "src/paladin/example.py"),
            ("x = 1\n", "src/mylib/core.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "source",
        [
            pytest.param("from requests import get\n", id="サードパーティのfrom_import"),
            pytest.param(
                "from requests.auth import HTTPBasicAuth\n",
                id="サードパーティのサブモジュールfrom_import",
            ),
            pytest.param("import requests as req\n", id="サードパーティのimport_as"),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(self, source: str) -> None:
        # Arrange
        source_files = make_source_files((source, "src/paladin/example.py"))
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1


class TestRequireQualifiedThirdPartyRulePrepare:
    """RequireQualifiedThirdPartyRule.prepare() のテスト"""

    def test_prepare_正常系_source_filesからルートパッケージが自動導出されること(self):
        # Arrange: src/paladin/ があれば paladin が root_packages に含まれる
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        rule = RequireQualifiedThirdPartyRule()
        rule.prepare(source_files)
        source_with_paladin_import = make_source_file(
            "from paladin.check import Rule\n", "src/paladin/example.py"
        )

        # Act
        # prepare() 後は paladin が root_packages に含まれるため違反なし
        result = rule.check(source_with_paladin_import)

        # Assert
        assert len(result) == 0

    def test_prepare_正常系_testsが常にroot_packagesに含まれること(self):
        # Arrange: tests は src/ 配下になくても常に含まれる
        source_files = make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        rule = RequireQualifiedThirdPartyRule()
        rule.prepare(source_files)
        source = make_source_file(
            "from tests.unit.fakes import InMemoryFsReader\n", "src/paladin/example.py"
        )

        # Act
        # tests からのインポートは違反なし
        result = rule.check(source)

        # Assert
        assert len(result) == 0

    def test_prepare_正常系_準備なしでは空のroot_packagesで動作すること(self):
        # Arrange: prepare() を呼ばない場合は root_packages が空
        rule = RequireQualifiedThirdPartyRule()
        source = make_source_file("from requests import get\n", "example.py")

        # Act: 空の root_packages でも check() は動作する（全モジュールが対象）
        result = rule.check(source)

        # Assert: requests はサードパーティなので違反
        assert len(result) == 1
