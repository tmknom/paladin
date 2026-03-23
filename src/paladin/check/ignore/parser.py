"""FileIgnoreParser / LineIgnoreParser の実装"""

import re
from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.rule import SourceFiles


def _parse_rule_spec(rule_spec: str) -> frozenset[str]:
    """カンマ区切りのルール仕様文字列を frozenset に変換する"""
    return frozenset(r.strip() for r in rule_spec.split(","))


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
            stripped = lines[i].strip()

            # docstring 内をスキップ
            if in_docstring:
                in_docstring = docstring_quote not in lines[i]
                i += 1
                continue

            # docstring 開始の検出
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_quote = stripped[:3]
                in_docstring = docstring_quote not in stripped[3:]
                i += 1
                continue

            # ignore-file ディレクティブの検出
            directive = self._parse_directive(file_path, stripped)
            if directive is not None:
                return directive

            # ヘッダースキップ対象行（空行・shebang・エンコーディング・通常コメント）
            if self._is_header_skip_line(stripped):
                i += 1
                continue

            # ヘッダー領域外（import 文や実行コードなど）に到達したら走査終了
            break

        return FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=frozenset(),
        )

    def _is_header_skip_line(self, stripped: str) -> bool:
        """ヘッダー領域でスキップすべき行かどうかを返す"""
        if stripped == "":
            return True
        if self._SHEBANG_PATTERN.match(stripped):
            return True
        if self._ENCODING_PATTERN.search(stripped):
            return True
        return bool(stripped.startswith("#"))

    def _parse_directive(self, file_path: Path, stripped: str) -> FileIgnoreDirective | None:
        """行テキストから ignore-file ディレクティブを解析する。該当しない場合は None を返す"""
        match = self._DIRECTIVE_PATTERN.match(stripped)
        if match is None:
            return None
        rule_spec = match.group(2)
        if rule_spec is None:
            return FileIgnoreDirective(
                file_path=file_path,
                ignore_all=True,
                ignored_rules=frozenset(),
            )
        return FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=_parse_rule_spec(rule_spec),
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
                result.append(
                    LineIgnoreDirective(
                        file_path=file_path,
                        target_line=next_index + 1,  # 1-indexed
                        ignore_all=False,
                        ignored_rules=_parse_rule_spec(rule_spec),
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
