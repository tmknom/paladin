import ast
import logging
from pathlib import Path

import pytest

from paladin.rule.rule_set import RuleSet
from paladin.rule.rule_set_factory import RuleSetFactory
from paladin.rule.types import SourceFile, SourceFiles


def _make_source_file_for_import(source: str) -> SourceFile:
    """インポートテスト用の SourceFile を作る"""
    return SourceFile(file_path=Path("test.py"), tree=ast.parse(source), source=source)


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

    def test_create_正常系_rule_optionsでroot_packagesを指定できること(self):
        # Arrange: myapp をルートパッケージとして設定
        rule_options = {"require-qualified-third-party": {"root-packages": ["myapp"]}}
        rule_set = RuleSetFactory().create(rule_options=rule_options)
        source_file = _make_source_file_for_import("from myapp.foo import bar\n")

        # Act: myapp からのインポートは root_packages に含まれるため違反なし
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert: require-qualified-third-party の違反がないこと
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_rule_optionsがNoneの場合デフォルト値が使われること(self):
        # Arrange: デフォルト root_packages = ("tests",)（project_name なし）
        rule_set = RuleSetFactory().create(rule_options=None)
        source_file = _make_source_file_for_import("from tests.foo import bar\n")

        # Act: tests はデフォルトの root_packages に含まれるため違反なし
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_rule_optionsが空dictの場合デフォルト値が使われること(self):
        # Arrange: デフォルト root_packages = ("tests",)（project_name なし）
        rule_set = RuleSetFactory().create(rule_options={})
        source_file = _make_source_file_for_import("from tests.foo import bar\n")

        # Act
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_対象ルールIDのエントリがない場合デフォルト値が使われること(self):
        # Arrange: 別ルール ID のエントリのみ（require-qualified-third-party エントリなし）
        rule_options = {"no-relative-import": {"some-param": "value"}}
        rule_set = RuleSetFactory().create(rule_options=rule_options)
        source_file = _make_source_file_for_import("from tests.foo import bar\n")

        # Act
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert: デフォルトの root_packages が使われるため tests からのインポートは違反なし
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_kebab_caseのパラメータ名がsnake_caseに変換されること(self):
        # Arrange: "root-packages" (kebab-case) が "root_packages" (snake_case) に変換される
        rule_options = {"require-qualified-third-party": {"root-packages": ["myapp"]}}
        rule_set = RuleSetFactory().create(rule_options=rule_options)

        # "myapp" が root_packages に含まれているため違反なし
        source_file = _make_source_file_for_import("from myapp.utils import helper\n")
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_未知ルールIDに対して警告を出力すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        rule_options = {"unknown-rule": {"key": "value"}}

        # Act
        with caplog.at_level(logging.WARNING, logger="paladin.rule.rule_set_factory"):
            RuleSetFactory().create(rule_options=rule_options)

        # Assert
        assert any("unknown-rule" in record.message for record in caplog.records)

    def test_create_正常系_未知パラメータに対して警告を出力すること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange
        rule_options = {"require-qualified-third-party": {"unknown-param": "value"}}

        # Act
        with caplog.at_level(logging.WARNING, logger="paladin.rule.rule_set_factory"):
            RuleSetFactory().create(rule_options=rule_options)

        # Assert
        assert any("unknown-param" in record.message for record in caplog.records)

    def test_create_正常系_未知パラメータがあっても既知パラメータは正常に適用されること(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange: 既知パラメータと未知パラメータが混在
        rule_options: dict[str, dict[str, object]] = {
            "require-qualified-third-party": {"root-packages": ["myapp"], "unknown": "x"}
        }

        # Act
        with caplog.at_level(logging.WARNING, logger="paladin.rule.rule_set_factory"):
            rule_set = RuleSetFactory().create(rule_options=rule_options)

        # Assert1: 警告が出力されること
        assert any("unknown" in record.message for record in caplog.records)

        # Assert2: root_packages が正しく適用されていること
        source_file = _make_source_file_for_import("from myapp.foo import bar\n")
        result = rule_set.run(SourceFiles(files=(source_file,)))
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_既知ルールIDと既知パラメータのみの場合警告が出ないこと(
        self, caplog: pytest.LogCaptureFixture
    ):
        # Arrange: 正常な設定
        rule_options = {"require-qualified-third-party": {"root-packages": ["myapp"]}}

        # Act
        with caplog.at_level(logging.WARNING, logger="paladin.rule.rule_set_factory"):
            RuleSetFactory().create(rule_options=rule_options)

        # Assert: 警告なし
        assert len(caplog.records) == 0

    def test_create_正常系_project_name指定時にデフォルトroot_packagesがproject_nameとtestsになること(
        self,
    ):
        # Arrange: project_name = "myapp" → デフォルト root_packages = ("myapp", "tests")
        rule_set = RuleSetFactory().create(project_name="myapp")
        source_file = _make_source_file_for_import("from myapp.foo import bar\n")

        # Act: myapp からのインポートは root_packages に含まれるため違反なし
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_project_name指定時にtestsもデフォルトで内部パッケージになること(
        self,
    ):
        # Arrange: project_name = "myapp" → tests も root_packages に含まれる
        rule_set = RuleSetFactory().create(project_name="myapp")
        source_file = _make_source_file_for_import("from tests.foo import bar\n")

        # Act
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert: tests も root_packages に含まれるため違反なし
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_project_nameがNoneの場合testsのみがデフォルトroot_packagesになること(
        self,
    ):
        # Arrange: project_name = None → デフォルト root_packages = ("tests",)
        rule_set = RuleSetFactory().create(project_name=None)
        source_file = _make_source_file_for_import("from tests.foo import bar\n")

        # Act
        result = rule_set.run(SourceFiles(files=(source_file,)))

        # Assert: tests は含まれるため違反なし
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

    def test_create_正常系_rule_optionsのroot_packagesがproject_nameより優先されること(
        self,
    ):
        # Arrange: rule_options で root-packages を明示指定 → project_name は無視される
        rule_options = {"require-qualified-third-party": {"root-packages": ["explicit_pkg"]}}
        rule_set = RuleSetFactory().create(rule_options=rule_options, project_name="myapp")

        # explicit_pkg からのインポートは違反なし
        source_file = _make_source_file_for_import("from explicit_pkg.foo import bar\n")
        result = rule_set.run(SourceFiles(files=(source_file,)))
        rqtp_violations = [v for v in result.items if v.rule_id == "require-qualified-third-party"]
        assert len(rqtp_violations) == 0

        # myapp からのインポートは rule_options で上書きされたため違反あり
        source_file2 = _make_source_file_for_import("from myapp.foo import bar\n")
        result2 = rule_set.run(SourceFiles(files=(source_file2,)))
        rqtp_violations2 = [
            v for v in result2.items if v.rule_id == "require-qualified-third-party"
        ]
        assert len(rqtp_violations2) == 1

    def test_create_正常系_project_name未指定の場合もデフォルト引数で動作すること(self):
        # Arrange / Act: project_name を指定しない（デフォルト引数 None）
        result = RuleSetFactory().create()

        # Assert: インスタンスが返ること
        assert isinstance(result, RuleSet)

    def test_create_正常系_no_direct_internal_importルールが登録されていること(self):
        result = RuleSetFactory().create()
        assert "no-direct-internal-import" in result.rule_ids

    def test_create_正常系_全ルールが登録されていること_5ルール(self):
        result = RuleSetFactory().create()
        rule_ids = result.rule_ids
        assert "require-all-export" in rule_ids
        assert "no-relative-import" in rule_ids
        assert "no-local-import" in rule_ids
        assert "require-qualified-third-party" in rule_ids
        assert "no-direct-internal-import" in rule_ids
