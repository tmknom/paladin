"""Rule 層の Composition Root。

ルールの追加・削除はこのファイルで一元管理する。
新しいルールを実装した場合は `RuleSetFactory.create` の `rules` または `multi_file_rules` に追加すること。
逆に、ここに登録されていないルールは静的解析の実行対象にならない。
"""

from typing import cast

from paladin.rule.max_class_length import MaxClassLengthRule
from paladin.rule.max_file_length import MaxFileLengthRule
from paladin.rule.max_method_length import MaxMethodLengthRule
from paladin.rule.no_cross_package_import import NoCrossPackageImportRule
from paladin.rule.no_cross_package_reexport import NoCrossPackageReexportRule
from paladin.rule.no_deep_nesting import NoDeepNestingRule
from paladin.rule.no_direct_internal_import import NoDirectInternalImportRule
from paladin.rule.no_error_message_test import NoErrorMessageTestRule
from paladin.rule.no_frozen_instance_test import NoFrozenInstanceTestRule
from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.no_mock_usage import NoMockUsageRule
from paladin.rule.no_nested_test_class import NoNestedTestClassRule
from paladin.rule.no_non_init_all import NoNonInitAllRule
from paladin.rule.no_relative_import import NoRelativeImportRule
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


class RuleSetFactory:
    """プロダクション用のデフォルトルール一式を組み立てるファクトリー"""

    def create(self, rule_options: dict[str, dict[str, object]] | None = None) -> RuleSet:
        """プロダクションで使うデフォルトのルール一式を返す

        `rule_options` が `None` の場合は全ルールにデフォルト値を適用する。

        Constraints:
            - `rule_options` のキーはルールID文字列、値は各ルールのオプション辞書。
            - オプション値が期待する型と一致しない場合はデフォルト値にフォールバックする（例外を出さない）。
              例: `max-lines` に文字列が渡されても `int` のデフォルト値を使用し処理を継続する。
        """
        third_party_allow_dirs = self._extract_allow_dirs(rule_options, "no-third-party-import")
        cross_package_allow_dirs = self._extract_allow_dirs(rule_options, "no-cross-package-import")
        max_lines, max_test_lines = self._extract_length_options(
            rule_options, "max-method-length", 50, 100
        )
        class_max_lines, class_max_test_lines = self._extract_length_options(
            rule_options, "max-class-length", 200, 400
        )
        file_max_lines, file_max_test_lines = self._extract_length_options(
            rule_options, "max-file-length", 300, 500
        )
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
                NoThirdPartyImportRule(allow_dirs=third_party_allow_dirs),
                NoCrossPackageImportRule(allow_dirs=cross_package_allow_dirs),
                MaxMethodLengthRule(max_lines=max_lines, max_test_lines=max_test_lines),
                MaxClassLengthRule(max_lines=class_max_lines, max_test_lines=class_max_test_lines),
                MaxFileLengthRule(max_lines=file_max_lines, max_test_lines=file_max_test_lines),
                RequireDocstringRule(),
                RequireEmptyTestInitRule(),
                RequireAaaCommentRule(),
                NoErrorMessageTestRule(),
                NoFrozenInstanceTestRule(),
                NoNestedTestClassRule(),
            ),
            multi_file_rules=(
                NoDirectInternalImportRule(),
                NoUnusedExportRule(),
                NoTestingTestCodeRule(),
            ),
            unused_ignore_rule=UnusedIgnoreRule(),
        )

    def _extract_allow_dirs(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
    ) -> tuple[str, ...]:
        """rule_options から指定ルールの allow-dirs を取り出す

        `rule_options` が `None` の場合は空タプルを返す。
        `allow-dirs` の値が `list` でない場合も空タプルを返す（設定値が期待する型でない場合に安全に無視する）。
        """
        if rule_options is None:
            return ()
        opts = rule_options.get(rule_id, {})
        raw: object = opts.get("allow-dirs", [])
        if not isinstance(raw, list):
            return ()
        return tuple(str(item) for item in cast(list[object], raw))

    def _extract_length_options(
        self,
        rule_options: dict[str, dict[str, object]] | None,
        rule_id: str,
        default_max: int,
        default_test: int,
    ) -> tuple[int, int]:
        """rule_options から指定ルールの max-lines / max-test-lines を取り出す

        `rule_options` が `None` の場合は `default_max` / `default_test` を返す。
        値が存在しても `int` でない場合も同様に `default_max` / `default_test` を返す。
        """
        if rule_options is None:
            return default_max, default_test
        opts = rule_options.get(rule_id, {})
        raw_max = opts.get("max-lines", default_max)
        raw_test = opts.get("max-test-lines", default_test)
        max_lines = raw_max if isinstance(raw_max, int) else default_max
        max_test_lines = raw_test if isinstance(raw_test, int) else default_test
        return max_lines, max_test_lines
