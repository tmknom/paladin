"""メソッド/関数の最大行数制限ルール"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 50
_DEFAULT_MAX_TEST_LINES = 100


def _calc_length(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """関数/メソッドの行数を返す（def 行からメソッド本体の最終行まで）"""
    return func_node.end_lineno - func_node.lineno + 1  # type: ignore[operator]


class MaxMethodLengthRule:
    """メソッド/関数の行数が設定された上限を超えた場合に違反を検出するルール"""

    def __init__(
        self, max_lines: int = _DEFAULT_MAX_LINES, max_test_lines: int = _DEFAULT_MAX_TEST_LINES
    ) -> None:
        """ルールを初期化する"""
        self._max_lines = max_lines
        self._max_test_lines = max_test_lines
        self._meta = RuleMeta(
            rule_id="max-method-length",
            rule_name="Max Method Length",
            summary="単一メソッド/関数の行数が設定された上限を超えた場合に違反を検出する",
            intent="メソッド/関数の肥大化を防ぎ、単一責任原則を促進する",
            guidance="各メソッド/関数の行数を確認し、上限を超えていないか検査する",
            suggestion="メソッド/関数の処理を分割し、複数のプライベートメソッドや関数に分離することを検討してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        limit = self._max_test_lines if source_file.is_test_file else self._max_lines
        violations: list[Violation] = []
        self._visit_module(
            source_file.tree.body, limit=limit, violations=violations, source_file=source_file
        )
        return tuple(violations)

    def _visit_module(
        self,
        stmts: list[ast.stmt],
        limit: int,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """ステートメントリストからトップレベルの関数・クラスを探索する"""
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(
                    stmt,
                    class_name=None,
                    limit=limit,
                    violations=violations,
                    source_file=source_file,
                )
            elif isinstance(stmt, ast.ClassDef):
                self._visit_class(stmt, limit=limit, violations=violations, source_file=source_file)

    def _visit_class(
        self,
        class_node: ast.ClassDef,
        limit: int,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """クラス内のメソッドを検査する"""
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(
                    stmt,
                    class_name=class_node.name,
                    limit=limit,
                    violations=violations,
                    source_file=source_file,
                )
            elif isinstance(stmt, ast.ClassDef):
                self._visit_class(stmt, limit=limit, violations=violations, source_file=source_file)

    def _check_function(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        limit: int,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """関数/メソッドの行数を計算し、上限を超えていれば違反を追加する"""
        length = _calc_length(func_node)

        if length > limit:
            if class_name is not None:
                func_label = f"{class_name}.{func_node.name}"
            else:
                func_label = func_node.name
            message = f"メソッド/関数 `{func_label}` は `{length}` 行です。上限は `{limit}` 行です"
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location(func_node.lineno),
                    message=message,
                    reason="メソッド/関数が長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
                    suggestion="メソッド/関数の処理を分割し、複数のプライベートメソッドや関数に分離することを検討してください",
                )
            )

        # ネスト関数を独立スコープとして検査
        for stmt in func_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_function(
                    stmt,
                    class_name=None,
                    limit=limit,
                    violations=violations,
                    source_file=source_file,
                )
            elif isinstance(stmt, ast.ClassDef):
                self._visit_class(stmt, limit=limit, violations=violations, source_file=source_file)
