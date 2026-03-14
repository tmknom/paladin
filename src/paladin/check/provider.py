"""Check層の Composition Root

具象クラスへの依存を隠蔽し、Check層の生成ロジックを一元化する。
"""

from paladin.check.collector import FileCollector
from paladin.check.config import ProjectConfigLoader, RuleFilter
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.path import PathExcluder, TargetResolver
from paladin.foundation.fs.text import TextFileSystemReader
from paladin.foundation.log import log
from paladin.lint import (
    NoLocalImportRule,
    NoRelativeImportRule,
    RequireAllExportRule,
    RequireQualifiedThirdPartyRule,
    RuleRunner,
)


class CheckOrchestratorProvider:
    """CheckOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(self) -> CheckOrchestrator:
        """CheckOrchestratorを構築

        Returns:
            設定済みのCheckOrchestrator
        """
        reader = TextFileSystemReader()
        parser = AstParser(reader=reader)
        runner = self._create_runner()
        config_loader = ProjectConfigLoader(reader=TextFileSystemReader())
        return CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            config_loader=config_loader,
            rule_filter=RuleFilter(),
            target_resolver=TargetResolver(),
            path_excluder=PathExcluder(),
        )

    def _create_runner(self) -> RuleRunner:
        require_all_export_rule = RequireAllExportRule()
        no_relative_import_rule = NoRelativeImportRule()
        no_local_import_rule = NoLocalImportRule()
        require_qualified_third_party_rule = RequireQualifiedThirdPartyRule(
            root_packages=("paladin", "tests")
        )
        return RuleRunner(
            rules=(
                require_all_export_rule,
                no_relative_import_rule,
                no_local_import_rule,
                require_qualified_third_party_rule,
            )
        )
