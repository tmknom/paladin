"""RulesOrchestratorProviderの実装"""

from paladin.check.rule.no_local_import import NoLocalImportRule
from paladin.check.rule.no_relative_import import NoRelativeImportRule
from paladin.check.rule.protocol import Rule
from paladin.check.rule.registry import RuleRegistry
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.foundation.log import log
from paladin.rules.detail_formatter import RulesDetailFormatter
from paladin.rules.formatter import RulesFormatter
from paladin.rules.orchestrator import RulesOrchestrator


class RulesOrchestratorProvider:
    """RulesOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(self) -> RulesOrchestrator:
        """RulesOrchestratorを構築する

        Returns:
            設定済みの RulesOrchestrator
        """
        registry = RuleRegistry(rules=self._create_rules())
        formatter = RulesFormatter()
        detail_formatter = RulesDetailFormatter()
        return RulesOrchestrator(
            registry=registry, formatter=formatter, detail_formatter=detail_formatter
        )

    def _create_rules(self) -> tuple[Rule, ...]:
        return (
            RequireAllExportRule(),
            NoRelativeImportRule(),
            NoLocalImportRule(),
            RequireQualifiedThirdPartyRule(root_packages=("paladin",)),
        )
