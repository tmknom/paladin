"""CheckOrchestratorとその依存を一括生成するファクトリー

具象クラスへの依存を隠蔽し、Check層の生成ロジックを一元化する。

依存グラフ:
    CheckOrchestratorProvider
    ├── TextFileSystemReader
    ├── AstParser(reader=TextFileSystemReader)
    ├── FileCollector
    ├── RequireAllExportRule
    ├── NoRelativeImportRule
    ├── NoLocalImportRule
    ├── RequireQualifiedThirdPartyRule(root_packages=("paladin",))
    ├── RuleRunner(rules=(RequireAllExportRule, NoRelativeImportRule, NoLocalImportRule, RequireQualifiedThirdPartyRule))
    ├── CheckReportFormatter
    └── CheckOrchestrator(collector=FileCollector, parser=AstParser, runner=RuleRunner, formatter=CheckReportFormatter)
"""

from paladin.check.collector import FileCollector
from paladin.check.formatter import CheckReportFormatter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.parser import AstParser
from paladin.check.rule.no_local_import import NoLocalImportRule
from paladin.check.rule.no_relative_import import NoRelativeImportRule
from paladin.check.rule.require_all_export import RequireAllExportRule
from paladin.check.rule.require_qualified_third_party import RequireQualifiedThirdPartyRule
from paladin.check.rule.runner import RuleRunner
from paladin.foundation.fs.text import TextFileSystemReader
from paladin.foundation.log import log


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
        require_all_export_rule = RequireAllExportRule()
        no_relative_import_rule = NoRelativeImportRule()
        no_local_import_rule = NoLocalImportRule()
        require_qualified_third_party_rule = RequireQualifiedThirdPartyRule(
            root_packages=("paladin",)
        )
        runner = RuleRunner(
            rules=(
                require_all_export_rule,
                no_relative_import_rule,
                no_local_import_rule,
                require_qualified_third_party_rule,
            )
        )
        return CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            runner=runner,
            formatter=CheckReportFormatter(),
        )
