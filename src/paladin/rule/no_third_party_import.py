"""許可ディレクトリ外でのサードパーティインポート禁止ルール

仕様は docs/rules/no-third-party-import.md を参照。
"""

import sys
from pathlib import Path

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class ThirdPartyChecker:
    """サードパーティライブラリかどうかの判定を行う"""

    @staticmethod
    def is_third_party(
        module_name: str,
        stdlib_modules: frozenset[str],
        root_packages: tuple[str, ...],
    ) -> bool:
        """標準ライブラリとルートパッケージを除いたサードパーティかを判定する"""
        if module_name in stdlib_modules:
            return False
        return module_name not in root_packages

    @staticmethod
    def is_allowed_path(file_path: Path, allow_dirs: tuple[str, ...]) -> bool:
        """ファイルパスが allow_dirs のいずれかに前方一致するかを判定する"""
        try:
            rel_str = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            rel_str = str(file_path)
        return any(rel_str.startswith(allow_dir) for allow_dir in allow_dirs)


class ThirdPartyImportDetector:
    """サードパーティインポートの Violation を生成する"""

    @staticmethod
    def detect_from_import(
        stmt: ImportStatement,
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> list[Violation]:
        """From X import Y 形式の違反リストを返す"""
        module_str = stmt.module_str
        violations: list[Violation] = []
        for imported in stmt.names:
            violations.append(
                meta.create_violation_at(
                    location=source_file.location_from(stmt),
                    message=f"`from {module_str} import {imported.name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
                    reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
                    suggestion=f"`{module_str}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
                )
            )
        return violations

    @staticmethod
    def detect_plain_import(
        stmt: ImportStatement,
        imported_name: str,
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> Violation:
        """Import X 形式の違反を返す"""
        return meta.create_violation_at(
            location=source_file.location_from(stmt),
            message=f"`import {imported_name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
            reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
            suggestion=f"`{imported_name}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
        )


class NoThirdPartyImportRule:
    """許可ディレクトリ以外でのサードパーティライブラリのインポートを検出するルール"""

    def __init__(self, allow_dirs: tuple[str, ...] = ()) -> None:
        """ルールを初期化する

        Args:
            allow_dirs: サードパーティインポートを許可するディレクトリのパス
        """
        self._allow_dirs = tuple(d if d.endswith("/") else d + "/" for d in allow_dirs)
        self._resolver = PackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._stdlib_modules: frozenset[str] = sys.stdlib_module_names
        self._meta = RuleMeta(
            rule_id="no-third-party-import",
            rule_name="No Third Party Import",
            summary="許可ディレクトリ以外でのサードパーティライブラリのインポートを禁止する",
            intent="サードパーティライブラリの利用を特定ディレクトリに集約し、外部依存の境界を明確にする",
            guidance="allow-dirs 外でサードパーティライブラリをインポートしている箇所を確認する",
            suggestion="サードパーティライブラリの利用を allow-dirs で指定されたディレクトリに移動するか、ラッパーモジュール経由でアクセスしてください",
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
        if ThirdPartyChecker.is_allowed_path(source_file.file_path, self._allow_dirs):
            return ()

        violations: list[Violation] = []
        for stmt in source_file.imports:
            if stmt.is_relative:
                continue
            if stmt.is_import_from:
                violations.extend(self._check_from_import(stmt, source_file))
            else:
                violations.extend(self._check_plain_import(stmt, source_file))
        return tuple(violations)

    def _check_from_import(
        self,
        stmt: ImportStatement,
        source_file: SourceFile,
    ) -> list[Violation]:
        top = stmt.top_level_module
        if top is None or not ThirdPartyChecker.is_third_party(
            top, self._stdlib_modules, self._root_packages
        ):
            return []
        return ThirdPartyImportDetector.detect_from_import(stmt, source_file, self._meta)

    def _check_plain_import(
        self,
        stmt: ImportStatement,
        source_file: SourceFile,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for imported in stmt.names:
            top = ModulePath(imported.name).top_level
            if not ThirdPartyChecker.is_third_party(top, self._stdlib_modules, self._root_packages):
                continue
            violations.append(
                ThirdPartyImportDetector.detect_plain_import(
                    stmt, imported.name, source_file, self._meta
                )
            )
        return violations
