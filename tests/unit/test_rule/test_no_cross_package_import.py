import ast
from pathlib import Path

import pytest

from paladin.rule.import_statement import ModulePath
from paladin.rule.no_cross_package_import import (
    CrossPackageImportChecker,
    CrossPackageImportDetector,
    EntrypointChecker,
    NoCrossPackageImportRule,
)
from paladin.rule.types import RuleMeta, SourceFiles
from tests.unit.test_rule.helpers import make_source_files


def _rule_with_prepare(
    source_files: SourceFiles,
    allow_dirs: tuple[str, ...] = ("src/myapp/rule/",),
) -> NoCrossPackageImportRule:
    """prepare() を呼んで root_packages を自動導出したルールを返す"""
    rule = NoCrossPackageImportRule(allow_dirs=allow_dirs)
    rule.prepare(source_files)
    return rule


class TestNoCrossPackageImportRuleMeta:
    """NoCrossPackageImportRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = NoCrossPackageImportRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "no-cross-package-import"
        assert result.rule_name == "No Cross Package Import"
        assert result.summary != ""
        assert result.intent != ""
        assert result.guidance != ""
        assert result.suggestion != ""


class TestNoCrossPackageImportRuleCheck:
    """NoCrossPackageImportRule.check のテスト"""

    def test_check_正常系_違反フィールド値が正しいこと_from_import(self):
        # Arrange
        source_files = make_source_files(
            ("from myapp.check import OutputFormat\n", "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("src/myapp/view/handler.py")
        assert violation.line == 1
        assert violation.column == 0
        assert violation.rule_id == "no-cross-package-import"
        assert violation.rule_name == "No Cross Package Import"
        assert "myapp.check" in violation.message
        assert "OutputFormat" in violation.message

    def test_check_正常系_allow_dirs未設定の場合は全ファイルで違反を検出すること(self):
        # Arrange
        source_files = make_source_files(
            ("from myapp.check import OutputFormat\n", "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=())

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    def test_check_正常系_エントリーポイントファイルは違反を報告しないこと(self):
        # Arrange: トップレベルに def main() がある
        source = "from myapp.check import OutputFormat\n\ndef main():\n    pass\n"
        source_files = make_source_files(
            (source, "src/myapp/main.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 0

    def test_check_正常系_main以外のトップレベル関数があってもエントリーポイントにならないこと(
        self,
    ):
        # Arrange: def helper() のみ（def main() はない）
        source = "from myapp.check import OutputFormat\n\ndef helper():\n    pass\n"
        source_files = make_source_files(
            (source, "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: エントリーポイントではないので違反を検出する
        assert len(result) == 1

    def test_check_正常系_末尾スラッシュなしのallow_dirsが正規化されて機能すること(self):
        # Arrange: 末尾スラッシュなしで指定
        source_files = make_source_files(
            ("from myapp.rule import RuleMeta\n", "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/rule/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert: 末尾スラッシュなしでも src/myapp/rule/ として認識される
        assert len(result) == 0

    def test_check_正常系_複数のallow_dirsが機能すること(self):
        # Arrange: 2つの許可ディレクトリのうち1つに一致すれば許可
        source_files = make_source_files(
            ("from myapp.rule import RuleMeta\n", "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/rule/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/config/", "src/myapp/rule/"))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルから対応プロダクションパッケージのインポートは違反なしを返すこと(
        self,
    ):
        # Arrange: tests/unit/test_check/test_orchestrator.py から paladin.check.formatter をインポート
        # → テストファイルは paladin.check と同一視されるため違反なし
        source_files = make_source_files(
            (
                "from myapp.check.formatter import CheckFormatterFactory\n",
                "tests/unit/test_check/test_orchestrator.py",
            ),
            ("x = 1\n", "src/myapp/check/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルから異なるパッケージのインポートは違反を返すこと(self):
        # Arrange: tests/unit/test_check/test_orchestrator.py から myapp.view.formatter をインポート
        # → テストファイルは myapp.check と同一視されるが myapp.view は別パッケージのため違反
        source_files = make_source_files(
            (
                "from myapp.view.formatter import ViewFormatter\n",
                "tests/unit/test_check/test_orchestrator.py",
            ),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1

    @pytest.mark.parametrize(
        "sources_and_files,check_index",
        [
            pytest.param(
                [
                    (
                        "from myapp.check.formatter import CheckFormatterFactory\n",
                        "src/myapp/check/orchestrator.py",
                    ),
                    ("x = 1\n", "src/myapp/check/__init__.py"),
                ],
                0,
                id="同一パッケージ内インポート",
            ),
            pytest.param(
                [
                    ("from . import utils\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="相対インポート",
            ),
            pytest.param(
                [
                    ("import os\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="標準ライブラリ",
            ),
            pytest.param(
                [
                    ("import requests\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="サードパーティ",
            ),
            pytest.param(
                [
                    ("from myapp.rule import RuleMeta\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/rule/__init__.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="allow_dirsに含まれる",
            ),
            pytest.param(
                [
                    ("", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="空ファイル",
            ),
            pytest.param(
                [
                    ("x = 1\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="importなし",
            ),
            pytest.param(
                [
                    ("import myapp\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/__init__.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                0,
                id="1セグメントimport",
            ),
        ],
    )
    def test_check_違反なしのケースで空を返すこと(
        self, sources_and_files: list[tuple[str, str]], check_index: int
    ) -> None:
        # Arrange
        source_files = make_source_files(*sources_and_files)
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[check_index])

        # Assert
        assert len(result) == 0

    @pytest.mark.parametrize(
        "sources_and_files",
        [
            pytest.param(
                [
                    ("from myapp.check import OutputFormat\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/check/__init__.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                id="allow_dirs外from_import",
            ),
            pytest.param(
                [
                    ("import myapp.check.context\n", "src/myapp/view/handler.py"),
                    ("x = 1\n", "src/myapp/check/__init__.py"),
                    ("x = 1\n", "src/myapp/view/__init__.py"),
                ],
                id="allow_dirs外plain_import",
            ),
        ],
    )
    def test_check_違反ありのケースで1件返すこと(
        self, sources_and_files: list[tuple[str, str]]
    ) -> None:
        # Arrange
        source_files = make_source_files(*sources_and_files)
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))

        # Act
        result = rule.check(source_files.files[0])

        # Assert
        assert len(result) == 1


class TestEntrypointChecker:
    """EntrypointChecker のテスト"""

    def test_is_entrypoint_正常系_main関数があればTrueを返すこと(self):
        tree = ast.parse("def main(): pass\n")
        assert EntrypointChecker.is_entrypoint(tree) is True

    def test_is_entrypoint_正常系_main関数がなければFalseを返すこと(self):
        tree = ast.parse("def foo(): pass\n")
        assert EntrypointChecker.is_entrypoint(tree) is False


class TestCrossPackageImportChecker:
    """CrossPackageImportChecker のテスト"""

    _STDLIB = frozenset({"os", "sys"})
    _ROOT = ("myapp",)
    _ALLOW = ("src/myapp/rule/",)

    def test_is_cross_package_正常系_標準ライブラリはFalseを返すこと(self):
        module = ModulePath("os.path")
        assert (
            CrossPackageImportChecker.is_cross_package(
                module, frozenset({"myapp.view"}), self._STDLIB, self._ROOT, self._ALLOW
            )
            is False
        )

    def test_is_cross_package_正常系_ルートパッケージ外はFalseを返すこと(self):
        module = ModulePath("requests.auth")
        assert (
            CrossPackageImportChecker.is_cross_package(
                module, frozenset({"myapp.view"}), self._STDLIB, self._ROOT, self._ALLOW
            )
            is False
        )

    def test_is_cross_package_正常系_同一パッケージはFalseを返すこと(self):
        module = ModulePath("myapp.view.formatter")
        assert (
            CrossPackageImportChecker.is_cross_package(
                module, frozenset({"myapp.view"}), self._STDLIB, self._ROOT, self._ALLOW
            )
            is False
        )

    def test_is_cross_package_正常系_allow_dirsに含まれるパッケージはFalseを返すこと(self):
        module = ModulePath("myapp.rule.types")
        assert (
            CrossPackageImportChecker.is_cross_package(
                module, frozenset({"myapp.view"}), self._STDLIB, self._ROOT, self._ALLOW
            )
            is False
        )

    def test_is_cross_package_正常系_クロスパッケージはTrueを返すこと(self):
        module = ModulePath("myapp.check.formatter")
        assert (
            CrossPackageImportChecker.is_cross_package(
                module, frozenset({"myapp.view"}), self._STDLIB, self._ROOT, self._ALLOW
            )
            is True
        )


class TestCrossPackageImportDetector:
    """CrossPackageImportDetector のテスト"""

    def test_detect_from_import_正常系_複数名で複数Violationを返すこと(self):
        source = "from myapp.check import OutputFormat, Rule\n"
        source_files = make_source_files(
            (source, "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))
        source_file = source_files.files[0]
        stmt = source_file.imports[0]
        import_module = ModulePath("myapp.check")
        result = CrossPackageImportDetector.detect_from_import(
            stmt, import_module, source_file, rule.meta
        )
        assert len(result) == 2
        assert result[0].rule_id == "no-cross-package-import"

    def test_detect_plain_import_正常系_Violationを返すこと(self):
        source = "import myapp.check.context\n"
        source_files = make_source_files(
            (source, "src/myapp/view/handler.py"),
            ("x = 1\n", "src/myapp/check/__init__.py"),
            ("x = 1\n", "src/myapp/view/__init__.py"),
        )
        rule = _rule_with_prepare(source_files, allow_dirs=("src/myapp/rule/",))
        source_file = source_files.files[0]
        stmt = source_file.imports[0]
        result = CrossPackageImportDetector.detect_plain_import(
            stmt, "myapp.check.context", source_file, rule.meta
        )
        assert result.rule_id == "no-cross-package-import"
