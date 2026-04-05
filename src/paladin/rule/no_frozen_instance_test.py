"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-frozen-instance-test.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "`frozen=True` の不変性は pyright が静的に検証します。ランタイムテストで重複検証する必要はありません"


class FrozenInstanceTestDetector:
    """`pytest.raises(FrozenInstanceError)` パターン専用の検出器。単一の検出パターンをカプセル化し、ルールクラスと検出ロジックを分離する"""

    @staticmethod
    def detect(node: ast.Call, meta: RuleMeta, source_file: SourceFile) -> Violation | None:
        """pytest.raises の第1引数が FrozenInstanceError であれば Violation を返す。

        Flow:
            1. func が ast.Attribute でなければスキップ（メソッド呼び出し形式か確認）
            2. attr が "raises" でなければスキップ（pytest.raises 以外の呼び出しを除外）
            3. func.value が ast.Name かつ id が "pytest" でなければスキップ（pytest モジュールを確認）
            4. args が空なら スキップ
            5. args[0] が ast.Attribute かつ attr が "FrozenInstanceError" → 違反（dataclasses.FrozenInstanceError）
            6. args[0] が ast.Name かつ id が "FrozenInstanceError" → 違反（直接インポートのケース）
            7. いずれでもなければ None
        """
        func = node.func
        if not isinstance(func, ast.Attribute):
            return None
        if func.attr != "raises":
            return None
        if not isinstance(func.value, ast.Name):
            return None
        if func.value.id != "pytest":
            return None
        if not node.args:
            return None
        arg = node.args[0]
        if isinstance(arg, ast.Attribute) and arg.attr == "FrozenInstanceError":
            return meta.create_violation_at(
                location=source_file.location(line=node.lineno),
                message="`FrozenInstanceError` のテストは不要です",
                reason=_REASON,
                suggestion="このテストを削除してください。不変性の保証は pyright に委ねてください",
            )
        if isinstance(arg, ast.Name) and arg.id == "FrozenInstanceError":
            return meta.create_violation_at(
                location=source_file.location(line=node.lineno),
                message="`FrozenInstanceError` のテストは不要です",
                reason=_REASON,
                suggestion="このテストを削除してください。不変性の保証は pyright に委ねてください",
            )
        return None


class NoFrozenInstanceTestRule:
    """テスト内で `FrozenInstanceError` を `pytest.raises` で検証するパターンを禁止するルール"""

    def __init__(self) -> None:
        """ルールメタ情報を初期化する"""
        self._meta = RuleMeta(
            rule_id="no-frozen-instance-test",
            rule_name="No Frozen Instance Test",
            summary="`FrozenInstanceError` を検証するテストを禁止する",
            intent="frozen dataclass の不変性は pyright が静的に保証するため、ランタイムテストでの重複検証を防止する",
            guidance="`pytest.raises(FrozenInstanceError)` および `pytest.raises(dataclasses.FrozenInstanceError)` のパターンを検出する",
            suggestion="このテストを削除してください。不変性の保証は pyright に委ねてください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """テストファイルのみを対象に FrozenInstanceError テストを検査する。

        プロダクションコードに `pytest.raises(FrozenInstanceError)` が現れることはないため、
        テストファイルに限定することで不要な解析コストを排除する。
        """
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.Call):
                continue
            v = FrozenInstanceTestDetector.detect(node, self._meta, source_file)
            if v is not None:
                violations.append(v)
        return tuple(violations)
