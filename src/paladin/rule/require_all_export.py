"""__all__ エクスポート要求ルール

仕様は docs/rules/require-all-export.md を参照。
"""

import ast

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.types import RuleMeta, SourceFile, Violation


class RequireAllExportRule:
    """__init__.py に __all__ が定義されているかを AST で判定するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._extractor = AllExportsExtractor()
        self._meta = RuleMeta(
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            summary="__init__.py に __all__ の定義を要求する",
            intent="パッケージの公開インターフェースを明示し、意図しないシンボルの露出を防ぐ",
            guidance="__init__.py に __all__ が定義されているかを確認する",
            suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if not source_file.is_init_py:
            return ()
        if not self._has_substantial_code(source_file.tree):
            return ()
        if self._extractor.has_all_definition(source_file):
            return ()
        symbols = self._collect_public_symbols(source_file)
        if symbols:
            symbols_str = ", ".join(f'"{s}"' for s in sorted(symbols))
            suggestion = f"`__all__ = [{symbols_str}]` のように公開シンボルを定義してください"
        else:
            suggestion = "`__all__` リストを定義し、公開するシンボルを明示的に列挙してください"
        return (
            self._meta.create_violation_at(
                location=source_file.location(1),
                message="__init__.py に __all__ が定義されていない",
                reason="__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある",
                suggestion=suggestion,
            ),
        )

    def _has_substantial_code(self, tree: ast.Module) -> bool:
        """実質的なコード（コメント・docstring以外）が存在するか判定する"""
        for node in tree.body:
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                # docstring はスキップ
                continue
            return True
        return False

    def _collect_public_symbols(self, source_file: SourceFile) -> list[str]:
        """トップレベルの公開シンボルを収集する

        from .xxx import Yyy の Yyy と、アンダースコア始まりでないトップレベル定義を返す。
        """
        symbols: list[str] = []
        for stmt in source_file.top_level_imports:
            if stmt.is_relative:
                for imported in stmt.names:
                    if not imported.bound_name.startswith("_"):
                        symbols.append(imported.bound_name)
        for node in source_file.tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and not node.name.startswith("_"):
                symbols.append(node.name)
        return symbols
