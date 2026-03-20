"""サードパーティ完全修飾インポート要求ルール

仕様は docs/rules/require-qualified-third-party.md を参照。
"""

import sys

from paladin.rule.import_statement import ImportStatement, ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class RequireQualifiedThirdPartyRule:
    """サードパーティライブラリの from X import Y およびエイリアスインポートを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._resolver = PackageResolver()
        self._root_packages: tuple[str, ...] = ()
        self._stdlib_modules: frozenset[str] = sys.stdlib_module_names
        self._meta = RuleMeta(
            rule_id="require-qualified-third-party",
            rule_name="Require Qualified Third Party",
            summary="サードパーティライブラリの直接インポートとエイリアスインポートを禁止する",
            intent="外部依存の境界を明示し、サードパーティライブラリの使用箇所を追跡可能にする",
            guidance="from X import Y や import X as Y の形式でサードパーティが使われている箇所を確認する",
            suggestion="import X の完全修飾インポートに書き換え、使用箇所を X.Y 形式に修正する",
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
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if stmt.is_import_from:
                self._check_import_from(stmt, violations, source_file)
            else:
                self._check_import_as(stmt, violations, source_file)
        return tuple(violations)

    def _check_import_from(
        self,
        stmt: ImportStatement,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        if stmt.is_relative:
            return
        if not stmt.has_module:
            return  # pragma: no cover
        top = stmt.top_level_module
        if top is None or self._is_excluded(top):
            return
        module_str = stmt.module_str
        for imported in stmt.names:
            violations.append(
                self._meta.create_violation(
                    file=source_file.file_path,
                    line=stmt.line,
                    column=stmt.column,
                    message=f"`from {module_str} import {imported.name}` はサードパーティライブラリの直接インポートである",
                    reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
                    suggestion=f"`from {module_str} import {imported.name}` を `import {module_str}` に書き換え、使用箇所の `{imported.name}` を `{module_str}.{imported.name}` に置換してください",
                )
            )

    def _check_import_as(
        self,
        stmt: ImportStatement,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        for imported in stmt.names:
            if not imported.has_alias:
                continue
            top = ModulePath(imported.name).top_level
            if self._is_excluded(top):
                continue
            violations.append(
                self._meta.create_violation(
                    file=source_file.file_path,
                    line=stmt.line,
                    column=stmt.column,
                    message=f"`import {imported.name} as {imported.asname}` はサードパーティライブラリのエイリアスインポートである",
                    reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
                    suggestion=f"`import {imported.name} as {imported.asname}` を `import {imported.name}` に書き換え、使用箇所の `{imported.asname}` を `{imported.name}` に置換してください",
                )
            )

    def _is_excluded(self, module_name: str) -> bool:
        """標準ライブラリまたはルートパッケージに該当するかを判定する"""
        if module_name in self._stdlib_modules:
            return True
        return module_name in self._root_packages
