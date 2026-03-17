import ast
from pathlib import Path

from paladin.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles


def _make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def _make_source_files(*pairs: tuple[str, str]) -> SourceFiles:
    return SourceFiles(files=tuple(_make_source_file(src, name) for src, name in pairs))


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
        # Arrange: src/paladin/ 配下に paladin パッケージがあることを示すファイル群
        source_files = _make_source_files(
            ("from requests import get\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_from_importの違反フィールド値が正しいこと(self):
        # Arrange
        source_files = _make_source_files(
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

    def test_check_正常系_from_importで複数名をインポートした場合に名前ごとに個別の違反を返すこと(
        self,
    ):
        # Arrange
        source_files = _make_source_files(
            ("from requests import get, post\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 2

    def test_check_正常系_サードパーティのサブモジュールfrom_importで違反を返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("from requests.auth import HTTPBasicAuth\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1


class TestRequireQualifiedThirdPartyRuleCheckImportAs:
    """RequireQualifiedThirdPartyRule.check の import as パターンのテスト"""

    def test_check_正常系_サードパーティのimport_asで違反を1件返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("import requests as req\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_import_asの違反フィールド値が正しいこと(self):
        # Arrange
        source_files = _make_source_files(
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


class TestRequireQualifiedThirdPartyRuleCheckExclusions:
    """RequireQualifiedThirdPartyRule.check の除外パターンのテスト"""

    def test_check_正常系_標準ライブラリのfrom_importは違反なしを返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("from os.path import join\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange: src/paladin/ がルートパッケージとして自動導出される
        source_files = _make_source_files(
            ("from paladin.check import Rule\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_相対インポートは違反なしを返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("from . import utils\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_標準ライブラリのimport_asは違反なしを返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("import os as operating_system\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_ルートパッケージのimport_asは違反なしを返すこと(self):
        # Arrange: paladin が root_packages に自動導出される
        source_files = _make_source_files(
            ("import paladin as p\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_通常のimport文は違反なしを返すこと(self):
        # Arrange
        source_files = _make_source_files(
            ("import requests\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_testsパッケージのfrom_importは違反なしを返すこと(self):
        # Arrange: tests は常に root_packages に含まれる
        source_files = _make_source_files(
            ("from tests.unit.fakes import InMemoryFsReader\n", "src/paladin/example.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_正常系_複数のroot_packagesで除外できること(self):
        # Arrange: src/paladin/ と src/mylib/ の両方がルートパッケージとして導出される
        source_files = _make_source_files(
            ("from mylib import foo\n", "src/paladin/example.py"),
            ("x = 1\n", "src/mylib/core.py"),
        )
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()


class TestRequireQualifiedThirdPartyRuleCheckEdgeCases:
    """RequireQualifiedThirdPartyRule.check のエッジケースのテスト"""

    def test_check_エッジケース_空のソースコードは空タプルを返すこと(self):
        # Arrange
        source_files = _make_source_files(("", "src/paladin/example.py"))
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_エッジケース_importを含まないソースコードは空タプルを返すこと(self):
        # Arrange
        source_files = _make_source_files(("x = 1\n", "src/paladin/example.py"))
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()

    def test_check_エッジケース_node_moduleがNoneの相対インポートは違反なしを返すこと(self):
        # Arrange: from . import utils は node.module=None, node.level=1
        source_files = _make_source_files(("from . import utils\n", "src/paladin/example.py"))
        rule = _rule_with_prepare(source_files)

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert result == ()


class TestRequireQualifiedThirdPartyRulePrepare:
    """RequireQualifiedThirdPartyRule.prepare() のテスト"""

    def test_prepare_正常系_source_filesからルートパッケージが自動導出されること(self):
        # Arrange: src/paladin/ があれば paladin が root_packages に含まれる
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        rule = RequireQualifiedThirdPartyRule()

        rule.prepare(source_files)

        # prepare() 後は paladin が root_packages に含まれるため違反なし
        source_with_paladin_import = _make_source_file(
            "from paladin.check import Rule\n", "src/paladin/example.py"
        )
        result = rule.check(source_with_paladin_import)
        assert result == ()

    def test_prepare_正常系_testsが常にroot_packagesに含まれること(self):
        # Arrange: tests は src/ 配下になくても常に含まれる
        source_files = _make_source_files(
            ("x = 1\n", "src/paladin/module.py"),
        )
        rule = RequireQualifiedThirdPartyRule()
        rule.prepare(source_files)

        # tests からのインポートは違反なし
        source = _make_source_file(
            "from tests.unit.fakes import InMemoryFsReader\n", "src/paladin/example.py"
        )
        result = rule.check(source)
        assert result == ()

    def test_prepare_正常系_準備なしでは空のroot_packagesで動作すること(self):
        # Arrange: prepare() を呼ばない場合は root_packages が空
        rule = RequireQualifiedThirdPartyRule()
        source = _make_source_file("from requests import get\n", "example.py")

        # Act: 空の root_packages でも check() は動作する（全モジュールが対象）
        result = rule.check(source)

        # Assert: requests はサードパーティなので違反
        assert len(result) == 1
