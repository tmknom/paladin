"""値オブジェクト生成ファクトリ"""

import ast
from pathlib import Path

from paladin.rule import SourceFile


class SourceFileFactory:
    """テスト用 SourceFile 生成ファクトリ"""

    @staticmethod
    def make(source: str, filename: str = "example.py") -> SourceFile:
        return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)
