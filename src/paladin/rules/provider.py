"""Rules層の Composition Root

具象クラスへの依存を隠蔽し、Rules層の生成ロジックを一元化する。
"""

from paladin.foundation.log import log
from paladin.lint import (
    NoLocalImportRule,
    NoRelativeImportRule,
    RequireAllExportRule,
    RequireQualifiedThirdPartyRule,
    Rule,
    RuleRegistry,
)
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
