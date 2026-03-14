"""Pythonソースコードの解析済み表現

ASTパーサーが生成する値オブジェクトを定義する。
"""

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedFile:
    """単一ファイルのAST解析結果を保持する不変な値オブジェクト"""

    file_path: Path
    tree: ast.Module


@dataclass(frozen=True)
class ParsedFiles:
    """複数ファイルのAST解析結果を集約する不変な値オブジェクト"""

    files: tuple[ParsedFile, ...]

    def __len__(self) -> int:
        """解析済みファイル数を返す"""
        return len(self.files)

    def __iter__(self) -> Iterator[ParsedFile]:
        """解析済みファイルをイテレーションする"""
        return iter(self.files)
