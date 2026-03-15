"""ファイル単位・行単位の Ignore 機能

ファイル先頭コメントから ignore-file ディレクティブを抽出し、
また直前コメントから行単位 ignore ディレクティブを抽出し、
Violations から該当違反を除外する。
設定ファイルの per-file-ignores による FileIgnoreDirective 生成も担当する。
"""

import re
from dataclasses import dataclass
from pathlib import Path, PurePath

from paladin.config import PerFileIgnoreEntry
from paladin.lint import SourceFiles, Violation, Violations


@dataclass(frozen=True)
class FileIgnoreDirective:
    """単一ファイルの ignore-file ディレクティブ情報を保持する値オブジェクト"""

    file_path: Path
    ignore_all: bool
    ignored_rules: frozenset[str]


@dataclass(frozen=True)
class LineIgnoreDirective:
    """行単位の ignore ディレクティブ情報を保持する値オブジェクト"""

    file_path: Path
    target_line: int
    ignore_all: bool
    ignored_rules: frozenset[str]


class FileIgnoreParser:
    """ソーステキストの先頭コメントから ignore-file ディレクティブを抽出するパーサー"""

    _DIRECTIVE_PATTERN = re.compile(r"^# paladin: ignore-file(\[(.+)\])?$")
    _SHEBANG_PATTERN = re.compile(r"^#!")
    _ENCODING_PATTERN = re.compile(r"# -\*- coding:")

    def parse(self, file_path: Path, source: str) -> FileIgnoreDirective:
        """ソーステキストのヘッダー領域から ignore-file ディレクティブを抽出する

        Args:
            file_path: 対象ファイルのパス
            source: ソーステキスト

        Returns:
            FileIgnoreDirective。ディレクティブなしの場合は ignore_all=False、ignored_rules=frozenset()
        """
        lines = source.splitlines()
        i = 0
        in_docstring = False
        docstring_quote = ""

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # docstring 内をスキップ
            if in_docstring:
                if docstring_quote in line:
                    in_docstring = False
                i += 1
                continue

            # 空行をスキップ
            if stripped == "":
                i += 1
                continue

            # shebang 行をスキップ
            if self._SHEBANG_PATTERN.match(stripped):
                i += 1
                continue

            # エンコーディング宣言をスキップ
            if self._ENCODING_PATTERN.search(stripped):
                i += 1
                continue

            # docstring 開始の検出
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_quote = stripped[:3]
                # 同一行で閉じている場合
                rest = stripped[3:]
                if docstring_quote in rest:
                    i += 1
                    continue
                in_docstring = True
                i += 1
                continue

            # ignore-file ディレクティブの検出
            match = self._DIRECTIVE_PATTERN.match(stripped)
            if match:
                rule_spec = match.group(2)
                if rule_spec is None:
                    return FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=True,
                        ignored_rules=frozenset(),
                    )
                rules = frozenset(r.strip() for r in rule_spec.split(","))
                return FileIgnoreDirective(
                    file_path=file_path,
                    ignore_all=False,
                    ignored_rules=rules,
                )

            # 通常コメント行（# paladin: ではない）をスキップ
            if stripped.startswith("#"):
                i += 1
                continue

            # ヘッダー領域外（import 文や実行コードなど）に到達したら走査終了
            break

        return FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=frozenset(),
        )

    def parse_all(self, source_files: SourceFiles) -> tuple[FileIgnoreDirective, ...]:
        """複数ファイルのディレクティブをタプルで返す

        Args:
            source_files: 検査対象のソースファイル群

        Returns:
            各ファイルの FileIgnoreDirective のタプル
        """
        return tuple(self.parse(sf.file_path, sf.source) for sf in source_files)


