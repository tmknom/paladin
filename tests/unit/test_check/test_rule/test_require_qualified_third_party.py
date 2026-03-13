import ast
from pathlib import Path

from paladin.check.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.check.rule.types import RuleMeta
from paladin.check.types import ParsedFile


def _make_parsed_file(source: str, filename: str = "example.py") -> ParsedFile:
    return ParsedFile(file_path=Path(filename), tree=ast.parse(source))


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


class TestRequireQualifiedThirdPartyRuleCheckFromImport:
    """RequireQualifiedThirdPartyRule.check の from import パターンのテスト"""

    def test_check_正常系_サードパーティのfrom_importで違反を1件返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_from_importの違反フィールド値が正しいこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"
        assert (
            violation.message
            == "`from requests import get` はサードパーティライブラリの直接インポートである"
        )
        assert (
            violation.reason
            == "外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある"
        )
        assert (
            violation.suggestion
            == "`import requests` に書き換え、使用箇所を `requests.get` 形式に修正する"
        )

    def test_check_正常系_from_importで複数名をインポートした場合に名前ごとに個別の違反を返すこと(
        self,
    ):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests import get, post\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 2

    def test_check_正常系_サードパーティのサブモジュールfrom_importで違反を返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from requests.auth import HTTPBasicAuth\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1


class TestRequireQualifiedThirdPartyRuleCheckImportAs:
    """RequireQualifiedThirdPartyRule.check の import as パターンのテスト"""

    def test_check_正常系_サードパーティのimport_asで違反を1件返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests as req\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_import_asの違反フィールド値が正しいこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests as req\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "require-qualified-third-party"
        assert violation.rule_name == "Require Qualified Third Party"
        assert (
            violation.message
            == "`import requests as req` はサードパーティライブラリのエイリアスインポートである"
        )
        assert (
            violation.reason
            == "外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある"
        )
        assert violation.suggestion == "`import requests` に書き換え、エイリアスなしで使用する"


class TestRequireQualifiedThirdPartyRuleCheckExclusions:
    """RequireQualifiedThirdPartyRule.check の除外パターンのテスト"""

    def test_check_正常系_標準ライブラリのfrom_importは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from os.path import join\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from paladin.check import Rule\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_相対インポートは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "from . import utils\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_標準ライブラリのimport_asは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import os as operating_system\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのimport_asは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import paladin as p\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_通常のimport文は違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "import requests\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_正常系_複数のroot_packagesで除外できること(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin", "mylib"))
        source = "from mylib import foo\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()


class TestRequireQualifiedThirdPartyRuleCheckEdgeCases:
    """RequireQualifiedThirdPartyRule.check のエッジケースのテスト"""

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        parsed_file = _make_parsed_file("")

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_importを含まないソースコードは空タプルを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        source = "x = 1\nreturn x\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()

    def test_check_エッジケース_node_moduleがNoneの相対インポートは違反なしを返すこと(self):
        # Arrange
        rule = RequireQualifiedThirdPartyRule(root_packages=("paladin",))
        # from . import utils は node.module=None, node.level=1
        source = "from . import utils\n"
        parsed_file = _make_parsed_file(source)

        # Act
        result = rule.check(parsed_file)

        # Assert
        assert result == ()
