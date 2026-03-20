"""相対インポート禁止ルール

仕様は docs/rules/no-relative-import.md を参照。
"""

from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoRelativeImportRule:
    """相対インポート（from . import ...）の使用を AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-relative-import",
            rule_name="No Relative Import",
            summary="相対インポートの使用を禁止する",
            intent="依存関係を明示的にし、モジュール移動時の影響を局所化する",
            guidance="from .xxx import ... の形式が使われている箇所を確認する",
            suggestion="プロジェクトルートからの絶対インポートに書き換える",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if not stmt.is_relative:
                continue
            names_str = ", ".join(imported.name for imported in stmt.names)
            violations.append(
                self._meta.create_violation(
                    file=source_file.file_path,
                    line=stmt.line,
                    column=stmt.column,
                    message=f"相対インポートが使用されている（from {stmt.level_dots}{stmt.module_str} import ...）",
                    reason="相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる",
                    suggestion=f"`from {stmt.level_dots}{stmt.module_str} import {names_str}` をプロジェクトルートからの絶対インポートに書き換えてください",
                )
            )
        return tuple(violations)
