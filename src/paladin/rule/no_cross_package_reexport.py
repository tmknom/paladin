"""別パッケージのシンボルを __all__ で再エクスポートすることを禁止するルール

仕様は docs/rules/no-cross-package-reexport.md を参照。
"""

import ast
from pathlib import Path

from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoCrossPackageReexportRule:
    """__init__.py の __all__ に別パッケージのシンボルが含まれていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
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
        if source_file.file_path.name != "__init__.py":
            return ()

        current_package = self._resolve_current_package(source_file.file_path)
        if current_package is None:
            return ()

        all_symbols = self._extract_all_symbols(source_file.tree)
        if not all_symbols:
            return ()

        import_mapping = self._collect_import_mapping(source_file.tree)

        violations: list[Violation] = []
        for node in source_file.tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "__all__"):
                    continue
                if not isinstance(node.value, (ast.List, ast.Tuple)):
                    continue
                for elt in node.value.elts:
                    if not isinstance(elt, ast.Constant) or not isinstance(elt.value, str):
                        continue
                    name = elt.value
                    if name not in import_mapping:
                        continue
                    import_source = import_mapping[name]
                    if not self._is_same_package(current_package, import_source):
                        source_package = self._to_source_package(import_source)
                        violations.append(
                            self._violation(
                                file=source_file.file_path,
                                line=node.lineno,
                                name=name,
                                source_package=source_package,
                                current_package=current_package,
                            )
                        )
        return tuple(violations)

    def _resolve_current_package(self, file_path: Path) -> str | None:
        """file_path から現在のパッケージ名を導出する。

        PackageResolver.resolve_exact_package_path() に委譲する。
        """
        return self._resolver.resolve_exact_package_path(file_path)

    def _extract_all_symbols(self, tree: ast.Module) -> tuple[str, ...]:
        """AST からトップレベルの __all__ 代入文を探し、文字列リテラルを抽出する"""
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id == "__all__"):
                    continue
                if not isinstance(node.value, (ast.List, ast.Tuple)):
                    return ()
                result: list[str] = []
                for elt in node.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        result.append(elt.value)
                return tuple(result)
        return ()

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

    def _is_same_package(self, current_package: str, import_source: str) -> bool:
        """インポート元モジュールパスが現在のパッケージ配下かどうかを判定する"""
        return import_source == current_package or import_source.startswith(current_package + ".")

    def _to_source_package(self, import_source: str) -> str:
        """インポート元モジュールパスから先頭2セグメントを返す。

        セグメント数が2未満の場合はそのまま返す。
        """
        segments = import_source.split(".")
        if len(segments) < 2:
            return import_source
        return ".".join(segments[:2])

    def _violation(
        self,
        file: Path,
        line: int,
        name: str,
        source_package: str,
        current_package: str,
    ) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        return Violation(
            file=file,
            line=line,
            column=0,
            rule_id=self._meta.rule_id,
            rule_name=self._meta.rule_name,
            message=f"__all__ に別パッケージのシンボル `{name}` が含まれている（定義元: `{source_package}`）",
            reason=f"`{source_package}` で定義されたシンボルを `{current_package}` の公開 API として再エクスポートすると、パッケージ境界が曖昧になる",
            suggestion=f"`{name}` を __all__ から削除し、利用者が `from {source_package} import {name}` を直接使用するよう誘導してください",
        )
