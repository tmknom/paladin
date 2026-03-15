"""View層の Composition Root

具象クラスへの依存を隠蔽し、View層の生成ロジックを一元化する。
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
from paladin.view.formatter import ViewFormatter
from paladin.view.orchestrator import ViewOrchestrator


class ViewOrchestratorProvider:
    """ViewOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(self) -> ViewOrchestrator:
        """ViewOrchestratorを構築する

        Returns:
            設定済みの ViewOrchestrator
        """
        registry = RuleRegistry(rules=self._create_rules())
        formatter = ViewFormatter()
        return ViewOrchestrator(registry=registry, formatter=formatter)

    def _create_rules(self) -> tuple[Rule, ...]:
        return (
            RequireAllExportRule(),
            NoRelativeImportRule(),
            NoLocalImportRule(),
            RequireQualifiedThirdPartyRule(root_packages=("paladin", "tests")),
        )
