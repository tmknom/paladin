"""Ignoreパッケージのドメインモデル定義

ファイル単位・行単位の ignore ディレクティブを表す値オブジェクトを定義する。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileIgnoreDirective:
    """単一ファイルの ignore-file ディレクティブ情報を保持する値オブジェクト"""

    file_path: Path
    ignore_all: bool
    ignored_rules: frozenset[str]

    @staticmethod
    def merge(
        config_directives: tuple["FileIgnoreDirective", ...],
        comment_directives: tuple["FileIgnoreDirective", ...],
    ) -> tuple["FileIgnoreDirective", ...]:
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


@dataclass(frozen=True)
class LineIgnoreDirective:
    """行単位の ignore ディレクティブ情報を保持する値オブジェクト"""

    file_path: Path
    target_line: int
    ignore_all: bool
    ignored_rules: frozenset[str]
