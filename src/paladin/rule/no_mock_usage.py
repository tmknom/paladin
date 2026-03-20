"""Mock/MagicMock インポート禁止ルール

仕様は docs/rules/no-mock-usage.md を参照。
"""

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
        for stmt in source_file.imports:
            if stmt.is_import_from:
                if stmt.module_str == "unittest.mock":
                    for imported in stmt.names:
                        if imported.name in _FORBIDDEN_NAMES:
                            violations.append(
                                self._meta.create_violation_at(
                                    location=source_file.location_from(stmt),
                                    message=f"{imported.name} のインポートは禁止されています",
                                    reason=_REASON,
                                    suggestion=self._meta.suggestion,
                                )
                            )
            else:
                for imported in stmt.names:
                    if imported.name == "unittest.mock":
                        violations.append(
                            self._meta.create_violation_at(
                                location=source_file.location_from(stmt),
                                message="unittest.mock のインポートは禁止されています",
                                reason=_REASON,
                                suggestion=self._meta.suggestion,
                            )
                        )
        return tuple(violations)
