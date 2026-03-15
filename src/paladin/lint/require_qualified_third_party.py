"""サードパーティ完全修飾インポート要求ルール

仕様は docs/rules/require-qualified-third-party.md を参照。
"""

import ast
import sys

from paladin.lint.types import RuleMeta, SourceFile, Violation


class RequireQualifiedThirdPartyRule:
    """サードパーティライブラリの from X import Y およびエイリアスインポートを AST で検出するルール"""

    def __init__(self, root_packages: tuple[str, ...]) -> None:
        """ルールを初期化する"""
        self._root_packages = root_packages
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

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if isinstance(node, ast.ImportFrom):
                self._check_import_from(node, violations, source_file)
            elif isinstance(node, ast.Import):
                self._check_import_as(node, violations, source_file)
        return tuple(violations)

    def _check_import_from(
        self,
        node: ast.ImportFrom,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        if node.level >= 1:
            return
        if node.module is None:
            return  # pragma: no cover
        top = _top_level_name(node.module)
        if self._is_excluded(top):
            return
        for alias in node.names:
            violations.append(
                Violation(
                    file=source_file.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    rule_id=self._meta.rule_id,
                    rule_name=self._meta.rule_name,
                    message=f"`from {node.module} import {alias.name}` はサードパーティライブラリの直接インポートである",
                    reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
                    suggestion=f"`from {node.module} import {alias.name}` を `import {node.module}` に書き換え、使用箇所の `{alias.name}` を `{node.module}.{alias.name}` に置換してください",
                )
            )

    def _check_import_as(
        self,
        node: ast.Import,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        for alias in node.names:
            if alias.asname is None:
                continue
            top = _top_level_name(alias.name)
            if self._is_excluded(top):
                continue
            violations.append(
                Violation(
                    file=source_file.file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    rule_id=self._meta.rule_id,
                    rule_name=self._meta.rule_name,
                    message=f"`import {alias.name} as {alias.asname}` はサードパーティライブラリのエイリアスインポートである",
                    reason="外部依存の境界を明示するために、サードパーティライブラリは完全修飾名で使用する必要がある",
                    suggestion=f"`import {alias.name} as {alias.asname}` を `import {alias.name}` に書き換え、使用箇所の `{alias.asname}` を `{alias.name}` に置換してください",
                )
            )

    def _is_excluded(self, module_name: str) -> bool:
        """標準ライブラリまたはルートパッケージに該当するかを判定する"""
        if module_name in self._stdlib_modules:
            return True
        return module_name in self._root_packages


def _top_level_name(module_name: str) -> str:
    """ドット区切りのモジュール名から先頭部分を返す"""
    return module_name.split(".")[0]
