"""Ignoreパッケージの設定ファイル解決

per-file-ignores 設定をファイルパスと照合して FileIgnoreDirective に変換する。
"""

from pathlib import Path, PurePath

from paladin.check.ignore.directive import FileIgnoreDirective
from paladin.rule import PerFileIgnoreEntry


class ConfigIgnoreResolver:
    """ProjectConfig のパターンと file_paths を照合して FileIgnoreDirective を生成するリゾルバー

    glob パターンの照合には PurePath.full_match() を使用する。
    ディレクトリ単位のパターン（例: "tests/**"）が絶対パスに対しても
    正しくマッチするよう、相対パターンには自動的に "**/" を前置する。
    """

    def _normalize_glob_pattern(self, pattern: str) -> str:
        """Glob パターンに "**/" プレフィックスを付加して正規化する"""
        if pattern.startswith("/") or pattern.startswith("**/"):
            return pattern
        return "**/" + pattern

    def resolve(
        self,
        per_file_ignores: tuple[PerFileIgnoreEntry, ...],
        file_paths: tuple[Path, ...],
    ) -> tuple[FileIgnoreDirective, ...]:
        """各ファイルパスに対してマッチするパターンを照合し、FileIgnoreDirective を返す

        Args:
            per_file_ignores: ファイルごとのignoreエントリ群
            file_paths: 照合対象のファイルパス群

        Returns:
            マッチしたファイルの FileIgnoreDirective のタプル。マッチしないファイルは含まない
        """
        if not per_file_ignores or not file_paths:
            return ()

        normalized_patterns = [
            (entry, self._normalize_glob_pattern(entry.pattern)) for entry in per_file_ignores
        ]
        result: list[FileIgnoreDirective] = []
        for file_path in file_paths:
            pure_path = PurePath(str(file_path))
            matched_entries: list[PerFileIgnoreEntry] = [
                entry for entry, pattern in normalized_patterns if pure_path.full_match(pattern)
            ]
            if not matched_entries:
                continue
            result.append(self._build_directive(file_path, matched_entries))
        return tuple(result)

    def _build_directive(
        self, file_path: Path, matched_entries: list[PerFileIgnoreEntry]
    ) -> FileIgnoreDirective:
        """マッチしたエントリ群から FileIgnoreDirective を生成する"""
        if any(entry.ignore_all for entry in matched_entries):
            return FileIgnoreDirective(
                file_path=file_path,
                ignore_all=True,
                ignored_rules=frozenset(),
            )
        merged_rules: frozenset[str] = frozenset()
        for entry in matched_entries:
            merged_rules = merged_rules | entry.rule_ids
        return FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=merged_rules,
        )
