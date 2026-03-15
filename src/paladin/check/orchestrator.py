"""Check層の中核

対象列挙と AST 生成の処理フロー全体を制御し、結果を返す。
"""

from pathlib import Path

from paladin.check.collector import FileCollector, PathExcluder
from paladin.check.context import CheckContext
from paladin.check.formatter import CheckFormatterFactory
from paladin.check.ignore import (
    ConfigIgnoreResolver,
    FileIgnoreDirective,
    FileIgnoreParser,
    LineIgnoreParser,
    ViolationFilter,
)
from paladin.check.parser import AstParser
from paladin.check.result import CheckReport, CheckResult
from paladin.check.rule_filter import RuleFilter
from paladin.foundation.log import log
from paladin.lint import RuleSet


class CheckOrchestrator:
    """対象列挙と AST 生成の処理フローを制御するオーケストレーター

    Flow:
        1. context.targets から解析対象パスを取得
        2. FileCollector で .py ファイルを列挙
        3. PathExcluder で context.exclude パターンを適用
        4. AstParser で各ファイルの AST を生成
        5. RuleSet でルールを適用し Violations を収集
        6. CheckReportFormatter で CheckReport に変換して返す

    Returns:
        CheckReport: フォーマット済みレポート文字列と終了コードを含む実行結果
    """

    def __init__(
        self,
        collector: FileCollector,
        parser: AstParser,
        rule_set: RuleSet,
        formatter: CheckFormatterFactory,
        violation_filter: ViolationFilter,
        rule_filter: RuleFilter,
        path_excluder: PathExcluder,
    ) -> None:
        """CheckOrchestratorを初期化

        Args:
            collector: ファイル列挙コレクター
            parser: ASTパーサー
            rule_set: ルール管理・実行
            formatter: レポートフォーマッター
            violation_filter: ignore フィルター
            rule_filter: ルール有効/無効フィルター
            path_excluder: exclude パターンによるファイル除外
        """
        self.collector = collector
        self.parser = parser
        self.rule_set = rule_set
        self.formatter = formatter
        self.violation_filter = violation_filter
        self.rule_filter = rule_filter
        self.path_excluder = path_excluder

    @log
    def orchestrate(self, context: CheckContext) -> CheckReport:
        """解析対象ファイルを列挙してAST生成し、ルール適用後にレポートを返す

        Args:
            context: Check処理の実行時コンテキスト

        Returns:
            Check処理のフォーマット済みレポート
        """
        target_files = self.collector.collect(context.targets)
        target_files = self.path_excluder.exclude(target_files, context.exclude)
        source_files = self.parser.parse_all(target_files)
        disabled_rule_ids = self.rule_filter.resolve_disabled_rules(
            context.rules, self.rule_set.rule_ids
        )
        violations = self.rule_set.run(source_files, disabled_rule_ids=disabled_rule_ids)
        file_paths = tuple(sf.file_path for sf in source_files)
        config_directives = ConfigIgnoreResolver().resolve(context.per_file_ignores, file_paths)
        comment_directives = FileIgnoreParser().parse_all(source_files)
        merged_directives = self._merge_directives(config_directives, comment_directives)
        line_directives = LineIgnoreParser().parse_all(source_files)
        violations = self.violation_filter.filter(
            violations, merged_directives, line_directives, context.ignore_rules
        )
        result = CheckResult(
            target_files=target_files, source_files=source_files, violations=violations
        )
        return self.formatter.format(result, context.format)

    def _merge_directives(
        self,
        config_directives: tuple[FileIgnoreDirective, ...],
        comment_directives: tuple[FileIgnoreDirective, ...],
    ) -> tuple[FileIgnoreDirective, ...]:
        """設定ファイル由来とコメント由来の FileIgnoreDirective を統合する

        同一ファイルに対して両方が存在する場合は ignored_rules の和集合とし、
        いずれかが ignore_all=True なら ignore_all=True とする。
        """
        merged: dict[Path, FileIgnoreDirective] = {}
        for directive in (*config_directives, *comment_directives):
            existing = merged.get(directive.file_path)
            if existing is None:
                merged[directive.file_path] = directive
            else:
                merged[directive.file_path] = FileIgnoreDirective(
                    file_path=directive.file_path,
                    ignore_all=existing.ignore_all or directive.ignore_all,
                    ignored_rules=existing.ignored_rules | directive.ignored_rules,
                )
        return tuple(merged.values())
