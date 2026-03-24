"""メソッド/関数の最大行数制限ルール"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 50
_DEFAULT_MAX_TEST_LINES = 100


@dataclass(frozen=True)
class FunctionScope:
    """検査対象関数/メソッドの中間表現"""

    node: ast.FunctionDef | ast.AsyncFunctionDef
    class_name: str | None


class FunctionCollector:
    """AST から検査対象関数/メソッドを再帰的に収集する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[FunctionScope, ...]:
        """ast.Module から全 FunctionDef / AsyncFunctionDef を再帰的に収集する"""
        result: list[FunctionScope] = []
        FunctionCollector._collect_from_stmts(tree.body, class_name=None, result=result)
        return tuple(result)

    @staticmethod
    def _collect_from_stmts(
        stmts: list[ast.stmt], class_name: str | None, result: list[FunctionScope]
    ) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, class_name=class_name, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_class(class_node: ast.ClassDef, result: list[FunctionScope]) -> None:
        for stmt in class_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(
                    stmt, class_name=class_node.name, result=result
                )
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)

    @staticmethod
    def _collect_from_function(
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str | None,
        result: list[FunctionScope],
    ) -> None:
        result.append(FunctionScope(node=func_node, class_name=class_name))
        for stmt in func_node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                FunctionCollector._collect_from_function(stmt, class_name=None, result=result)
            elif isinstance(stmt, ast.ClassDef):
                FunctionCollector._collect_from_class(stmt, result=result)


class MethodLengthCalculator:
    """メソッド/関数の行数を算出する"""

    @staticmethod
    def calc(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """関数/メソッドの行数を返す（def 行からメソッド本体の最終行まで、docstring 除外）"""
        assert func_node.end_lineno is not None
        total = func_node.end_lineno - func_node.lineno + 1
        return total - MethodLengthCalculator.calc_docstring_lines(func_node)

    @staticmethod
    def calc_docstring_lines(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
        """関数/メソッドの docstring の行数を返す。docstring がない場合は 0 を返す"""
        if not func_node.body:  # pragma: no cover
            return 0
        first = func_node.body[0]
        if not isinstance(first, ast.Expr):
            return 0
        if not isinstance(first.value, ast.Constant) or not isinstance(first.value.value, str):
            return 0
        end: int = first.end_lineno  # type: ignore[assignment]
        start: int = first.lineno  # type: ignore[assignment]
        return end - start + 1


class MethodLengthDetector:
    """メソッド行数の閾値判定を行う"""

    @staticmethod
    def detect(
        scope: FunctionScope,
        length: int,
        limit: int,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation | None:
        """Length が limit を超えた場合に Violation を返す。そうでなければ None を返す"""
        if length <= limit:
            return None
        if scope.class_name is not None:
            func_label = f"{scope.class_name}.{scope.node.name}"
        else:
            func_label = scope.node.name
        message = f"メソッド/関数 `{func_label}` は `{length}` 行です。上限は `{limit}` 行です"
        return meta.create_violation_at(
            location=source_file.location(scope.node.lineno),
            message=message,
            reason="メソッド/関数が長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
            suggestion="メソッド/関数の処理を分割し、複数のプライベートメソッドや関数に分離することを検討してください",
        )


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
        for scope in FunctionCollector.collect(source_file.tree):
            length = MethodLengthCalculator.calc(scope.node)
            violation = MethodLengthDetector.detect(scope, length, limit, self._meta, source_file)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
