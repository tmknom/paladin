"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-nested-test-class.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "テストクラスのネストは可読性を下げます。テストはフラットな構造に保ってください"
_SUGGESTION = "ネストされたクラスをトップレベルのテストクラスとして独立させてください"


class NestedClassDetector:
    """ネストされたクラス定義から Violation を生成するヘルパー。検出ロジックは呼び出し側が担う"""

    @staticmethod
    def detect(
        outer_class: ast.ClassDef,
        inner_class: ast.ClassDef,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation:
        """ネストされたクラスに対して Violation を返す。呼び出し側で ClassDef 確認済みのため、確定的に Violation を生成する"""
        return meta.create_violation_at(
            location=source_file.location(line=inner_class.lineno),
            message=f"テストクラス `{outer_class.name}` の中にクラス `{inner_class.name}` がネストされています",
            reason=_REASON,
            suggestion=_SUGGESTION,
        )


class NoNestedTestClassRule:
    """テストクラス内にネストされたクラス定義を禁止するルール"""

    def __init__(self) -> None:
        """RuleMeta を初期化する"""
        self._meta = RuleMeta(
            rule_id="no-nested-test-class",
            rule_name="No Nested Test Class",
            summary="テストクラス内へのクラスのネストを禁止する",
            intent="テストクラスのネストは可読性を下げるため、フラットな構造を維持する",
            guidance="テストファイル内のトップレベルクラスの body に ClassDef が存在する場合に違反を検出する",
            suggestion=_SUGGESTION,
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """テストファイルのみを対象にネストされたクラスを検査する"""
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for outer_class in source_file.tree.body:
            if not isinstance(outer_class, ast.ClassDef):
                continue
            for inner_node in outer_class.body:
                if not isinstance(inner_node, ast.ClassDef):
                    continue
                violation = NestedClassDetector.detect(
                    outer_class, inner_node, self._meta, source_file
                )
                violations.append(violation)
        return tuple(violations)
