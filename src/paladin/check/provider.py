"""Check層の Composition Root

具象クラスへの依存を隠蔽し、Check層の生成ロジックを一元化する。
"""

from collections.abc import Mapping

from paladin.check.collector import FileCollector, PathExcluder
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import ViolationFilter
from paladin.check.orchestrator import CheckOrchestrator
from paladin.check.override import OverrideResolver
from paladin.check.parser import AstParser
from paladin.check.rule_filter import RuleFilter
from paladin.foundation.fs.text import TextFileSystemReader
from paladin.foundation.log import log
from paladin.lint import RuleSet


class CheckOrchestratorProvider:
    """CheckOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    @log
    def provide(
        self,
        rule_options: Mapping[str, Mapping[str, object]] | None = None,
        project_name: str | None = None,
    ) -> CheckOrchestrator:
        """CheckOrchestratorを構築

        Args:
            rule_options: ルール個別設定。None の場合はデフォルト値を使用する
            project_name: pyproject.toml の [project] name から取得した正規化済みプロジェクト名

        Returns:
            設定済みのCheckOrchestrator
        """
        reader = TextFileSystemReader()
        parser = AstParser(reader=reader)
        rule_set = RuleSet.default(rule_options=rule_options, project_name=project_name)
        return CheckOrchestrator(
            collector=FileCollector(),
            parser=parser,
            rule_set=rule_set,
            formatter=CheckFormatterFactory(),
            violation_filter=ViolationFilter(),
            rule_filter=RuleFilter(),
            path_excluder=PathExcluder(),
            override_resolver=OverrideResolver(),
        )
