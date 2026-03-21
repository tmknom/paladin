"""__all__ シンボル抽出ドメインサービス

SourceFile の AST から __all__ シンボルを抽出する値オブジェクトとサービスを提供する。
"""

import ast
from collections.abc import Iterator
from dataclasses import dataclass

from paladin.rule.types import SourceFile


@dataclass(frozen=True)
class AllExports:
    """__all__ から抽出したシンボル群を保持する値オブジェクト"""

    symbols: tuple[str, ...]
    node: ast.Assign | ast.AugAssign | None

    @property
    def is_defined(self) -> bool:
        """__all__ が定義されているかどうかを返す"""
        return self.node is not None

    @property
    def is_empty(self) -> bool:
        """シンボルが空かどうかを返す"""
        return len(self.symbols) == 0

    @property
    def has_exports(self) -> bool:
        """__all__ が定義済みかつシンボルが存在するかを返す"""
        return self.is_defined and not self.is_empty

    @property
    def lineno(self) -> int:
        """__all__ 代入文の行番号を返す（node がない場合は 1）"""
        return self.node.lineno if self.node is not None else 1

    def __contains__(self, name: object) -> bool:
        """シンボルが含まれているかどうかを返す"""
        return name in self.symbols

    def __len__(self) -> int:
        """シンボル数を返す"""
        return len(self.symbols)

    def __iter__(self) -> Iterator[str]:
        """シンボルをイテレーションする"""
        return iter(self.symbols)


class AllExportsExtractor:
    """SourceFile の AST から __all__ シンボルを抽出するドメインサービス"""

    def _find_all_node(self, tree: ast.Module) -> ast.Assign | ast.AugAssign | None:
        """トップレベルの __all__ 代入ノードを返す（存在しなければ None）"""
        for node in tree.body:
            result = self._match_all_node(node)
            if result is not None:
                return result
        return None

    def _match_all_node(self, node: ast.stmt) -> ast.Assign | ast.AugAssign | None:
        """Node が __all__ 代入であれば返す。そうでなければ None を返す"""
        if isinstance(node, ast.Assign) and self._is_all_assign(node):
            return node
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
        ):
            return node
        return None

    def _is_all_assign(self, node: ast.Assign) -> bool:
        """ast.Assign が __all__ への代入かどうかを返す"""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                return True
        return False

    def _extract_symbols(self, node: ast.Assign | ast.AugAssign) -> tuple[str, ...]:
        """__all__ 代入ノードから文字列リテラルのシンボル群を抽出する"""
        value = node.value if isinstance(node, ast.Assign) else None
        if not isinstance(value, (ast.List, ast.Tuple)):
            return ()
        return tuple(
            elt.value
            for elt in value.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        )

    def extract(self, source_file: SourceFile) -> AllExports:
        """__all__ の代入文を探し、文字列リテラルを AllExports として返す

        __all__ が定義されていない場合は node=None の空の AllExports を返す。
        """
        node = self._find_all_node(source_file.tree)
        if node is None:
            return AllExports(symbols=(), node=None)
        symbols = self._extract_symbols(node)
        return AllExports(symbols=symbols, node=node)

    def has_all_definition(self, source_file: SourceFile) -> bool:
        """トップレベルに __all__ の代入（AugAssign 含む）が存在するか判定する"""
        return self._find_all_node(source_file.tree) is not None

    def extract_with_reexports(self, source_file: SourceFile) -> set[str]:
        """__all__ のシンボルと相対インポートで再エクスポートされたシンボルを返す

        __init__.py の公開シンボル全体を収集する際に使用する。
        ast.walk で全ツリーを走査し、ネストされた __all__ 定義も拾う。
        """
        exports: set[str] = set()

        for node in ast.walk(source_file.tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "__all__"
            ):
                exports.update(self._extract_symbols(node))

            if not (isinstance(node, ast.ImportFrom) and node.level >= 1 and node.names):
                continue
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                exports.add(name)

        return exports
