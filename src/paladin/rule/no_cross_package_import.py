"""許可ディレクトリ以外のパッケージからのクロスパッケージインポート禁止ルール

仕様は docs/rules/no-cross-package-import.md を参照。
"""

import ast
import sys

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.own_package_resolver import OwnPackageResolver
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class NoCrossPackageImportRule:
    """allow-dirs に含まれないパッケージからのクロスパッケージインポートを検出するルール"""

    def __init__(self, allow_dirs: tuple[str, ...] = ()) -> None:
        """ルールを初期化する

        Args:
            allow_dirs: クロスパッケージインポートを許可するディレクトリのパス
        """
        self._allow_dirs = tuple(d if d.endswith("/") else d + "/" for d in allow_dirs)
        self._resolver = PackageResolver()
        self._own_package_resolver = OwnPackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._stdlib_modules: frozenset[str] = sys.stdlib_module_names
        self._meta = RuleMeta(
            rule_id="no-cross-package-import",
            rule_name="No Cross Package Import",
            summary="許可ディレクトリ以外のパッケージからのクロスパッケージインポートを禁止する",
            intent="依存方向に制約を設けることで、アーキテクチャ境界の崩壊と変更影響範囲の拡大を防ぐ",
            guidance="allow-dirs 外のパッケージをインポートしている箇所を確認する",
            suggestion="インポート先パッケージを allow-dirs に追加するか、同一パッケージ内のモジュールを使うように変更してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def prepare(self, source_files: SourceFiles) -> None:
        """実行前の事前準備：source_files からルートパッケージを自動導出する"""
        self._root_packages = self._resolver.resolve_root_packages(source_files)

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if self._is_entrypoint(source_file):
            return ()

        own_packages = self._own_package_resolver.resolve(
            source_file.file_path, self._root_packages
        )
        if not own_packages:
            return ()
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if stmt.is_relative:
                continue
            if stmt.is_import_from and stmt.module is not None:
                self._check_from_import(stmt, stmt.module, source_file, own_packages, violations)
            elif not stmt.is_import_from:
                self._check_plain_import(stmt, source_file, own_packages, violations)
        return tuple(violations)

    def _is_entrypoint(self, source_file: SourceFile) -> bool:
        """トップレベルに def main() が定義されているかを判定する"""
        for node in source_file.tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                return True
        return False

    def _check_from_import(
        self,
        stmt: ImportStatement,
        import_module: ModulePath,
        source_file: SourceFile,
        own_packages: frozenset[str],
        violations: list[Violation],
    ) -> None:
        """From X import Y パターンの違反を収集する"""
        module_str = str(import_module)
        if not self._is_cross_package_import(import_module, own_packages):
            return
        for imported in stmt.names:
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location_from(stmt),
                    message=f"`from {module_str} import {imported.name}` は許可されていないクロスパッケージインポートである",
                    reason=f"`{module_str}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である",
                    suggestion=f"`{module_str}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください",
                )
            )

    def _check_plain_import(
        self,
        stmt: ImportStatement,
        source_file: SourceFile,
        own_packages: frozenset[str],
        violations: list[Violation],
    ) -> None:
        """Import X パターンの違反を収集する"""
        for imported in stmt.names:
            import_module = ModulePath(imported.name)
            if not self._is_cross_package_import(import_module, own_packages):
                continue
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location_from(stmt),
                    message=f"`import {imported.name}` は許可されていないクロスパッケージインポートである",
                    reason=f"`{imported.name}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である",
                    suggestion=f"`{imported.name}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください",
                )
            )

    def _is_cross_package_import(
        self,
        import_module: ModulePath,
        own_packages: frozenset[str],
    ) -> bool:
        """クロスパッケージインポートかどうかを判定する"""
        # 標準ライブラリは対象外
        top = import_module.top_level
        if top in self._stdlib_modules:
            return False
        # ルートパッケージに属さない（サードパーティ等）は対象外
        if top not in self._root_packages:
            return False

        # セグメントが1つのみ（ルートパッケージ自体のインポート）は対象外
        if import_module.depth < 2:
            return False

        # 同一パッケージ内のインポートは対象外（自パッケージセットに含まれるか比較）
        if import_module.package_key in own_packages:
            return False

        # allow-dirs に含まれるパッケージは対象外
        return not self._is_allowed_package(import_module)

    def _is_allowed_package(self, import_module: ModulePath) -> bool:
        """インポート先モジュールのパッケージパスが allow-dirs に前方一致するかを判定する

        呼び出し前に depth >= 2 が保証されているため、segments の長さは常に 2 以上である。
        """
        # 先頭2セグメントでパッケージキーを構築（src/<seg0>/<seg1>/）
        segments = import_module.segments
        pkg_path = "src/" + "/".join(segments[:2]) + "/"
        return any(pkg_path.startswith(allow_dir) for allow_dir in self._allow_dirs)
