"""プロダクション用ルール群の構築ファクトリー

RuleSet のインスタンス生成と具象ルールの組み立てを担う。
"""

from paladin.rule.no_cross_package_reexport import NoCrossPackageReexportRule
from paladin.rule.no_direct_internal_import import NoDirectInternalImportRule
from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.no_non_init_all import NoNonInitAllRule
from paladin.rule.no_relative_import import NoRelativeImportRule
from paladin.rule.require_all_export import RequireAllExportRule
from paladin.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.rule.rule_set import RuleSet


class RuleSetFactory:
    """プロダクション用のデフォルトルール一式を組み立てるファクトリー"""

    def create(self) -> RuleSet:
        """プロダクションで使うデフォルトのルール一式を返す"""
        return RuleSet(
            rules=(
                RequireAllExportRule(),
                NoRelativeImportRule(),
                NoLocalImportRule(),
                RequireQualifiedThirdPartyRule(),
                NoNonInitAllRule(),
                NoCrossPackageReexportRule(),
            ),
            multi_file_rules=(NoDirectInternalImportRule(),),
        )
