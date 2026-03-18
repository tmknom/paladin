"""__init__.py の __all__ に定義されたシンボルが別パッケージから利用されていないことを検出するルール

仕様は docs/rules/no-unused-export.md を参照。
"""

import ast
from pathlib import Path

from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class NoUnusedExportRule:
    """__init__.py の __all__ に定義されたシンボルが別パッケージから利用されていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._meta = RuleMeta(
            rule_id="no-unused-export",
            rule_name="No Unused Export",
            summary="__init__.py の __all__ に定義したシンボルが別パッケージから利用されていないことを禁止する",
            intent="利用されていないシンボルを公開し続けると、不必要な後方互換義務が生じるためパブリック API を最小限に保つ",
            guidance="__init__.py の __all__ に列挙されているシンボルが他パッケージのコードから実際に参照されているか確認する",
            suggestion="利用されていないシンボルを __all__ から削除してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def prepare(self, source_files: SourceFiles) -> None:
        """実行前の事前準備：source_files からルートパッケージを自動導出する"""
        self._root_packages = self._resolver.resolve_root_packages(source_files)

    def check(self, source_files: SourceFiles) -> tuple[Violation, ...]:
        """複数ファイルに対する違反判定を行う"""
        if not self._root_packages:
            return ()

        all_exports = self._collect_all_exports(source_files)
        if not all_exports:
            return ()

        usages = self._collect_usages(source_files, all_exports)

        violations: list[Violation] = []
        for pkg_path, (file_path, symbols) in all_exports.items():
            used_symbols = usages.get(pkg_path, set())
            for name, node in symbols.items():
                if name not in used_symbols:
                    violations.append(self._make_violation(file_path, node, name))

        return tuple(violations)

    def _collect_all_exports(
        self, source_files: SourceFiles
    ) -> dict[str, tuple[Path, dict[str, ast.AST]]]:
        """全 __init__.py の __all__ からシンボルと AST ノードを収集する

        戻り値: {パッケージパス: (ファイルパス, {シンボル名: __all__ 代入文の AST ノード})}
        """
        result: dict[str, tuple[Path, dict[str, ast.AST]]] = {}

        for source_file in source_files:
            if source_file.file_path.name != "__init__.py":
                continue

            pkg_path = self._resolve_package_path(source_file.file_path)
            if pkg_path is None:
                continue

            symbols = self._extract_all_symbols(source_file)
            if symbols:
                result[pkg_path] = (source_file.file_path, symbols)

        return result

    def _extract_all_symbols(self, source_file: SourceFile) -> dict[str, ast.AST]:
        """__init__.py の AST から __all__ のシンボルと代入ノードを抽出する"""
        symbols: dict[str, ast.AST] = {}

        for node in source_file.tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not (isinstance(target, ast.Name) and target.id == "__all__"):
                continue
            if not isinstance(node.value, (ast.List, ast.Tuple)):
                continue
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    symbols[elt.value] = node

        return symbols

    def _collect_usages(
        self,
        source_files: SourceFiles,
        all_exports: dict[str, tuple[Path, dict[str, ast.AST]]],
    ) -> dict[str, set[str]]:
        """プロダクションコード全体から利用されているシンボルを収集する

        戻り値: {パッケージパス: 利用されているシンボル名のセット}
        """
        usages: dict[str, set[str]] = {}

        for source_file in source_files:
            # テストファイルは除外
            if self._is_test_file(source_file.file_path):
                continue

            # 利用元のパッケージキー
            user_pkg_key = self._resolve_package_key(source_file.file_path)

            # AST を1回だけ走査して Import / ImportFrom / Attribute を同時に収集する
            all_nodes = list(ast.walk(source_file.tree))

            # パターン2用: import 文からインポートされたモジュール名を収集する
            imported_modules: set[str] = set()
            for node in all_nodes:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name)

            for node in all_nodes:
                # パターン1: from paladin.check import Foo
                if isinstance(node, ast.ImportFrom):
                    if node.module is None or node.level != 0:
                        continue
                    if node.module not in all_exports:
                        continue

                    # 同一パッケージからの利用は除外
                    export_pkg_key = self._resolve_package_key_from_pkg_path(node.module)
                    if self._is_same_package(user_pkg_key, export_pkg_key):
                        continue

                    for alias in node.names:
                        usages.setdefault(node.module, set()).add(alias.name)

                # パターン2: paladin.check.CheckOrchestrator（属性アクセス）
                elif isinstance(node, ast.Attribute):
                    module_name = self._reconstruct_module_name(node.value)
                    if module_name is None:
                        continue
                    if module_name not in imported_modules:
                        continue
                    if module_name not in all_exports:
                        continue

                    # 同一パッケージからの利用は除外
                    export_pkg_key = self._resolve_package_key_from_pkg_path(module_name)
                    if self._is_same_package(user_pkg_key, export_pkg_key):
                        continue

                    usages.setdefault(module_name, set()).add(node.attr)

        return usages

    def _reconstruct_module_name(self, node: ast.expr) -> str | None:
        """ast.Attribute の value から a.b.c 形式のモジュール名を再構築する"""
        parts: list[str] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        else:
            return None
        return ".".join(reversed(parts))

    def _is_test_file(self, file_path: Path) -> bool:
        """ファイルが tests/ 配下かどうかを判定する"""
        return "tests" in file_path.parts

    def _resolve_package_path(self, file_path: Path) -> str | None:
        """__init__.py のファイルパスから正確なパッケージパスを取得する"""
        return self._resolver.resolve_exact_package_path(file_path)

    def _resolve_package_key(self, file_path: Path) -> str | None:
        """ファイルパスからパッケージキー（先頭2セグメント）を取得する"""
        return self._resolver.resolve_package_key(file_path)

    def _resolve_package_key_from_pkg_path(self, pkg_path: str) -> str:
        """パッケージパス文字列から先頭2セグメントのキーを返す

        呼び出し元で all_exports のキー（常に2セグメント以上）と一致チェック済みのため、
        1セグメントの pkg_path は渡されない。
        """
        segments = pkg_path.split(".")
        return ".".join(segments[:2])

    def _is_same_package(self, pkg_a: str | None, pkg_b: str | None) -> bool:
        """2つのパッケージキーが同一かどうかを判定する"""
        if pkg_a is None or pkg_b is None:
            return False
        return pkg_a == pkg_b

    def _make_violation(self, file_path: Path, node: ast.AST, name: str) -> Violation:
        """診断メッセージ仕様に従い Violation を生成する"""
        line = getattr(node, "lineno", 1)
        return Violation(
            file=file_path,
            line=line,
            column=0,
            rule_id=self._meta.rule_id,
            rule_name=self._meta.rule_name,
            message=f"`__all__` のシンボル `{name}` はどの別パッケージからも利用されていない",
            reason="利用されていないシンボルを公開し続けると、不必要な後方互換義務が生じる",
            suggestion=f"`{name}` を `__all__` から削除してください",
        )