class LineIgnoreParser:
    """ソーステキストの直前コメントから行単位 ignore ディレクティブを抽出するパーサー"""

    _LINE_DIRECTIVE_PATTERN = re.compile(r"^# paladin: ignore(\[(.+)\])?$")

    def parse(self, file_path: Path, source: str) -> tuple[LineIgnoreDirective, ...]:
        """ソーステキストから行単位 ignore ディレクティブを抽出する

        Args:
            file_path: 対象ファイルのパス
            source: ソーステキスト

        Returns:
            LineIgnoreDirective のタプル。ディレクティブなしの場合は空タプル
        """
        lines = source.splitlines()
        result: list[LineIgnoreDirective] = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            match = self._LINE_DIRECTIVE_PATTERN.match(stripped)
            if not match:
                continue

            # 直後の行が存在し、かつ非空行であることを確認する
            next_index = i + 1
            if next_index >= len(lines):
                continue
            next_line = lines[next_index]
            if next_line.strip() == "":
                continue

            rule_spec = match.group(2)
            if rule_spec is None:
                result.append(
                    LineIgnoreDirective(
                        file_path=file_path,
                        target_line=next_index + 1,  # 1-indexed
                        ignore_all=True,
                        ignored_rules=frozenset(),
                    )
                )
            else:
                rules = frozenset(r.strip() for r in rule_spec.split(","))
                result.append(
                    LineIgnoreDirective(
                        file_path=file_path,
                        target_line=next_index + 1,  # 1-indexed
                        ignore_all=False,
                        ignored_rules=rules,
                    )
                )

        return tuple(result)

    def parse_all(self, source_files: SourceFiles) -> tuple[LineIgnoreDirective, ...]:
        """複数ファイルのディレクティブをタプルで返す

        Args:
            source_files: 検査対象のソースファイル群

        Returns:
            全ファイルの LineIgnoreDirective を平坦化したタプル
        """
        return tuple(
            directive for sf in source_files for directive in self.parse(sf.file_path, sf.source)
        )


class ViolationFilter:
    """FileIgnoreDirective / LineIgnoreDirective に基づいて Violations から ignore 対象の違反を除外するフィルター"""

    def filter(
        self,
        violations: Violations,
        directives: tuple[FileIgnoreDirective, ...],
        line_directives: tuple[LineIgnoreDirective, ...] = (),
        ignore_rules: frozenset[str] = frozenset(),
    ) -> Violations:
        """Ignore 対象の違反を除外した新しい Violations を返す

        Args:
            violations: フィルタリング対象の違反群
            directives: ファイルごとの ignore ディレクティブ群
            line_directives: 行単位の ignore ディレクティブ群
            ignore_rules: CLI から指定されたグローバル ignore ルール ID 群

        Returns:
            ignore 対象を除外した Violations
        """
        file_directive_map = {d.file_path: d for d in directives}
        filtered = tuple(
            v
            for v in violations
            if not self._should_ignore_by_cli(v, ignore_rules)
            and not self._should_ignore_by_file(v, file_directive_map)
            and not self._should_ignore_by_line(v, line_directives)
        )
        return Violations(items=filtered)

    def _should_ignore_by_cli(
        self,
        violation: Violation,
        ignore_rules: frozenset[str],
    ) -> bool:
        return violation.rule_id in ignore_rules

    def _should_ignore_by_file(
        self,
        violation: Violation,
        directive_map: dict[Path, FileIgnoreDirective],
    ) -> bool:
        directive = directive_map.get(violation.file)
        if directive is None:
            return False
        if directive.ignore_all:
            return True
        return violation.rule_id in directive.ignored_rules

    def _should_ignore_by_line(
        self,
        violation: Violation,
        line_directives: tuple[LineIgnoreDirective, ...],
    ) -> bool:
        for directive in line_directives:
            if violation.file != directive.file_path:
                continue
            if violation.line != directive.target_line:
                continue
            if directive.ignore_all:
                return True
            if violation.rule_id in directive.ignored_rules:
                return True
        return False


class ConfigIgnoreResolver:
    """ProjectConfig のパターンと file_paths を照合して FileIgnoreDirective を生成するリゾルバー

    glob パターンの照合には PurePath.full_match() を使用する。
    ディレクトリ単位のパターン（例: "tests/**"）が絶対パスに対しても
    正しくマッチするよう、相対パターンには自動的に "**/" を前置する。
    """

    def _normalize_glob_pattern(self, pattern: str) -> str:
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

        result: list[FileIgnoreDirective] = []
        for file_path in file_paths:
            matched_entries: list[PerFileIgnoreEntry] = [
                entry
                for entry in per_file_ignores
                if PurePath(str(file_path)).full_match(self._normalize_glob_pattern(entry.pattern))
            ]
            if not matched_entries:
                continue

            if any(entry.ignore_all for entry in matched_entries):
                result.append(
                    FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=True,
                        ignored_rules=frozenset(),
                    )
                )
            else:
                merged_rules: frozenset[str] = frozenset()
                for entry in matched_entries:
                    merged_rules = merged_rules | entry.rule_ids
                result.append(
                    FileIgnoreDirective(
                        file_path=file_path,
                        ignore_all=False,
                        ignored_rules=merged_rules,
                    )
                )
        return tuple(result)
