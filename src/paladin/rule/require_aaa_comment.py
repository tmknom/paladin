"""Rule 層の単一ルール実装。テスト構造の強制を担う。

仕様は docs/rules/require-aaa-comment.md を参照。
"""

import ast
from dataclasses import dataclass

from paladin.rule.types import RuleMeta, SourceFile, Violation

_REASON = "AAA パターンのコメントがないと、テストの「実行」フェーズの境界が不明確になります"
_SUGGESTION = (
    "'# Arrange'、'# Act'、'# Assert' コメントを追加してください。"
    "Act と Assert が同時の場合は '# Act & Assert' を使用してください"
)


@dataclass(frozen=True)
class TargetMethod:
    """テストメソッドの中間表現"""

    name: str
    lineno: int
    end_lineno: int


class TargetMethodCollector:
    """AST から test_ プレフィックスのメソッドを列挙する"""

    @staticmethod
    def collect(tree: ast.Module) -> tuple[TargetMethod, ...]:
        """AST を再帰的に走査して test_ で始まる FunctionDef を収集する。ネストされたクラス内のメソッドも対象となる"""
        methods: list[TargetMethod] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                end_lineno = node.end_lineno if node.end_lineno is not None else node.lineno
                methods.append(
                    TargetMethod(name=node.name, lineno=node.lineno, end_lineno=end_lineno)
                )
        return tuple(methods)


class AaaCommentDetector:
    """ソーステキストの行範囲内に # Act コメントが存在するかを判定し、Violation を生成する"""

    @staticmethod
    def detect(method: TargetMethod, source_file: SourceFile, meta: RuleMeta) -> Violation | None:
        """テストメソッドの行範囲に `# Act` または `# Act & Assert` を含む行がなければ Violation を返す"""
        lines = source_file.source.splitlines()
        for line_index in range(method.lineno - 1, method.end_lineno):
            if line_index < len(lines) and "# Act" in lines[line_index]:
                return None
        return meta.create_violation_at(
            location=source_file.location(line=method.lineno),
            message=f"テストメソッド '{method.name}' に '# Act' コメントがありません",
            reason=_REASON,
            suggestion=_SUGGESTION,
        )


class RequireAaaCommentRule:
    """テストメソッドに AAA コメントの存在を要求するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="require-aaa-comment",
            rule_name="Require AAA Comment",
            summary="テストメソッドに AAA コメントの存在を要求する",
            intent="テストの構造を可視化し、AAA パターンの徹底を機械的に保証する",
            guidance="テストメソッドに '# Act' または '# Act & Assert' コメントが含まれているか確認する",
            suggestion=_SUGGESTION,
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """非テストファイルは即時スキップし、テストファイルのみ AAA コメントの欠如を検査する"""
        if not source_file.is_test_file:
            return ()
        methods = TargetMethodCollector.collect(source_file.tree)
        violations: list[Violation] = []
        for method in methods:
            violation = AaaCommentDetector.detect(method, source_file, self._meta)
            if violation is not None:
                violations.append(violation)
        return tuple(violations)
