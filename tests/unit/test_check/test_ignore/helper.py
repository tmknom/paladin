"""値オブジェクト生成ファクトリ"""

import ast
from pathlib import Path

from paladin.rule import SourceFile


def make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    """テスト用の SourceFile を生成する"""
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)
