"""許可ディレクトリ外でのサードパーティインポート禁止ルール

仕様は docs/rules/no-third-party-import.md を参照。
"""

import sys
from pathlib import Path

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


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
        if self._is_allowed(source_file.file_path):
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
        violations: list[Violation] = []
        top = stmt.top_level_module
        if top is None or not self._is_third_party(top):
            return violations
        module_str = stmt.module_str
        for imported in stmt.names:
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location_from(stmt),
                    message=f"`from {module_str} import {imported.name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
                    reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
                    suggestion=f"`{module_str}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
                )
            )
        return violations

    def _check_plain_import(
        self,
        stmt: ImportStatement,
        source_file: SourceFile,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for imported in stmt.names:
            top = ModulePath(imported.name).top_level
            if not self._is_third_party(top):
                continue
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location_from(stmt),
                    message=f"`import {imported.name}` は許可ディレクトリ外でのサードパーティライブラリのインポートである",
                    reason="サードパーティライブラリの利用は `allow-dirs` で指定されたディレクトリに集約する必要がある",
                    suggestion=f"`{imported.name}` の利用を許可ディレクトリ配下に移動するか、ラッパーモジュール経由でアクセスしてください",
                )
            )
        return violations

    def _is_allowed(self, file_path: Path) -> bool:
        """ファイルパスが allow_dirs のいずれかに前方一致するかを判定する"""
        try:
            rel_str = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            rel_str = str(file_path)
        return any(rel_str.startswith(allow_dir) for allow_dir in self._allow_dirs)

    def _is_third_party(self, module_name: str) -> bool:
        """標準ライブラリとルートパッケージを除いたサードパーティかを判定する"""
        if module_name in self._stdlib_modules:
            return False
        return module_name not in self._root_packages
