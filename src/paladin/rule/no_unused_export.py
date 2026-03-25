"""__init__.py の __all__ に定義されたシンボルが別パッケージから利用されていないことを検出するルール

仕様は docs/rules/no-unused-export.md を参照。
"""

import ast
from pathlib import Path

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.import_statement import ModulePath, SourceLocation
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class ExportCollector:
    """全 __init__.py の __all__ からシンボルと行番号を収集する"""

    @staticmethod
    def collect(
        source_files: SourceFiles,
        resolver: PackageResolver,
        extractor: AllExportsExtractor,
    ) -> dict[str, tuple[Path, dict[str, int]]]:
        """全 __init__.py の __all__ からシンボルと行番号を収集する

        戻り値: {パッケージパス: (ファイルパス, {シンボル名: __all__ 代入文の行番号})}
        """
        result: dict[str, tuple[Path, dict[str, int]]] = {}

        for source_file in source_files.init_files():
            pkg_path = resolver.resolve_exact_package_path(source_file.file_path)
            if pkg_path is None:
                continue

            all_exports = extractor.extract(source_file)
            if not all_exports.has_exports:
                continue

            lineno = all_exports.lineno
            symbols: dict[str, int] = {name: lineno for name in all_exports}
            result[pkg_path] = (source_file.file_path, symbols)

        return result


class UsageCollector:
    """全ファイルから利用されているシンボルを収集する"""

    @staticmethod
    def collect(
        source_files: SourceFiles,
        all_exports: dict[str, tuple[Path, dict[str, int]]],
        resolver: PackageResolver,
    ) -> dict[str, set[str]]:
        """全ファイルから利用されているシンボルを収集する

        プロダクションコードの export はプロダクションコードからの利用のみカウントする。
        テストコードの export はテストコードからの利用もカウントする。

        戻り値: {パッケージパス: 利用されているシンボル名のセット}
        """
        usages: dict[str, set[str]] = {}
        for source_file in source_files:
            file_usages = UsageCollector._collect_from_file(source_file, all_exports, resolver)
            for pkg, symbols in file_usages.items():
                usages.setdefault(pkg, set()).update(symbols)
        return usages

    @staticmethod
    def _collect_from_file(
        source_file: SourceFile,
        all_exports: dict[str, tuple[Path, dict[str, int]]],
        resolver: PackageResolver,
    ) -> dict[str, set[str]]:
        """1ファイルの AST を走査して利用シンボルを収集して返す"""
        is_test_file = source_file.is_test_file
        user_pkg_key = resolver.resolve_package_key(source_file.file_path)
        user_exact_pkg = resolver.resolve_exact_package_path(source_file.file_path)
        effective_user_key = user_exact_pkg or user_pkg_key

        # AST を1回だけ走査して Import / ImportFrom / Attribute を同時に収集する
        all_nodes = list(ast.walk(source_file.tree))
        imported_modules = UsageCollector._collect_imported_module_names(all_nodes)

        usages: dict[str, set[str]] = {}
        for node in all_nodes:
            node_usages = UsageCollector._process_node(
                node, all_exports, imported_modules, is_test_file, effective_user_key
            )
            for pkg, symbols in node_usages.items():
                usages.setdefault(pkg, set()).update(symbols)
        return usages

    @staticmethod
    def _collect_imported_module_names(all_nodes: list[ast.AST]) -> set[str]:
        """Import 文から直接インポートされたモジュール名を収集する"""
        return {
            alias.name for node in all_nodes if isinstance(node, ast.Import) for alias in node.names
        }

    @staticmethod
    def _process_node(
        node: ast.AST,
        all_exports: dict[str, tuple[Path, dict[str, int]]],
        imported_modules: set[str],
        is_test_file: bool,
        effective_user_key: str | None,
    ) -> dict[str, set[str]]:
        """1 AST ノードを処理して利用シンボルの dict を返す"""
        if isinstance(node, ast.ImportFrom):
            return UsageCollector._process_import_from(
                node, all_exports, is_test_file, effective_user_key
            )
        if isinstance(node, ast.Attribute):
            return UsageCollector._process_attribute(
                node, all_exports, imported_modules, is_test_file, effective_user_key
            )
        return {}

    @staticmethod
    def _process_import_from(
        node: ast.ImportFrom,
        all_exports: dict[str, tuple[Path, dict[str, int]]],
        is_test_file: bool,
        effective_user_key: str | None,
    ) -> dict[str, set[str]]:
        """ImportFrom ノードを処理して利用シンボルの dict を返す"""
        if node.module is None or node.level != 0:
            return {}
        if node.module not in all_exports:
            return {}
        if is_test_file and not UsageCollector._is_test_export(node.module, all_exports):
            return {}
        if UsageCollector._is_same_or_sub_package(effective_user_key, node.module):
            return {}
        return {node.module: {alias.name for alias in node.names}}

    @staticmethod
    def _process_attribute(
        node: ast.Attribute,
        all_exports: dict[str, tuple[Path, dict[str, int]]],
        imported_modules: set[str],
        is_test_file: bool,
        effective_user_key: str | None,
    ) -> dict[str, set[str]]:
        """Attribute ノードを処理して利用シンボルの dict を返す"""
        module_name = UsageCollector._reconstruct_module_name(node.value)
        if module_name is None:
            return {}
        if module_name not in imported_modules:
            return {}
        if module_name not in all_exports:
            return {}
        if is_test_file and not UsageCollector._is_test_export(module_name, all_exports):
            return {}
        if UsageCollector._is_same_or_sub_package(effective_user_key, module_name):
            return {}
        return {module_name: {node.attr}}

    @staticmethod
    def _is_same_or_sub_package(user_pkg: str | None, export_pkg: str) -> bool:
        """利用元が export パッケージと同一か、そのサブパッケージかどうかを返す"""
        if user_pkg is None:
            return False
        return ModulePath(user_pkg).is_subpackage_of(ModulePath(export_pkg))

    @staticmethod
    def _is_test_export(module: str, all_exports: dict[str, tuple[Path, dict[str, int]]]) -> bool:
        """Export 元がテストコードかどうかを返す（呼び出し前に module の存在確認済みを前提とする）"""
        file_path = all_exports[module][0]
        return "tests" in file_path.parts

    @staticmethod
    def _reconstruct_module_name(node: ast.expr) -> str | None:
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


