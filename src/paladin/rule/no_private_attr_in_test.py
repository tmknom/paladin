"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-private-attr-in-test.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "プライベート属性は実装の詳細です。リファクタリングのたびにテストが壊れます"
_SUGGESTION = (
    "公開メソッドの戻り値または Fake の呼び出し記録フィールドを通じて振る舞いを検証してください"
)


class PrivateAttrDetector:
    """`ast.Attribute` ノードからプライベート属性アクセスの違反を判定する検出器。

    Constraints:
        判定ロジックを `NoPrivateAttrInTestRule` から分離することで、
        各クラスの責務を単一に保ちテスト容易性を高める。
    """

    @staticmethod
    def detect(node: ast.Attribute, meta: RuleMeta, source_file: SourceFile) -> Violation | None:
        """プライベート属性アクセスであれば Violation を返す。

        Flow:
            1. attr が `_` で始まるか確認
            2. attr が `__` で始まる場合は除外（ダンダー）
            3. value が ast.Name(id="self") の場合は除外
            4. 条件一致 → Violation を生成して返す
        """
        attr = node.attr
        if not attr.startswith("_"):
            return None
        if attr.startswith("__"):
            return None
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return None
        return meta.create_violation_at(
            location=source_file.location(line=node.lineno),
            message=f"テストコード内でプライベート属性 `{attr}` に直接アクセスしています",
            reason=_REASON,
            suggestion=_SUGGESTION,
        )


class NoPrivateAttrInTestRule:
    """テストコード内でのプライベート属性への直接アクセスを禁止するルール"""

    def __init__(self) -> None:
        """ルールメタ情報を初期化する"""
        self._meta = RuleMeta(
            rule_id="no-private-attr-in-test",
            rule_name="No Private Attr In Test",
            summary="テストコード内でのプライベート属性への直接アクセスを禁止する",
            intent="テストが実装の内部詳細に依存することを防止し、リファクタリング耐性を高める",
            guidance="テスト対象オブジェクトのシングルアンダースコア属性 (_xxx) へのアクセスを検出する",
            suggestion=_SUGGESTION,
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """非テストファイルは即時スキップし、テストファイルのみプライベート属性アクセスを検査する"""
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.Attribute):
                continue
            v = PrivateAttrDetector.detect(node, self._meta, source_file)
            if v is not None:
                violations.append(v)
        return tuple(violations)
