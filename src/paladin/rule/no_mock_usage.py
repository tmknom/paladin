"""Mock/MagicMock インポート禁止ルール

仕様は docs/rules/no-mock-usage.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_FORBIDDEN_NAMES = frozenset({"Mock", "MagicMock"})
_REASON = (
    "Mock/MagicMock は型チェッカーによる検証が効かず、インターフェース変更を見逃す可能性がある"
)


class NoMockUsageRule:
    """unittest.mock の Mock / MagicMock インポートを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-mock-usage",
            rule_name="No Mock Usage",
            summary="Mock/MagicMock のインポートを禁止する",
            intent="テストの型安全性を確保し、インターフェース変更への耐性を高める",
            guidance="from unittest.mock import Mock / MagicMock のインポート箇所を確認する",
            suggestion="Protocol を満たす Fake クラスを定義して代替してください",
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
                if node.module == "unittest.mock":
                    for alias in node.names:
                        if alias.name in _FORBIDDEN_NAMES:
                            violations.append(
                                Violation(
                                    file=source_file.file_path,
                                    line=node.lineno,
                                    column=node.col_offset,
                                    rule_id=self._meta.rule_id,
                                    rule_name=self._meta.rule_name,
                                    message=f"{alias.name} のインポートは禁止されています",
                                    reason=_REASON,
                                    suggestion=self._meta.suggestion,
                                )
                            )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "unittest.mock":
                        violations.append(
                            Violation(
                                file=source_file.file_path,
                                line=node.lineno,
                                column=node.col_offset,
                                rule_id=self._meta.rule_id,
                                rule_name=self._meta.rule_name,
                                message="unittest.mock のインポートは禁止されています",
                                reason=_REASON,
                                suggestion=self._meta.suggestion,
                            )
                        )
        return tuple(violations)
