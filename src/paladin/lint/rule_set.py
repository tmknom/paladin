"""ルール管理・実行

複数 Rule を束ねて管理し、実行・一覧・検索を提供する。
"""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from paladin.lint.no_direct_internal_import import NoDirectInternalImportRule
from paladin.lint.no_local_import import NoLocalImportRule
from paladin.lint.no_relative_import import NoRelativeImportRule
from paladin.lint.protocol import MultiFileRule, Rule
from paladin.lint.require_all_export import RequireAllExportRule
from paladin.lint.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.lint.types import RuleMeta, SourceFiles, Violation, Violations

logger = logging.getLogger(__name__)


class RuleSet:
    """複数 Rule を束ねて管理し、実行・一覧・検索を提供する"""

    _KNOWN_RULE_IDS: ClassVar[frozenset[str]] = frozenset(
        {
            "require-qualified-third-party",
            "require-all-export",
            "no-relative-import",
            "no-local-import",
            "no-direct-internal-import",
        }
    )
    _KNOWN_PARAMS: ClassVar[dict[str, frozenset[str]]] = {
        "require-qualified-third-party": frozenset({"root-packages"}),
    }

    def __init__(
        self,
        rules: tuple[Rule, ...],
        multi_file_rules: tuple[MultiFileRule, ...] = (),
    ) -> None:
        """RuleSetを初期化"""
        self._rules = rules
        self._multi_file_rules = multi_file_rules

    @classmethod
    def default(
        cls,
        rule_options: Mapping[str, Mapping[str, object]] | None = None,
        project_name: str | None = None,
    ) -> "RuleSet":
        """プロダクションで使うデフォルトのルール一式を返す

        Args:
            rule_options: ルール個別設定。キーはルール ID (kebab-case)、値はそのルールのパラメータ dict
            project_name: pyproject.toml の [project] name から取得した正規化済みプロジェクト名
        """
        options = rule_options or {}

        # 未知ルール ID の警告
        for rule_id in options:
            if rule_id not in cls._KNOWN_RULE_IDS:
                logger.warning("Unknown rule ID in [tool.paladin.rule]: %s", rule_id)

        # require-qualified-third-party の root_packages を解決
        root_packages = cls._resolve_root_packages(options, project_name=project_name)

        return cls(
            rules=(
                RequireAllExportRule(),
                NoRelativeImportRule(),
                NoLocalImportRule(),
                RequireQualifiedThirdPartyRule(root_packages=root_packages),
            ),
            multi_file_rules=(NoDirectInternalImportRule(root_packages=root_packages),),
        )

    @classmethod
    def _resolve_root_packages(
        cls,
        options: Mapping[str, Mapping[str, object]],
        project_name: str | None = None,
    ) -> tuple[str, ...]:
        """require-qualified-third-party の root_packages を解決する"""
        rule_id = "require-qualified-third-party"
        known_params = cls._KNOWN_PARAMS.get(rule_id, frozenset())
        entry = options.get(rule_id)
        default = (project_name, "tests") if project_name is not None else ("tests",)

        if entry is None:
            return default

        # 未知パラメータの警告
        for param in entry:
            if param not in known_params:
                logger.warning('Unknown parameter in [tool.paladin.rule."%s"]: %s', rule_id, param)

        # kebab-case -> snake_case 変換して root_packages を取得
        snake_entry = {k.replace("-", "_"): v for k, v in entry.items()}
        raw = snake_entry.get("root_packages")
        if raw is None:
            return default
        return tuple(str(p) for p in raw)  # type: ignore[arg-type]

    @property
    def rule_ids(self) -> frozenset[str]:
        """登録されている全ルールの ID セットを返す"""
        single_ids = frozenset(rule.meta.rule_id for rule in self._rules)
        multi_ids = frozenset(rule.meta.rule_id for rule in self._multi_file_rules)
        return single_ids | multi_ids

    def run(
        self,
        source_files: SourceFiles,
        disabled_rule_ids: frozenset[str] = frozenset(),
        per_file_disabled: Mapping[Path, frozenset[str]] | None = None,
    ) -> Violations:
        """全ファイルに全ルールを適用し、違反を集約して返す

        Args:
            source_files: 検査対象のソースファイル群
            disabled_rule_ids: スキップするルール ID の frozenset
            per_file_disabled: ファイルパスごとの disabled_rule_ids。指定されたファイルはこちらを優先使用する
        """
        violations: list[Violation] = []
        for source_file in source_files:
            effective_disabled = (
                per_file_disabled.get(source_file.file_path, disabled_rule_ids)
                if per_file_disabled is not None
                else disabled_rule_ids
            )
            for rule in self._rules:
                if rule.meta.rule_id in effective_disabled:
                    continue
                violations.extend(rule.check(source_file))
        for multi_rule in self._multi_file_rules:
            if multi_rule.meta.rule_id in disabled_rule_ids:
                continue
            violations.extend(multi_rule.check(source_files))
        return Violations(items=tuple(violations))

    def list_rules(self) -> tuple[RuleMeta, ...]:
        """登録済みルールのメタ情報一覧を返す"""
        return tuple(rule.meta for rule in self._rules) + tuple(
            rule.meta for rule in self._multi_file_rules
        )

    def find_rule(self, rule_id: str) -> RuleMeta | None:
        """指定した rule_id に一致する RuleMeta を返す。存在しない場合は None を返す"""
        for rule in self._rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        for rule in self._multi_file_rules:
            if rule.meta.rule_id == rule_id:
                return rule.meta
        return None
