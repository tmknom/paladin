"""Rule 層の静的解析ルール。許可ディレクトリ以外のパッケージからのクロスパッケージインポート禁止ルール。

仕様は docs/rules/no-cross-package-import.md を参照。
"""

import ast
import sys
from dataclasses import dataclass

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.own_package_resolver import OwnPackageResolver
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import DetectionContext, RuleMeta, SourceFile, SourceFiles, Violation


@dataclass(frozen=True)
class CheckConfig:
    """クロスパッケージインポート判定に必要なルール設定を集約する"""

    stdlib_modules: frozenset[str]
    root_packages: tuple[str, ...]
    allow_dirs: tuple[str, ...]


class EntrypointChecker:
    """エントリーポイントかどうかの判定を行う"""

    @staticmethod
    def is_entrypoint(tree: ast.Module) -> bool:
        """トップレベルに def main() が定義されているかを判定する"""
        return any(isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body)


class CrossPackageImportChecker:
    """クロスパッケージインポートかどうかの判定を行う"""

    @staticmethod
    def is_cross_package(
        import_module: ModulePath,
        own_packages: frozenset[str],
        config: CheckConfig,
    ) -> bool:
        """クロスパッケージインポートかどうかを判定する"""
        top = import_module.top_level
        if top in config.stdlib_modules:
            return False
        if top not in config.root_packages:
            return False
        if import_module.depth < 2:
            return False
        if import_module.package_key in own_packages:
            return False
        return not CrossPackageImportChecker._is_allowed_package(import_module, config.allow_dirs)

    @staticmethod
    def _is_allowed_package(import_module: ModulePath, allow_dirs: tuple[str, ...]) -> bool:
        """インポート先モジュールのパッケージパスが allow-dirs に前方一致するかを判定する

        呼び出し前に depth >= 2 が保証されているため、segments の長さは常に 2 以上である。
        allow-dirs には "src/paladin/foundation/" のような src/ 相対パスと
        "tests/fake/" のような tests/ 相対パスの両方を指定できる。
        """
        segments = import_module.segments
        pkg_path_src = "src/" + "/".join(segments[:2]) + "/"
        pkg_path_bare = "/".join(segments[:2]) + "/"
        return any(
            pkg_path_src.startswith(allow_dir) or pkg_path_bare.startswith(allow_dir)
            for allow_dir in allow_dirs
        )


class CrossPackageImportDetector:
    """クロスパッケージインポートの Violation を生成する"""

    @staticmethod
    def detect_from_import(
        stmt: ImportStatement,
        import_module: ModulePath,
        ctx: DetectionContext,
    ) -> list[Violation]:
        """From X import Y 形式の違反リストを返す"""
        module_str = str(import_module)
        violations: list[Violation] = []
        for imported in stmt.names:
            violations.append(
                ctx.meta.create_violation_at(
                    location=ctx.source_file.location_from(stmt),
                    message=f"`from {module_str} import {imported.name}` は許可されていないクロスパッケージインポートである",
                    reason=f"`{module_str}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である",
                    suggestion=f"`{module_str}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください",
                )
            )
        return violations

    @staticmethod
    def detect_plain_import(
        stmt: ImportStatement,
        imported_name: str,
        ctx: DetectionContext,
    ) -> Violation:
        """Import X 形式の違反を返す"""
        return ctx.meta.create_violation_at(
            location=ctx.source_file.location_from(stmt),
            message=f"`import {imported_name}` は許可されていないクロスパッケージインポートである",
            reason=f"`{imported_name}` は `allow-dirs` に含まれないパッケージのモジュールであり、同一パッケージ内からのみインポート可能である",
            suggestion=f"`{imported_name}` の利用を許可ディレクトリ配下に移動するか、`allow-dirs` にそのパッケージを追加してください",
        )


class NoCrossPackageImportRule:
    """allow-dirs に含まれないパッケージからのクロスパッケージインポートを検出するルール"""

    def __init__(self, allow_dirs: tuple[str, ...] = ()) -> None:
        """ルールを初期化する

        Args:
            allow_dirs: クロスパッケージインポートを許可するディレクトリのパス
        """
        self._resolver = PackageResolver()
        self._own_package_resolver = OwnPackageResolver()
        self._config = CheckConfig(
            stdlib_modules=sys.stdlib_module_names,
            root_packages=(),
            allow_dirs=tuple(d if d.endswith("/") else d + "/" for d in allow_dirs),
        )
        self._meta = RuleMeta(
            rule_id="no-cross-package-import",
            rule_name="No Cross Package Import",
            summary="許可ディレクトリ以外のパッケージからのクロスパッケージインポートを禁止する",
            intent="依存方向に制約を設けることで、アーキテクチャ境界の崩壊と変更影響範囲の拡大を防ぐ",
            guidance="allow-dirs 外のパッケージをインポートしている箇所を確認する",
            suggestion="インポート先パッケージを allow-dirs に追加するか、同一パッケージ内のモジュールを使うように変更してください",
            background="依存方向に制約がない状態では、パッケージ間の参照が無秩序に増加します。allow-dirs に許可するパッケージを明示することで、依存方向のアーキテクチャ制約を設定ファイルで宣言し自動検証できます。",
            steps=(
                "依存したいパッケージが allow-dirs に含まれているか確認する",
                "含まれていない場合は allow-dirs に追加するか、依存関係を整理して不要な参照を削除する",
            ),
            config_example='[tool.paladin.rule.no-cross-package-import]\nallow-dirs = ["src/myapp/foundation/", "src/myapp/models/"]',
            detection_example="# 違反: allow-dirs に含まれないパッケージへのクロスパッケージインポート\nfrom myapp.services import UserService  # 違反\n\n# 準拠: allow-dirs に含まれるパッケージへのインポート\nfrom myapp.foundation import BaseModel  # 準拠",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def prepare(self, source_files: SourceFiles) -> None:
        """実行前の事前準備：source_files からルートパッケージを自動導出する"""
        root_packages = self._resolver.resolve_root_packages(source_files)
        self._config = CheckConfig(
            stdlib_modules=self._config.stdlib_modules,
            root_packages=root_packages,
            allow_dirs=self._config.allow_dirs,
        )

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if EntrypointChecker.is_entrypoint(source_file.tree):
            return ()

        own_packages = self._own_package_resolver.resolve(
            source_file.file_path, self._config.root_packages
        )
        if not own_packages:
            return ()
        ctx = DetectionContext(meta=self._meta, source_file=source_file)
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if stmt.is_relative:
                continue
            if stmt.is_import_from and stmt.module is not None:
                violations.extend(self._check_from_import(stmt, own_packages, ctx))
            elif not stmt.is_import_from:
                violations.extend(self._check_plain_import(stmt, own_packages, ctx))
        return tuple(violations)

    def _check_from_import(
        self,
        stmt: ImportStatement,
        own_packages: frozenset[str],
        ctx: DetectionContext,
    ) -> list[Violation]:
        import_module = stmt.module
        assert import_module is not None
        if not CrossPackageImportChecker.is_cross_package(
            import_module, own_packages, self._config
        ):
            return []
        return CrossPackageImportDetector.detect_from_import(stmt, import_module, ctx)

    def _check_plain_import(
        self,
        stmt: ImportStatement,
        own_packages: frozenset[str],
        ctx: DetectionContext,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for imported in stmt.names:
            import_module = ModulePath(imported.name)
            if not CrossPackageImportChecker.is_cross_package(
                import_module, own_packages, self._config
            ):
                continue
            violations.append(
                CrossPackageImportDetector.detect_plain_import(stmt, imported.name, ctx)
            )
        return violations
