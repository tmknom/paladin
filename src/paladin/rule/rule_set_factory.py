"""Rule 層の Composition Root。"""

from dataclasses import dataclass
from typing import cast

from paladin.rule.max_class_length import MaxClassLengthRule
from paladin.rule.max_file_length import MaxFileLengthRule
from paladin.rule.max_function_parameter import MaxFunctionParameterRule
from paladin.rule.max_method_length import MaxMethodLengthRule
from paladin.rule.no_cross_package_import import NoCrossPackageImportRule
from paladin.rule.no_cross_package_reexport import NoCrossPackageReexportRule
from paladin.rule.no_deep_nesting import NoDeepNestingRule
from paladin.rule.no_direct_internal_import import NoDirectInternalImportRule
from paladin.rule.no_error_message_test import NoErrorMessageTestRule
from paladin.rule.no_frozen_instance_test import NoFrozenInstanceTestRule
from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.no_mock_usage import NoMockUsageRule
from paladin.rule.no_module_level_function import NoModuleLevelFunctionRule
from paladin.rule.no_nested_test_class import NoNestedTestClassRule
from paladin.rule.no_non_init_all import NoNonInitAllRule
from paladin.rule.no_private_attr_in_test import NoPrivateAttrInTestRule
from paladin.rule.no_relative_import import NoRelativeImportRule
from paladin.rule.no_test_method_docstring import NoTestMethodDocstringRule
from paladin.rule.no_testing_test_code import NoTestingTestCodeRule
from paladin.rule.no_third_party_import import NoThirdPartyImportRule
from paladin.rule.no_unused_export import NoUnusedExportRule
from paladin.rule.require_aaa_comment import RequireAaaCommentRule
from paladin.rule.require_all_export import RequireAllExportRule
from paladin.rule.require_docstring import RequireDocstringRule
from paladin.rule.require_empty_test_init import RequireEmptyTestInitRule
from paladin.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.rule.rule_set import RuleSet
from paladin.rule.unused_ignore import UnusedIgnoreRule


@dataclass(frozen=True)
class LengthOptions:
    """length 系 3 ルールの max-lines / max-test-lines を集約する。"""

    method_max: int
    method_test: int
    class_max: int
    class_test: int
    file_max: int
    file_test: int


@dataclass(frozen=True)
class RuleOptions:
    """各ルールへ渡すオプション値を集約する dataclass。"""

    third_party_allow_dirs: tuple[str, ...]
    third_party_allow_files: tuple[str, ...]
    cross_package_allow_dirs: tuple[str, ...]
    nmlf_allow_decorators: tuple[str, ...]
    nmlf_allow_files: tuple[str, ...]
    mfp_max: int
    mfp_allow_decorators: tuple[str, ...]
    max_lines: int
    max_test_lines: int
    class_max_lines: int
    class_max_test_lines: int
    file_max_lines: int
    file_max_test_lines: int


