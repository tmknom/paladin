"""値オブジェクト生成ファクトリ"""

import ast
from pathlib import Path

from paladin.rule import SourceFile, SourceFiles


class SourceFileFactory:
    """テスト用 SourceFile / SourceFiles 生成ファクトリ"""

    @staticmethod
    def make(source: str, filename: str = "example.py") -> SourceFile:
        return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)

    @staticmethod
    def make_test(source: str, filename: str = "tests/test_example.py") -> SourceFile:
        return SourceFile(file_path=Path(filename), tree=ast.parse(source), source=source)

    @staticmethod
    def make_many(*pairs: tuple[str, str]) -> SourceFiles:
        return SourceFiles(files=tuple(SourceFileFactory.make(src, name) for src, name in pairs))


class AstNodeExtractor:
    """テスト用の AST ノード抽出ヘルパー"""

    @staticmethod
    def first_call(source: str) -> ast.Call:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                return node
        raise AssertionError(f"ast.Call が見つかりません: {source!r}")

    @staticmethod
    def first_attribute(source: str) -> ast.Attribute:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                return node
        raise AssertionError(f"ast.Attribute が見つかりません: {source!r}")

    @staticmethod
    def first_function(source: str) -> ast.FunctionDef:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node
        raise AssertionError(f"ast.FunctionDef が見つかりません: {source!r}")

    @staticmethod
    def first_class_def(source: str) -> ast.ClassDef:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                return node
        raise AssertionError(f"ast.ClassDef が見つかりません: {source!r}")