class UnusedExportDetector:
    """未使用エクスポートの判定と Violation 生成"""

    @staticmethod
    def detect(
        file_path: Path,
        symbols: dict[str, int],
        used_symbols: set[str],
        meta: RuleMeta,
    ) -> list[Violation]:
        """Symbols の中から未使用のものを違反として返す"""
        violations: list[Violation] = []
        for name, lineno in symbols.items():
            if name not in used_symbols:
                location = SourceLocation(file=file_path, line=lineno, column=0)
                violations.append(
                    meta.create_violation_at(
                        location=location,
                        message=f"`__all__` のシンボル `{name}` はどの別パッケージからも利用されていない",
                        reason="利用されていないシンボルを公開し続けると、不必要な後方互換義務が生じる",
                        suggestion=f"`{name}` を `__all__` から削除してください",
                    )
                )
        return violations


class NoUnusedExportRule:
    """__init__.py の __all__ に定義されたシンボルが別パッケージから利用されていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._extractor = AllExportsExtractor()
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

        all_exports = ExportCollector.collect(source_files, self._resolver, self._extractor)
        if not all_exports:
            return ()

        usages = UsageCollector.collect(source_files, all_exports, self._resolver)

        violations: list[Violation] = []
        for pkg_path, (file_path, symbols) in all_exports.items():
            used_symbols = usages.get(pkg_path, set())
            violations.extend(
                UnusedExportDetector.detect(file_path, symbols, used_symbols, self._meta)
            )

        return tuple(violations)
