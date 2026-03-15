"""List層の Composition Root

具象クラスへの依存を隠蔽し、List層の生成ロジックを一元化する。
"""

from paladin.foundation.log import log
from paladin.lint import (
    NoLocalImportRule,
    NoRelativeImportRule,
    RequireAllExportRule,
    RequireQualifiedThirdPartyRule,
    Rule,
    RuleSet,
)
from paladin.list.formatter import ListFormatter
from paladin.list.orchestrator import ListOrchestrator


class ListOrchestratorProvider:
    """ListOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(self) -> ListOrchestrator:
        """ListOrchestratorを構築する

        Returns:
            設定済みの ListOrchestrator
        """
        rule_set = RuleSet(rules=self._create_rules())
        formatter = ListFormatter()
        return ListOrchestrator(rule_set=rule_set, formatter=formatter)

    def _create_rules(self) -> tuple[Rule, ...]:
        return (
            RequireAllExportRule(),
            NoRelativeImportRule(),
            NoLocalImportRule(),
            RequireQualifiedThirdPartyRule(root_packages=("paladin", "tests")),
        )
