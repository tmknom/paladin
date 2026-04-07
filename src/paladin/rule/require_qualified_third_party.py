"""サードパーティ完全修飾インポート要求ルール

仕様は docs/rules/require-qualified-third-party.md を参照。
"""

import sys

from paladin.rule.import_statement import AbsoluteFromImport, ImportStatement, ModulePath
from paladin.rule.package_resolver import PackageResolver
from paladin.rule.types import RuleMeta, SourceFile, SourceFiles, Violation


class QualifiedThirdPartyDetector:
    """サードパーティの直接/エイリアスインポートの Violation を生成する"""

    @staticmethod
    def detect_from_import(
        imp: AbsoluteFromImport,
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> list[Violation]:
        """From X import Y 形式の違反リストを返す"""
        module_str = imp.module_str
        violations: list[Violation] = []
        for imported in imp.names:
            violations.append(
                meta.create_violation_at(
                    location=source_file.location_from(imp),
                    message=f"`from {module_str} import {imported.name}` はサードパーティライブラリの直接インポートである",
                    reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
                    suggestion=f"`from {module_str} import {imported.name}` を `import {module_str}` に書き換え、使用箇所の `{imported.name}` を `{module_str}.{imported.name}` に置換してください",
                )
            )
        return violations

    @staticmethod
    def detect_import_as(
        stmt: ImportStatement,
        imported_name: str,
        asname: str,
        source_file: SourceFile,
        meta: RuleMeta,
    ) -> Violation:
        """Import X as Y 形式の違反を返す"""
        return meta.create_violation_at(
            location=source_file.location_from(stmt),
            message=f"`import {imported_name} as {asname}` はサードパーティライブラリのエイリアスインポートである",
            reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
            suggestion=f"`import {imported_name} as {asname}` を `import {imported_name}` に書き換え、使用箇所の `{asname}` を `{imported_name}` に置換してください",
        )


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
            background="from requests import get のように名前を直接インポートすると、その名前がどのライブラリに由来するかがコード上から見えなくなります。完全修飾名で使用することで外部依存の境界をコード中で明示できます。",
            steps=(
                "`from X import Y` を `import X` に書き換える",
                "使用箇所の `Y` を `X.Y` の完全修飾名に置換する",
            ),
            detection_example="# 違反: サードパーティを from ... import で直接インポート\nfrom requests import get  # 違反\nresponse = get(...)\n\n# 準拠: モジュール名でインポートし完全修飾名で使用\nimport requests\nresponse = requests.get(...)",
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
        for imp in source_file.absolute_from_imports:
            top = imp.top_level
            if top in self._stdlib_modules or top in self._root_packages:
                continue
            violations.extend(
                QualifiedThirdPartyDetector.detect_from_import(imp, source_file, self._meta)
            )
        for stmt in source_file.imports:
            if not stmt.is_import_from:
                violations.extend(self._check_import_as(stmt, source_file))
        return tuple(violations)

    def _check_import_as(
        self,
        stmt: ImportStatement,
        source_file: SourceFile,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for imported in stmt.names:
            if not imported.has_alias or imported.asname is None:
                continue
            top = ModulePath(imported.name).top_level
            if top in self._stdlib_modules or top in self._root_packages:
                continue
            violations.append(
                QualifiedThirdPartyDetector.detect_import_as(
                    stmt,
                    imported.name,
                    imported.asname,
                    source_file,
                    self._meta,
                )
            )
        return violations
