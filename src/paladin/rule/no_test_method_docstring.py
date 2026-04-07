"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-test-method-docstring.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = (
    "テストメソッドの目的はメソッド名で表現します。docstring があると名前との二重管理が発生します"
)
_SUGGESTION = "docstring を削除し、テストの目的がメソッド名だけで伝わるよう名前を改善してください"


class TestMethodDocstringDetector:
    """`NoTestMethodDocstringRule` から docstring 判定ロジックを分離した検出器。ASTノード単位の判定を単体テスト可能にするために独立させている。"""

    @staticmethod
    def detect(node: ast.FunctionDef, meta: RuleMeta, source_file: SourceFile) -> Violation | None:
        """Docstring が存在すれば Violation を返す。"""
        if not node.body:
            return None
        first = node.body[0]
        if not isinstance(first, ast.Expr):
            return None
        if not isinstance(first.value, ast.Constant):
            return None
        if not isinstance(first.value.value, str):
            return None
        return meta.create_violation_at(
            location=source_file.location(line=node.lineno),
            message=f"テストメソッド `{node.name}` に docstring が記述されています",
            reason=_REASON,
            suggestion=_SUGGESTION,
        )


class NoTestMethodDocstringRule:
    """Rule 層の公開エントリポイント。`TestMethodDocstringDetector` に判定を委譲し、ファイル単位の走査を担う。"""

    def __init__(self) -> None:
        """RuleMeta を初期化する"""
        self._meta = RuleMeta(
            rule_id="no-test-method-docstring",
            rule_name="No Test Method Docstring",
            summary="テストメソッドへの docstring の記述を禁止する",
            intent="テストメソッドの目的はメソッド名で表現する。docstring があると名前との二重管理が発生する",
            guidance="テストファイル内の test_ プレフィックスを持つメソッドに docstring が存在する場合に違反を検出する",
            suggestion=_SUGGESTION,
            background="テストメソッド名は `test_<対象>_<系統>_<期待する振る舞い>` の形式で自己説明的になるよう設計されます。docstring はメソッド名との二重管理になり、乖離が生じると読み手を混乱させます。",
            steps=(
                "テストメソッドの docstring を削除する",
                "テストの目的がメソッド名だけで伝わるよう、必要に応じてメソッド名を改善する",
            ),
            detection_example='# 違反: テストメソッドに docstring がある\ndef test_正常系_violationsを返す(self) -> None:\n    """正常にファイルを解析し、違反を返すことを確認する"""  # 違反\n    ...\n\n# 準拠: docstring なし\ndef test_正常系_violationsを返す(self) -> None:\n    ...',
        )

    @property
    def meta(self) -> RuleMeta:
        """RuleMeta を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """テストファイル内の test_ メソッドを走査し、docstring を持つものを違反として返す。

        Constraints:
            - 非テストファイルは即時スキップする（テストファイルのみを対象とする）
            - ast.walk によるネスト走査でクラス内メソッドも漏れなく検出する
        """
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("test_"):
                continue
            v = TestMethodDocstringDetector.detect(node, self._meta, source_file)
            if v is not None:
                violations.append(v)
        return tuple(violations)
