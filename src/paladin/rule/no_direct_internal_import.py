"""内部モジュールへの直接インポート禁止ルール

仕様は docs/rules/no-direct-internal-import.md を参照。
"""

from pathlib import Path

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.import_statement import AbsoluteFromImport, ModulePath
from paladin.rule.own_package_resolver import OwnPackageResolver
from paladin.rule.package_resolver import NON_PACKAGE_DIRS, PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class NoDirectInternalImportRule:
    """他パッケージの内部モジュールへの直接インポートを検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._extractor = AllExportsExtractor()
        self._own_package_resolver = OwnPackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._meta = RuleMeta(
            rule_id="no-direct-internal-import",
            rule_name="No Direct Internal Import",
            summary="他パッケージの内部モジュールへの直接インポートを禁止する",
            intent="パッケージの公開 API を経由した依存を促し、内部実装への依存を排除する",
            guidance="from package.submodule.internal import Foo のような3階層以上のインポートを確認する",
            suggestion="パッケージの __init__.py を経由するインポートに書き換える",
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

        package_exports = self._build_package_exports(source_files)
        src_root = self._infer_src_root(source_files)
        violations: list[Violation] = []

        for source_file in source_files:
            violations.extend(self._check_file(source_file, package_exports, src_root))

        return tuple(violations)

    def _infer_src_root(self, source_files: SourceFiles) -> Path | None:
        """source_files のパスから src/ ディレクトリを推定する

        アンカー（src or tests）の親ディレクトリをプロジェクトルートとして算出し、
        <project_root>/src を返す。
        """
        for source_file in source_files:
            result = self._find_src_root(source_file.file_path)
            if result is not None:
                return result
        return None

    def _find_src_root(self, file_path: Path) -> Path | None:
        """1ファイルのパスから src/ ディレクトリを推定する"""
        parts = file_path.parts
        for i, part in enumerate(parts):
            if part not in NON_PACKAGE_DIRS:
                continue
            project_root = Path(*parts[:i]) if i > 0 else Path()
            src_root = project_root / "src"
            if src_root.is_dir():
                return src_root
        return None

    def _is_subpackage_on_filesystem(self, module: ModulePath, src_root: Path | None) -> bool:
        """Module に対応する src/ 配下のディレクトリに __init__.py が存在するかを確認する"""
        if src_root is None:
            return False
        package_dir = src_root.joinpath(*module.segments)
        return (package_dir / "__init__.py").is_file()

    def _build_package_exports(self, source_files: SourceFiles) -> dict[str, set[str]]:
        """__init__.py を解析して、パッケージパス -> 公開シンボルセットのマッピングを構築する

        キーは先頭2セグメントではなく正確なパッケージパス（全セグメント）を使用する。
        例: src/paladin/foundation/model/__init__.py -> "paladin.foundation.model"
        """
        package_exports: dict[str, set[str]] = {}

        for source_file in source_files.init_files():
            exact_key = self._resolver.resolve_exact_package_path(source_file.file_path)
            if exact_key is None:
                continue

            exports = self._extractor.extract_with_reexports(source_file)
            package_exports[exact_key] = exports

        return package_exports

    def _check_file(
        self,
        source_file: SourceFile,
        package_exports: dict[str, set[str]],
        src_root: Path | None = None,
    ) -> list[Violation]:
        """1ファイルの ImportFrom ノードを走査して違反を収集する"""
        violations: list[Violation] = []
        own_packages = self._own_package_resolver.resolve(
            source_file.file_path, self._root_packages
        )

        for imp in source_file.absolute_from_imports:
            if imp.module.depth < 3:  # 3階層未満は対象外
                continue

            if imp.module.top_level not in self._root_packages:
                continue

            import_package = imp.module.package_key

            # 同一パッケージ（またはテストの対応プロダクションパッケージ）は対象外
            if PackageResolver.is_own_package(import_package, own_packages):
                continue

            # インポートモジュール自体がサブパッケージ（__init__.py を持つ）なら対象外
            if imp.module.value in package_exports:
                continue
            if self._is_subpackage_on_filesystem(imp.module, src_root):
                continue

            violations.extend(
                self._check_imported_names(source_file, imp, import_package, package_exports)
            )

        return violations

    def _check_imported_names(
        self,
        source_file: SourceFile,
        imp: AbsoluteFromImport,
        import_package: str,
        package_exports: dict[str, set[str]],
    ) -> list[Violation]:
        """インポートの各 name を検査して違反リストを返す"""
        violations: list[Violation] = []
        for imported in imp.names:
            if self._should_report(imported.name, import_package, package_exports):
                violations.append(
                    self._make_violation(source_file, imp, imported.name, import_package)
                )
        return violations

    def _should_report(
        self,
        name: str,
        import_package: str,
        package_exports: dict[str, set[str]],
    ) -> bool:
        """違反として報告すべきかを判定する"""
        if import_package not in package_exports:
            # __init__.py が解析対象にない場合はヒューリスティック検出
            return True

        exports = package_exports[import_package]
        if not exports:
            # __init__.py が存在するがエクスポートが空の場合もヒューリスティック検出
            return True

        # __init__.py で公開されているシンボルのみを違反として報告
        return name in exports

    def _make_violation(
        self,
        source_file: SourceFile,
        imp: AbsoluteFromImport,
        name: str,
        package: str,
    ) -> Violation:
        """違反オブジェクトを生成する"""
        module_path = imp.module_str
        return self._meta.create_violation_at(
            location=source_file.location_from(imp),
            message=f"`from {module_path} import {name}` は内部モジュールへの直接参照である",
            reason=f"`{package}` の内部実装に直接依存しており、パッケージの公開 API を経由していない",
            suggestion=f"`from {module_path} import {name}` を `from {package} import {name}` に書き換えてください",
        )
