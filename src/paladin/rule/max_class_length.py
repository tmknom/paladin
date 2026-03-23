"""クラスの最大行数制限ルール"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 200
_DEFAULT_MAX_TEST_LINES = 400


def _calc_class_docstring_lines(class_node: ast.ClassDef) -> int:
    """クラスの docstring の行数を返す。docstring がない場合は 0 を返す"""
    if not class_node.body:  # pragma: no cover
        return 0
    first = class_node.body[0]
    if not isinstance(first, ast.Expr):
        return 0
    if not isinstance(first.value, ast.Constant) or not isinstance(first.value.value, str):
        return 0
    end: int = first.end_lineno  # type: ignore[assignment]
    start: int = first.lineno  # type: ignore[assignment]
    return end - start + 1


def _calc_class_length(class_node: ast.ClassDef) -> int:
    """クラスの行数を返す（class 行からクラス本体の最終行まで、docstring 除外）"""
    assert class_node.end_lineno is not None
    total = class_node.end_lineno - class_node.lineno + 1
    return total - _calc_class_docstring_lines(class_node)


class MaxClassLengthRule:
    """クラスの行数が設定された上限を超えた場合に違反を検出するルール"""

    def __init__(
        self, max_lines: int = _DEFAULT_MAX_LINES, max_test_lines: int = _DEFAULT_MAX_TEST_LINES
    ) -> None:
        """ルールを初期化する"""
        self._max_lines = max_lines
        self._max_test_lines = max_test_lines
        self._meta = RuleMeta(
            rule_id="max-class-length",
            rule_name="Max Class Length",
            summary="単一クラスの行数が設定された上限を超えた場合に違反を検出する",
            intent="クラスの肥大化を防ぎ、単一責任原則を促進する",
            guidance="各クラスの行数を確認し、上限を超えていないか検査する",
            suggestion="クラスの責務を分割し、複数のクラスに分離することを検討してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        limit = self._max_test_lines if source_file.is_test_file else self._max_lines
        violations: list[Violation] = []
        self._visit_nodes(
            source_file.tree.body, limit=limit, violations=violations, source_file=source_file
        )
        return tuple(violations)

    def _visit_nodes(
        self,
        stmts: list[ast.stmt],
        limit: int,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """ステートメントリストからクラス・関数を探索する"""
        for stmt in stmts:
            if isinstance(stmt, ast.ClassDef):
                self._check_class(stmt, limit=limit, violations=violations, source_file=source_file)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_nodes(
                    stmt.body, limit=limit, violations=violations, source_file=source_file
                )

    def _check_class(
        self,
        class_node: ast.ClassDef,
        limit: int,
        violations: list[Violation],
        source_file: SourceFile,
    ) -> None:
        """クラスの行数を計算し、上限を超えていれば違反を追加する。ネストも再帰的に検査する"""
        length = _calc_class_length(class_node)

        if length > limit:
            message = f"クラス `{class_node.name}` は `{length}` 行です。上限は `{limit}` 行です"
            violations.append(
                self._meta.create_violation_at(
                    location=source_file.location(class_node.lineno),
                    message=message,
                    reason="クラスが長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
                    suggestion="クラスの責務を分割し、複数のクラスに分離することを検討してください",
                )
            )

        # クラス本体内のネストクラスと関数内クラスを再帰探索
        for stmt in class_node.body:
            if isinstance(stmt, ast.ClassDef):
                self._check_class(stmt, limit=limit, violations=violations, source_file=source_file)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_nodes(
                    stmt.body, limit=limit, violations=violations, source_file=source_file
                )
