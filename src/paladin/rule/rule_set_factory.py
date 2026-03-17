"""プロダクション用ルール群の構築ファクトリー

RuleSet のインスタンス生成と具象ルールの組み立てを担う。
"""

import logging
from collections.abc import Mapping

from paladin.rule.no_direct_internal_import import NoDirectInternalImportRule
from paladin.rule.no_local_import import NoLocalImportRule
from paladin.rule.no_relative_import import NoRelativeImportRule
from paladin.rule.require_all_export import RequireAllExportRule
from paladin.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.rule.rule_set import RuleSet

logger = logging.getLogger(__name__)

_KNOWN_RULE_IDS: frozenset[str] = frozenset(
    {
        "require-qualified-third-party",
        "require-all-export",
        "no-relative-import",
        "no-local-import",
        "no-direct-internal-import",
    }
)


class RuleSetFactory:
    """プロダクション用のデフォルトルール一式を組み立てるファクトリー"""

    def create(
        self,
        rule_options: Mapping[str, Mapping[str, object]] | None = None,
        project_name: str | None = None,
    ) -> RuleSet:
        """プロダクションで使うデフォルトのルール一式を返す

        Args:
            rule_options: ルール個別設定。キーはルール ID (kebab-case)、値はそのルールのパラメータ dict
            project_name: pyproject.toml の [project] name から取得した正規化済みプロジェクト名
        """
        options = rule_options or {}

        # 未知ルール ID の警告
        for rule_id in options:
            if rule_id not in _KNOWN_RULE_IDS:
                logger.warning("Unknown rule ID in [tool.paladin.rule]: %s", rule_id)

        # require-qualified-third-party の root_packages を解決
        root_packages = self._resolve_root_packages(options, project_name=project_name)

        return RuleSet(
            rules=(
                RequireAllExportRule(),
                NoRelativeImportRule(),
                NoLocalImportRule(),
                RequireQualifiedThirdPartyRule(root_packages=root_packages),
            ),
            multi_file_rules=(NoDirectInternalImportRule(root_packages=root_packages),),
        )

    def _resolve_root_packages(
        self,
        options: Mapping[str, Mapping[str, object]],
        project_name: str | None = None,
    ) -> tuple[str, ...]:
        """require-qualified-third-party の root_packages を解決する"""
        _known_params: frozenset[str] = frozenset({"root-packages"})
        rule_id = "require-qualified-third-party"
        entry = options.get(rule_id)
        default = (project_name, "tests") if project_name is not None else ("tests",)

        if entry is None:
            return default

        # 未知パラメータの警告
        for param in entry:
            if param not in _known_params:
                logger.warning('Unknown parameter in [tool.paladin.rule."%s"]: %s', rule_id, param)

        # kebab-case -> snake_case 変換して root_packages を取得
        snake_entry = {k.replace("-", "_"): v for k, v in entry.items()}
        raw = snake_entry.get("root_packages")
        if raw is None:
            return default
        return tuple(str(p) for p in raw)  # type: ignore[arg-type]
