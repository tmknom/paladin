"""クラスの最大行数制限ルール"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation

_DEFAULT_MAX_LINES = 200
_DEFAULT_MAX_TEST_LINES = 400


@dataclass(frozen=True)
class ClassScope:
    """検査対象クラスの中間表現"""

    node: ast.ClassDef


class ClassCollector:
    """AST から検査対象クラスを再帰的に収集する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[ClassScope, ...]:
        """ast.Module から全 ClassDef を再帰的に収集する"""
        result: list[ClassScope] = []
        ClassCollector._collect_from_stmts(tree.body, result)
        return tuple(result)

    @staticmethod
    def _collect_from_stmts(stmts: list[ast.stmt], result: list[ClassScope]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.ClassDef):
                ClassCollector._collect_from_class(stmt, result)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ClassCollector._collect_from_stmts(stmt.body, result)

    @staticmethod
    def _collect_from_class(class_node: ast.ClassDef, result: list[ClassScope]) -> None:
        result.append(ClassScope(node=class_node))
        for stmt in class_node.body:
            if isinstance(stmt, ast.ClassDef):
                ClassCollector._collect_from_class(stmt, result)
            elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ClassCollector._collect_from_stmts(stmt.body, result)


class ClassLengthCalculator:
    """クラスの行数を算出する"""

    @staticmethod
    def calc(class_node: ast.ClassDef) -> int:
        """クラスの行数を返す（class 行からクラス本体の最終行まで、docstring 除外）"""
        assert class_node.end_lineno is not None
        total = class_node.end_lineno - class_node.lineno + 1
        return total - ClassLengthCalculator.calc_docstring_lines(class_node)

    @staticmethod
    def calc_docstring_lines(class_node: ast.ClassDef) -> int:
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


class ClassLengthDetector:
    """クラス行数の閾値判定を行う"""

    @staticmethod
    def detect(
        scope: ClassScope,
        length: int,
        limit: int,
        meta: RuleMeta,
        source_file: SourceFile,
    ) -> Violation | None:
        """Length が limit を超えた場合に Violation を返す。そうでなければ None を返す"""
        if length <= limit:
            return None
        message = f"クラス `{scope.node.name}` は `{length}` 行です。上限は `{limit}` 行です"
        return meta.create_violation_at(
            location=source_file.location(scope.node.lineno),
            message=message,
            reason="クラスが長すぎることは、責務の肥大化や設計上の問題を示す兆候です",
            suggestion="クラスの責務を分割し、複数のクラスに分離することを検討してください",
        )


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
        for scope in ClassCollector.collect(source_file.tree):
            length = ClassLengthCalculator.calc(scope.node)
            violation = ClassLengthDetector.detect(scope, length, limit, self._meta, source_file)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
