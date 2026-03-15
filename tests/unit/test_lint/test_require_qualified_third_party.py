import ast
from pathlib import Path

from paladin.lint.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.lint.types import RuleMeta, SourceFile


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestRequireQualifiedThirdPartyRuleMeta:
    """RequireQualifiedThirdPartyRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "require-qualified-third-party"
        assert result.rule_name == "Require Qualified Third Party"
        assert (
            result.summary
            == "サードパーティライブラリの直接インポートとエイリアスインポートを禁止する"
        )
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestRequireQualifiedThirdPartyRuleCheckFromImport:
    """RequireQualifiedThirdPartyRule.check の from import パターンのテスト"""

    def test_check_正常系_サードパーティのfrom_importで違反を1件返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_from_importの違反フィールド値が正しいこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"

    def test_check_正常系_from_importで複数名をインポートした場合に名前ごとに個別の違反を返すこと(
        self,
    ):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get, post\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_サードパーティのサブモジュールfrom_importで違反を返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests.auth import HTTPBasicAuth\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1


class TestRequireQualifiedThirdPartyRuleCheckImportAs:
    """RequireQualifiedThirdPartyRule.check の import as パターンのテスト"""

    def test_check_正常系_サードパーティのimport_asで違反を1件返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests as req\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_import_asの違反フィールド値が正しいこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests as req\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"


class TestRequireQualifiedThirdPartyRuleCheckExclusions:
    """RequireQualifiedThirdPartyRule.check の除外パターンのテスト"""

    def test_check_正常系_標準ライブラリのfrom_importは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from os.path import join\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from paladin.check import Rule\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_相対インポートは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from . import utils\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_標準ライブラリのimport_asは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import os as operating_system\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのimport_asは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import paladin as p\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_通常のimport文は違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_testsパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin", "tests"))
        source = "from tests.unit.fakes import InMemoryFsReader\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数のroot_packagesで除外できること(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin", "mylib"))
        source = "from mylib import foo\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()


class TestRequireQualifiedThirdPartyRuleCheckEdgeCases:
    """RequireQualifiedThirdPartyRule.check のエッジケースのテスト"""

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source_file = _make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_importを含まないソースコードは空タプルを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "x = 1\nreturn x\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_node_moduleがNoneの相対インポートは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        # from . import utils は node.module=None, node.level=1
        source = "from . import utils\n"
        source_file = _make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert result == ()
