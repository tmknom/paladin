"""Ignore パッケージのエントリーポイント。

設定・コメント双方のディレクティブを統合して違反フィルタリングまで完結させる層。
"""

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.check.ignore.filter import ViolationFilter
from paladin.check.ignore.parser import FileIgnoreParser, LineIgnoreParser
from paladin.check.ignore.resolver import ConfigIgnoreResolver
from paladin.rule import PerFileIgnoreEntry, SourceFiles, Violations


class IgnoreProcessor:
    """Ignore ディレクティブの解析・統合・フィルタリングを一括実行するファサード"""

    def apply(
        self,
        violations: Violations,
        source_files: SourceFiles,
        per_file_ignores: tuple[PerFileIgnoreEntry, ...],
        ignore_rules: frozenset[str],
    ) -> Violations:
        """Ignore 処理を一括実行して違反を除外した Violations を返す

        Args:
            violations: フィルタリング対象の違反群
            source_files: 解析対象のソースファイル群
            per_file_ignores: 設定ファイル由来のファイル単位 ignore エントリ群
            ignore_rules: 全ファイル・全行に適用されるグローバルな ignore ルール ID 群。`--ignore-rule` オプションで指定される

        Returns:
            ignore 対象を除外した Violations

        Flow:
            1. 設定由来ディレクティブを解決: `per_file_ignores` をファイルパスに対応付ける
            2. コメント由来ディレクティブを解析: ソースファイルのインラインコメントを抽出する
            3. ファイル単位ディレクティブを統合: 設定由来とコメント由来を独立して解析してから
               マージすることで、それぞれの解析ロジックを疎結合に保つ
            4. 行単位ディレクティブを解析・統合: ソースファイルの行コメントを抽出してマージする
            5. 違反をフィルタリング: 統合したディレクティブと `ignore_rules` を適用して除外する
        """
        file_paths = tuple(sf.file_path for sf in source_files)
        config_directives = ConfigIgnoreResolver().resolve(per_file_ignores, file_paths)
        comment_directives = FileIgnoreParser().parse_all(source_files)
        merged_directives = FileIgnoreDirective.merge(config_directives, comment_directives)
        raw_line_directives = LineIgnoreParser().parse_all(source_files)
        line_directives = LineIgnoreDirective.merge(raw_line_directives)
        return ViolationFilter().filter(
            violations, merged_directives, line_directives, ignore_rules
        )