class RuleSetFactory:
    """静的解析で使用するルール一式を組み立てる Factory。

    `rule_options` を受け取り、各ルールに渡すオプション値を抽出・型変換してから
    `RuleSet` を返す。主要メソッドは `create()`。
    """

    _DEFAULT_ALLOW_DECORATORS: tuple[str, ...] = (
        "pytest.fixture",
        "fixture",
        "app.command",
        "app.callback",
    )

    _LENGTH_DEFAULTS: tuple[tuple[str, int, int], ...] = (
        ("max-method-length", 50, 100),
        ("max-class-length", 300, 600),
        ("max-file-length", 400, 800),
    )

    def create(self, rule_options: dict[str, dict[str, object]] | None = None) -> RuleSet:
        """`rule_options` が `None` の場合は全ルールにデフォルト値を適用する。

        Constraints:
            - `rule_options` のキーはルールID文字列、値は各ルールのオプション辞書。
            - オプション値が期待する型と一致しない場合はデフォルト値にフォールバックする（例外を出さない）。
              例: `max-lines` に文字列が渡されても `int` のデフォルト値を使用し処理を継続する。

        Returns:
            全ルールを格納した `RuleSet` インスタンス。
        """
        opts = self._resolve_options(rule_options)
        return RuleSet(
            rules=(
                RequireAllExportRule(),
                NoRelativeImportRule(),
                NoLocalImportRule(),
                RequireQualifiedThirdPartyRule(),
                NoNonInitAllRule(),
                NoCrossPackageReexportRule(),
                NoMockUsageRule(),
                NoDeepNestingRule(),
                NoThirdPartyImportRule(
                    allow_dirs=opts.third_party_allow_dirs,
                    allow_files=opts.third_party_allow_files,
                ),
                NoCrossPackageImportRule(allow_dirs=opts.cross_package_allow_dirs),
                MaxMethodLengthRule(max_lines=opts.max_lines, max_test_lines=opts.max_test_lines),
                MaxClassLengthRule(
                    max_lines=opts.class_max_lines, max_test_lines=opts.class_max_test_lines
                ),
                MaxFileLengthRule(
                    max_lines=opts.file_max_lines, max_test_lines=opts.file_max_test_lines
                ),
                RequireDocstringRule(),
                RequireEmptyTestInitRule(),
                RequireAaaCommentRule(),
                NoErrorMessageTestRule(),
                NoFrozenInstanceTestRule(),
                NoNestedTestClassRule(),
                NoPrivateAttrInTestRule(),
                NoTestMethodDocstringRule(),
                NoModuleLevelFunctionRule(
                    allow_decorators=opts.nmlf_allow_decorators,
                    allow_files=opts.nmlf_allow_files,
                ),
                MaxFunctionParameterRule(
                    max_parameters=opts.mfp_max, allow_decorators=opts.mfp_allow_decorators
                ),
            ),
            multi_file_rules=(
                NoDirectInternalImportRule(),
                NoUnusedExportRule(),
                NoTestingTestCodeRule(),
            ),
            unused_ignore_rule=UnusedIgnoreRule(),
        )

    def _resolve_options(self, rule_options: dict[str, dict[str, object]] | None) -> RuleOptions:
        """設定辞書を解析して `RuleOptions` に集約する。各 `_extract_*` ヘルパーに委譲し、型不一致はデフォルト値へフォールバックする。"""
        third_party_allow_dirs = self._extract_allow_dirs(rule_options, "no-third-party-import")
        third_party_allow_files = self._extract_allow_files(
            rule_options,
            "no-third-party-import",  # [tool.paladin.rule.no-third-party-import].allow-files
        )
        cross_package_allow_dirs = self._extract_allow_dirs(rule_options, "no-cross-package-import")
        nmlf_allow_decorators = self._extract_allow_decorators(
            rule_options,
            "no-module-level-function",  # [tool.paladin.rule.no-module-level-function].allow-decorators
        )
        nmlf_allow_files = self._extract_allow_files(
            rule_options,
            "no-module-level-function",  # [tool.paladin.rule.no-module-level-function].allow-files
        )
        mfp_max = self._extract_max_parameters(
            rule_options,
            "max-function-parameter",
            4,  # [tool.paladin.rule.max-function-parameter].max-parameters
        )
        mfp_allow_decorators = self._extract_allow_decorators(
            rule_options,
            "max-function-parameter",  # [tool.paladin.rule.max-function-parameter].allow-decorators
        )
        length = self._resolve_length_options(rule_options)
        return RuleOptions(
            third_party_allow_dirs=third_party_allow_dirs,
            third_party_allow_files=third_party_allow_files,
            cross_package_allow_dirs=cross_package_allow_dirs,
            nmlf_allow_decorators=nmlf_allow_decorators,
            nmlf_allow_files=nmlf_allow_files,
            mfp_max=mfp_max,
            mfp_allow_decorators=mfp_allow_decorators,
            max_lines=length.method_max,
            max_test_lines=length.method_test,
            class_max_lines=length.class_max,
            class_max_test_lines=length.class_test,
            file_max_lines=length.file_max,
            file_max_test_lines=length.file_test,
        )

    def _extract_max_parameters(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
        default: int,
    ) -> int:
        """指定ルールの max-parameters を取り出す。

        Constraints:
            - `rule_options` が `None`、または指定ルールIDのキーが存在しない場合も `default` にフォールバックする。
            - 値が `int` 以外の型の場合は `default` にフォールバックする（型安全な無視）。
              例外を出さずにデフォルト値を使うことで、設定値の型不一致が解析実行を妨げないようにする。
        """
        if rule_options is None:
            return default
        opts = rule_options.get(rule_id, {})
        raw = opts.get("max-parameters", default)
        return raw if isinstance(raw, int) else default

    def _extract_allow_decorators(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
    ) -> tuple[str, ...]:
        """指定ルールの allow-decorators を取り出す。設定が存在しない場合はデフォルト値を使用する。

        Constraints:
            - `rule_options` が `None`、または `allow-decorators` の値が `list` 以外の型の場合はデフォルト値を返す（型安全な無視）。
              例外を出さずにデフォルト値にフォールバックすることで、設定値の型不一致を安全に読み飛ばす。
        """
        if rule_options is None:
            return self._DEFAULT_ALLOW_DECORATORS
        opts = rule_options.get(rule_id, {})
        raw: object = opts.get("allow-decorators", list(self._DEFAULT_ALLOW_DECORATORS))
        if not isinstance(raw, list):
            return self._DEFAULT_ALLOW_DECORATORS
        return tuple(str(item) for item in cast(list[object], raw))

    def _extract_allow_dirs(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
    ) -> tuple[str, ...]:
        """指定ルールの allow-dirs を取り出す。設定が存在しない場合はデフォルト値（空タプル）を使用する。

        Constraints:
            - `rule_options` が `None`、または `allow-dirs` の値が `list` 以外の型の場合は空タプルを返す（型安全な無視）。
              例外を出さずに空タプルにフォールバックすることで、設定値の型不一致を安全に読み飛ばす。
        """
        if rule_options is None:
            return ()
        opts = rule_options.get(rule_id, {})
        raw: object = opts.get("allow-dirs", [])
        if not isinstance(raw, list):
            return ()
        return tuple(str(item) for item in cast(list[object], raw))

    def _extract_allow_files(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
    ) -> tuple[str, ...]:
        """指定ルールの allow-files を取り出す。設定が存在しない場合はデフォルト値（空タプル）を使用する。

        Constraints:
            - `rule_options` が `None`、または `allow-files` の値が `list` 以外の型の場合は空タプルを返す（型安全な無視）。
              例外を出さずに空タプルにフォールバックすることで、設定値の型不一致を安全に読み飛ばす。
        """
        if rule_options is None:
            return ()
        opts = rule_options.get(rule_id, {})
        raw: object = opts.get("allow-files", [])
        if not isinstance(raw, list):
            return ()
        return tuple(str(item) for item in cast(list[object], raw))

    def _resolve_length_options(
        self, rule_options: dict[str, dict[str, object]] | None
    ) -> LengthOptions:
        """Length 系 3 ルールの設定値をまとめて取り出す。"""
        method = self._extract_length_options(rule_options, *self._LENGTH_DEFAULTS[0])
        klass = self._extract_length_options(rule_options, *self._LENGTH_DEFAULTS[1])
        file = self._extract_length_options(rule_options, *self._LENGTH_DEFAULTS[2])
        return LengthOptions(
            method_max=method[0],
            method_test=method[1],
            class_max=klass[0],
            class_test=klass[1],
            file_max=file[0],
            file_test=file[1],
        )

    def _extract_length_options(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
        default_max: int,
        default_test: int,
    ) -> tuple[int, int]:
        """指定ルールの max-lines / max-test-lines を取り出す。

        Constraints:
            - `rule_options` が `None`、または値が `int` 以外の型の場合は `default_max` / `default_test` にフォールバックする（型安全な無視）。
              例外を出さずにデフォルト値を使うことで、設定値の型不一致が解析実行を妨げないようにする。
        """
        if rule_options is None:
            return default_max, default_test
        opts = rule_options.get(rule_id, {})
        raw_max = opts.get("max-lines", default_max)
        raw_test = opts.get("max-test-lines", default_test)
        max_lines = raw_max if isinstance(raw_max, int) else default_max
        max_test_lines = raw_test if isinstance(raw_test, int) else default_test
        return max_lines, max_test_lines
