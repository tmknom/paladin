"""Ignore パッケージの解析層

ソーステキストを走査してディレクティブを値オブジェクトに変換する責務を持つ。
"""

import re
from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.rule import SourceFiles


def _parse_rule_spec(rule_spec: str) -> frozenset[str]:
    """カンマ区切りのルール仕様文字列を frozenset に変換する"""
    return frozenset(r.strip() for r in rule_spec.split(","))


class FileIgnoreParser:
    """ソーステキストの先頭コメントから ignore-file ディレクティブを抽出するパーサー

    ファイル先頭のヘッダー領域のみを走査対象とし、import 文や実行コードに達した
    時点で走査を打ち切る。これはファイル全体に適用されるディレクティブがヘッダーに
    記述されるという規約を前提とする。
    """

    _DIRECTIVE_PATTERN = re.compile(r"^# paladin: ignore-file(\[(.+)\])?(\s+--\s.*)?$")
    _SHEBANG_PATTERN = re.compile(r"^#!")
    _ENCODING_PATTERN = re.compile(r"# -\*- coding:")

    def parse(self, file_path: Path, source: str) -> FileIgnoreDirective:
        """ソーステキストのヘッダー領域から ignore-file ディレクティブを抽出する

        Args:
            file_path: 対象ファイルのパス
            source: ソーステキスト

        Returns:
            FileIgnoreDirective。ディレクティブなしの場合は ignore_all=False、ignored_rules=frozenset()

        Flow:
            1. 行を順に走査し、docstring 内はフラグで読み飛ばす
            2. docstring 開始（\"\"\" / '''）を検出したらフラグを立て、同一行に閉じクォートが
               あれば即座にフラグを下ろす
            3. ディレクティブ行を検出したら即座に返す
            4. 空行・shebang・エンコーディング宣言・通常コメントはスキップして継続
            5. それ以外（import 文や実行コード）に到達したらヘッダー領域外と判断して break
        """
        lines = source.splitlines()
        i = 0
        in_docstring = False
        docstring_quote = ""

        while i < len(lines):
            stripped = lines[i].strip()

            if in_docstring:
                # クォート文字列が行内に現れれば docstring 終了と見なす
                in_docstring = docstring_quote not in lines[i]
                i += 1
                continue

            # docstring 開始の検出
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_quote = stripped[:3]
                in_docstring = docstring_quote not in stripped[3:]
                i += 1
                continue

            # ignore-file ディレクティブの検出（先頭空白を除去した行で照合する）
            directive = self._parse_directive(file_path, lines[i].lstrip())
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
        if stripped == "":
            return True
        if self._SHEBANG_PATTERN.match(stripped):
            return True
        if self._ENCODING_PATTERN.search(stripped):
            return True
        return bool(stripped.startswith("#"))

    def _parse_directive(self, file_path: Path, stripped: str) -> FileIgnoreDirective | None:
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
            各ファイルに対して必ず 1 件の FileIgnoreDirective を含むタプル。
            ディレクティブが存在しないファイルも ignore_all=False の値オブジェクトとして返る。
        """
        return tuple(self.parse(sf.file_path, sf.source) for sf in source_files)


class LineIgnoreParser:
    """ソーステキストの直前コメントと行末コメントから行単位 ignore ディレクティブを抽出するパーサー

    2 種類の検出方式を持ち、target_line の決定方法が非対称となる。
    - 直前コメント方式（`# paladin: ignore`）: ディレクティブの次の行を target_line とする
    - 行末コメント方式（`code  # paladin: ignore`）: ディレクティブが記述されたその行自身を target_line とする

    行番号は 1-indexed。
    """

    _LINE_DIRECTIVE_PATTERN = re.compile(r"^# paladin: ignore(\[(.+)\])?(\s+--\s.*)?$")
    _TRAILING_DIRECTIVE_PATTERN = re.compile(r"\s+# paladin: ignore(\[(.+)\])?(\s+--\s.*)?$")

    def parse(self, file_path: Path, source: str) -> tuple[LineIgnoreDirective, ...]:
        """ソーステキストから行単位 ignore ディレクティブを抽出する

        直前コメント方式（`# paladin: ignore[rule-id]`）と
        行末コメント方式（`code  # paladin: ignore[rule-id]`）の両方を検出する。

        Args:
            file_path: 対象ファイルのパス
            source: ソーステキスト

        Returns:
            LineIgnoreDirective のタプル。ディレクティブなしの場合は空タプル
        """
        lines = source.splitlines()
        return tuple(
            directive
            for i, line in enumerate(lines)
            for directive in self._parse_line(file_path, lines, i, line)
        )

    def _parse_line(
        self,
        file_path: Path,
        lines: list[str],
        i: int,
        line: str,
    ) -> list[LineIgnoreDirective]:
        """1行分のディレクティブを返す（0〜1件）

        直前コメントパターンを優先評価し、マッチした場合は行末コメントを確認しない
        排他処理とする。これにより 1 行から複数ディレクティブが生成される状況を防ぐ。
        0 件になる条件: (1) どちらのパターンにもマッチしない、(2) 直前コメントにマッチしたが
        次行が存在しないまたは空行である。
        """
        preceding_match = self._LINE_DIRECTIVE_PATTERN.match(line.lstrip())
        if preceding_match:
            directive = self._parse_preceding(file_path, lines, i, preceding_match)
            return [directive] if directive is not None else []
        trailing_match = self._TRAILING_DIRECTIVE_PATTERN.search(line)
        if trailing_match:
            return [self._parse_trailing(file_path, i, trailing_match)]
        return []

    def _parse_preceding(
        self,
        file_path: Path,
        lines: list[str],
        i: int,
        match: re.Match[str],
    ) -> LineIgnoreDirective | None:
        """直前コメント方式のディレクティブを生成する

        Flow:
            1. 次行インデックスを i + 1 として計算する
            2. 次行が存在しない（インデックス範囲外）、または次行が空行なら None を返す
            3. マッチグループからルール仕様を解析して LineIgnoreDirective を生成する
               （次行の行番号を target_line とする）
        """
        next_index = i + 1
        if next_index >= len(lines) or lines[next_index].strip() == "":
            return None
        rule_spec = match.group(2)
        if rule_spec is None:
            return LineIgnoreDirective(
                file_path=file_path,
                target_line=next_index + 1,
                ignore_all=True,
                ignored_rules=frozenset(),
            )
        return LineIgnoreDirective(
            file_path=file_path,
            target_line=next_index + 1,
            ignore_all=False,
            ignored_rules=_parse_rule_spec(rule_spec),
        )

    def _parse_trailing(
        self,
        file_path: Path,
        i: int,
        match: re.Match[str],
    ) -> LineIgnoreDirective:
        """_parse_preceding と異なり、次行確認が不要なため常に LineIgnoreDirective を返す"""
        rule_spec = match.group(2)
        if rule_spec is None:
            return LineIgnoreDirective(
                file_path=file_path,
                target_line=i + 1,
                ignore_all=True,
                ignored_rules=frozenset(),
            )
        return LineIgnoreDirective(
            file_path=file_path,
            target_line=i + 1,
            ignore_all=False,
            ignored_rules=_parse_rule_spec(rule_spec),
        )

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
