"""__all__ エクスポート要求ルール

仕様は docs/rules/require-all-export.md を参照。
"""

import ast

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.import_statement import ImportedName
from paladin.rule.types import RuleMeta, SourceFile, Violation


class PublicSymbolCollector:
    """公開シンボルを収集する"""

    @staticmethod
    def collect(source_file: SourceFile) -> list[str]:
        """トップレベルの公開シンボルを収集する

        from .xxx import Yyy の Yyy と、アンダースコア始まりでないトップレベル定義を返す。
        """
        symbols: list[str] = []
        for stmt in source_file.top_level_imports:
            if not stmt.is_relative:
                continue
            symbols.extend(PublicSymbolCollector._public_imported_names(stmt.names))
        for node in source_file.tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) and not node.name.startswith("_"):
                symbols.append(node.name)
        return symbols

    @staticmethod
    def has_substantial_code(tree: ast.Module) -> bool:
        """実質的なコード（コメント・docstring以外）が存在するか判定する"""
        for node in tree.body:
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue
            return True
        return False

    @staticmethod
    def _public_imported_names(names: tuple[ImportedName, ...]) -> list[str]:
        """インポートされた名前のうち公開シンボル（_ 始まりでないもの）を返す"""
        return [
            imported.bound_name for imported in names if not imported.bound_name.startswith("_")
        ]


class AllExportDetector:
    """__all__ 未定義の Violation を生成する"""

    @staticmethod
    def detect(source_file: SourceFile, symbols: list[str], meta: RuleMeta) -> Violation:
        """__all__ 未定義の Violation を生成する"""
        if symbols:
            symbols_str = ", ".join(f'"{s}"' for s in sorted(symbols))
            suggestion = f"`__all__ = [{symbols_str}]` のように公開シンボルを定義してください"
        else:
            suggestion = "`__all__` リストを定義し、公開するシンボルを明示的に列挙してください"
        return meta.create_violation_at(
            location=source_file.location(1),
            message="__init__.py に __all__ が定義されていない",
            reason="__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある",
            suggestion=suggestion,
        )


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
        if not PublicSymbolCollector.has_substantial_code(source_file.tree):
            return ()
        if self._extractor.has_all_definition(source_file):
            return ()
        symbols = PublicSymbolCollector.collect(source_file)
        return (AllExportDetector.detect(source_file, symbols, self._meta),)
