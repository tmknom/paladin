"""別パッケージのシンボルを __all__ で再エクスポートすることを禁止するルール

仕様は docs/rules/no-cross-package-reexport.md を参照。
"""

import ast
from typing import cast

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoCrossPackageReexportRule:
    """__init__.py の __all__ に別パッケージのシンボルが含まれていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._extractor = AllExportsExtractor()
        self._meta = RuleMeta(
            rule_id="no-cross-package-reexport",
            rule_name="No Cross Package Reexport",
            summary="別パッケージのシンボルを自パッケージの __all__ で再エクスポートすることを禁止する",
            intent="__all__ には自パッケージ内で定義したシンボルのみを列挙することで、パッケージ境界を明確に保つ",
            guidance="__init__.py の __all__ に含まれる別パッケージ由来のシンボルを確認する",
            suggestion="別パッケージのシンボルを __all__ から削除し、利用者が各パッケージから直接インポートするよう誘導してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if not source_file.is_init_py:
            return ()

        current_package = self._resolver.resolve_exact_package_path(source_file.file_path)
        if current_package is None:
            return ()

        all_exports = self._extractor.extract(source_file)
        if not all_exports.is_defined or all_exports.is_empty:
            return ()

        import_mapping = self._collect_import_mapping(source_file.tree)
        assign_node = cast(ast.Assign, all_exports.node)

        violations: list[Violation] = []
        for name in all_exports:
            if name not in import_mapping:
                continue
            import_source = import_mapping[name]
            if not PackageResolver.is_subpackage(import_source, current_package):
                source_package = PackageResolver.extract_package_key(import_source)
                violations.append(
                    self._make_violation(
                        source_file=source_file,
                        line=assign_node.lineno,
                        name=name,
                        source_package=source_package,
                        current_package=current_package,
                    )
                )
        return tuple(violations)

    def _collect_import_mapping(self, tree: ast.Module) -> dict[str, str]:
        """AST からトップレベルの from X import Y 文を収集し {シンボル名: インポート元} を返す。

        - as エイリアスがある場合は asname をキーとする
        - 相対インポート（level >= 1）はスキップする
        """
        mapping: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.level is not None and node.level >= 1:
                continue  # 相対インポートはスキップ
            if node.module is None:
                continue
            for alias in node.names:
                key = alias.asname if alias.asname else alias.name
                mapping[key] = node.module
        return mapping

    def _make_violation(
        self,
        source_file: SourceFile,
        line: int,
        name: str,
        source_package: str,
        current_package: str,
    ) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        return self._meta.create_violation(
            file=source_file.file_path,
            line=line,
            column=0,
            message=f"__all__ に別パッケージのシンボル `{name}` が含まれている（定義元: `{source_package}`）",
            reason=f"`{source_package}` で定義されたシンボルを `{current_package}` の公開 API として再エクスポートすると、パッケージ境界が曖昧になる",
            suggestion=f"`{name}` を __all__ から削除し、利用者が `from {source_package} import {name}` を直接使用するよう誘導してください",
        )
