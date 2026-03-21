import ast
from pathlib import Path

from paladin.rule.rule_set import RuleSet
from paladin.rule.rule_set_factory import RuleSetFactory
from paladin.rule.types import SourceFile, SourceFiles


def _make_source_file_for_import(source: str, filename: str = "src/myapp/test.py") -> SourceFile:
    """インポートテスト用の SourceFile を作る"""
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


class TestRuleSetFactory:
    """RuleSetFactory.create() メソッドのテスト"""

    def test_create_正常系_RuleSetインスタンスを返すこと(self):
        result = RuleSetFactory().create()
        assert isinstance(result, RuleSet)

    def test_create_正常系_全ルールが登録されていること(self):
        result = RuleSetFactory().create()
        rule_ids = result.rule_ids
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids

    def test_create_正常系_呼び出すたびに独立したインスタンスを返すこと(self):
        a = RuleSetFactory().create()
        b = RuleSetFactory().create()
        assert a is not b

    def test_create_正常系_no_direct_internal_importルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-direct-internal-import" in result.rule_ids

    def test_create_正常系_no_mock_usageルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-mock-usage" in result.rule_ids

    def test_create_正常系_全ルールが登録されていること_9ルール(self):
        result = RuleSetFactory().create()
        rule_ids = result.rule_ids
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
        assert "no-non-init-all" in rule_ids
        assert "no-cross-package-reexport" in rule_ids
        assert "no-mock-usage" in rule_ids
        assert "no-unused-export" in rule_ids

    def test_create_正常系_no_deep_nestingルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-deep-nesting" in result.rule_ids

    def test_create_正常系_全ルールが登録されていること_10ルール(self):
        result = RuleSetFactory().create()
        rule_ids = result.rule_ids
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
        assert "no-non-init-all" in rule_ids
        assert "no-cross-package-reexport" in rule_ids
        assert "no-mock-usage" in rule_ids
        assert "no-unused-export" in rule_ids
        assert "no-deep-nesting" in rule_ids

    def test_create_正常系_no_third_party_importルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-third-party-import" in result.rule_ids

    def test_create_正常系_全ルールが登録されていること_11ルール(self):
        result = RuleSetFactory().create()
        rule_ids = result.rule_ids
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
        assert "no-non-init-all" in rule_ids
        assert "no-cross-package-reexport" in rule_ids
        assert "no-mock-usage" in rule_ids
        assert "no-unused-export" in rule_ids
        assert "no-deep-nesting" in rule_ids
        assert "no-third-party-import" in rule_ids

    def test_create_正常系_rule_optionsでallow_dirsを指定できること(self):
        # Arrange
        rule_options: dict[str, dict[str, object]] = {
            "no-third-party-import": {"allow-dirs": ["src/foundation/"]}
        }

        # Act
        result = RuleSetFactory().create(rule_options=rule_options)

        # Assert: ルールが登録されていること
        assert "no-third-party-import" in result.rule_ids

    def test_create_正常系_引数なしで後方互換性を保つこと(self):
        # allow_dirs 未指定でもデフォルト引数で呼び出せる
        result = RuleSetFactory().create()
        assert "no-third-party-import" in result.rule_ids

    def test_create_正常系_allow_dirsがlist以外の場合は空タプルを返すこと(self):
        # Arrange: allow-dirs に不正な型（文字列）を渡す
        rule_options: dict[str, dict[str, object]] = {
            "no-third-party-import": {"allow-dirs": "src/foundation/"}
        }

        # Act
        result = RuleSetFactory().create(rule_options=rule_options)

        # Assert: 不正な型でも例外なく動作する
        assert "no-third-party-import" in result.rule_ids

    def test_create_正常系_no_unused_exportルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-unused-export" in result.rule_ids

    def test_create_正常系_no_cross_package_reexportルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-cross-package-reexport" in result.rule_ids

    def test_create_正常系_no_non_init_allルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-non-init-all" in result.rule_ids

    def test_create_正常系_testsパッケージはデフォルトでroot_packagesに含まれること(self):
        # Arrange: RuleSet.run() が prepare() を呼び tests が自動でルートパッケージになる
        source_file = _make_source_file_for_import("from tests.foo import bar\n")
        source_files = SourceFiles(files=(source_file,))
        rule_set = RuleSetFactory().create()

        # Act
        result = rule_set.run(source_files)

        # Assert: tests は root_packages に含まれるため require-qualified-third-party の違反なし
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_srcレイアウトのプロジェクトパッケージが自動導出されること(self):
        # Arrange: src/myapp/ 配下のファイルを渡すと myapp が root_packages に自動導出される
        source_file = _make_source_file_for_import(
            "from myapp.utils import helper\n", "src/myapp/test.py"
        )
        source_files = SourceFiles(files=(source_file,))
        rule_set = RuleSetFactory().create()

        # Act
        result = rule_set.run(source_files)

        # Assert: myapp が自動導出されるため require-qualified-third-party の違反なし
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0
