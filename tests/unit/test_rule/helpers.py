"""値オブジェクト生成ファクトリ"""

import ast
from pathlib import Path

from paladin.rule import SourceFile, SourceFiles


def make_source_file(source: str, filename: str = "example.py") -> SourceFile:
    """テスト用の SourceFile を生成する"""
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def make_test_source_file(source: str, filename: str = "tests/test_example.py") -> SourceFile:
    """テスト用の SourceFile を生成する（tests/ 配下のファイルとして）"""
    return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)


def make_source_files(*pairs: tuple[str, str]) -> SourceFiles:
    """テスト用の SourceFiles を生成する（(source, filename) のペアから）"""
    return SourceFiles(files=tuple(make_source_file(src, name) for src, name in pairs))
