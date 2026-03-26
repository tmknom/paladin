"""ViewパッケージのComposition Root

具象クラスへの依存を隠蔽し、Viewパッケージの生成ロジックを一元化する。
"""

from paladin.foundation.log import log
from paladin.rule import RuleSetFactory
from paladin.view.formatter import ViewFormatterFactory
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
        rule_set = RuleSetFactory().create()
        formatter = ViewFormatterFactory()
        return ViewOrchestrator(rule_set=rule_set, formatter=formatter)
