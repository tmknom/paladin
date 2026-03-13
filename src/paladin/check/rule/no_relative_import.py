"""no-relative-import ルールの実装"""

import ast

from paladin.check.rule.types import RuleMeta, Violation
from paladin.check.types import ParsedFile


class NoRelativeImportRule:
    """相対インポート（from . import ...）の使用を AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-relative-import",
            rule_name="No Relative Import",
            summary="相対インポートの使用を禁止する",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for node in ast.walk(parsed_file.tree):
            if isinstance(node, ast.ImportFrom) and node.level >= 1:
                level_dots = "." * node.level
                module = node.module or ""
                violations.append(
                    Violation(
                        file=parsed_file.file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        rule_id=self._meta.rule_id,
                        rule_name=self._meta.rule_name,
                        message=f"相対インポートが使用されている（from {level_dots}{module} import ...）",
                        reason="相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる",
                        suggestion="プロジェクトルートからの絶対インポートに書き換える（例：from myapp.services.data import DataLoader）",
                    )
                )
        return tuple(violations)
