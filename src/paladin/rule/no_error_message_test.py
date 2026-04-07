"""Rule 層の単一ルール実装。ASTベースの静的解析で実装するルールはこの層に配置する。

仕様は docs/rules/no-error-message-test.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "例外メッセージの文言は実装の詳細です。文言の変更のたびにテストが壊れます"


class PytestRaisesMatchDetector:
    """`pytest.raises(match=...)` パターン専用の検出器。単一の検出パターンを1クラスに閉じ込め、`NoErrorMessageTestRule` と検出ロジックを分離する"""

    @staticmethod
    def detect(node: ast.Call, meta: RuleMeta, source_file: SourceFile) -> Violation | None:
        """pytest.raises に match 引数が指定されていれば Violation を返す。

        Flow:
            1. func が ast.Attribute でなければスキップ（メソッド呼び出し形式か確認）
            2. attr が "raises" でなければスキップ（pytest.raises 以外の呼び出しを除外）
            3. func.value が ast.Name かつ id が "pytest" でなければスキップ（pytest モジュールを確認）
            4. keywords に "match" が含まれなければスキップ
            5. match 引数あり → Violation を生成して返す
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
        has_match = any(kw.arg == "match" for kw in node.keywords)
        if not has_match:
            return None
        return meta.create_violation_at(
            location=source_file.location(line=node.lineno),
            message="`pytest.raises` に `match` 引数が指定されています",
            reason=_REASON,
            suggestion="`match` 引数を削除してください。例外の型のみを検証してください",
        )


class StrExcInfoValueDetector:
    """`str(exc_info.value)` パターン専用の検出器。単一の検出パターンを1クラスに閉じ込め、`NoErrorMessageTestRule` と検出ロジックを分離する"""

    @staticmethod
    def detect(node: ast.Call, meta: RuleMeta, source_file: SourceFile) -> Violation | None:
        """str(<name>.value) パターンを検出すれば Violation を返す。

        Flow:
            1. func が ast.Name でなければスキップ（関数呼び出し形式か確認）
            2. func.id が "str" でなければスキップ（str() 呼び出し以外を除外）
            3. 引数がなければスキップ
            4. 第1引数が ast.Attribute でなければスキップ（属性アクセス形式か確認）
            5. attr が "value" でなければスキップ（.value 属性以外を除外）
            6. attr.value が ast.Name でなければスキップ（変数からのアクセスか確認）
            7. 条件一致 → Violation を生成して返す
        """
        func = node.func
        if not isinstance(func, ast.Name):
            return None
        if func.id != "str":
            return None
        if not node.args:
            return None
        arg = node.args[0]
        if not isinstance(arg, ast.Attribute):
            return None
        if arg.attr != "value":
            return None
        if not isinstance(arg.value, ast.Name):
            return None
        return meta.create_violation_at(
            location=source_file.location(line=node.lineno),
            message="例外メッセージの文言を文字列で検証しています",
            reason=_REASON,
            suggestion="`str(exc_info.value)` による文字列比較を削除してください。例外の型のみを検証してください",
        )


class NoErrorMessageTestRule:
    """テスト内で例外メッセージの文言を検証するパターンを禁止するルール"""

    def __init__(self) -> None:
        """ルールメタ情報を初期化する"""
        self._meta = RuleMeta(
            rule_id="no-error-message-test",
            rule_name="No Error Message Test",
            summary="テスト内で例外メッセージの文言を検証するパターンを禁止する",
            intent="例外メッセージの文言は実装の詳細であり、テストが実装に密結合することを防止する",
            guidance="`pytest.raises(match=...)` の使用と `str(exc_info.value)` の文字列比較を検出する",
            suggestion="例外の型のみを検証してください。メッセージ文言のテストを削除してください",
            background="例外が発生することを確認するテストでは、例外の型を検証すれば十分です。例外メッセージの文言は実装の詳細であり、文言の改善があるたびに機能的には正しいコードに対してテストが失敗します。",
            steps=(
                "`pytest.raises(match=...)` の `match` 引数を削除する",
                "`str(exc_info.value)` による文字列比較を削除する",
                "例外の型のみを検証するテストに整理する",
            ),
            detection_example='# 違反: 例外メッセージの文言を検証している\nwith pytest.raises(ValueError, match="空文字列は無効です"):  # 違反\n    validate(invalid_value)\n\n# 準拠: 例外の型のみを検証する\nwith pytest.raises(ValueError):\n    validate(invalid_value)',
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """非テストファイルは即時スキップし、テストファイルのみ例外メッセージ文言テストを検査する"""
        if not source_file.is_test_file:
            return ()
        violations: list[Violation] = []
        for node in ast.walk(source_file.tree):
            if not isinstance(node, ast.Call):
                continue
            v = PytestRaisesMatchDetector.detect(node, self._meta, source_file)
            if v is not None:
                violations.append(v)
            v = StrExcInfoValueDetector.detect(node, self._meta, source_file)
            if v is not None:
                violations.append(v)
        return tuple(violations)
