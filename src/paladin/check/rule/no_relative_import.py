"""no-relative-import ルールの実装"""

import ast

from paladin.check.types import ParsedFile, RuleMeta, Violation

_RULE_ID = "no-relative-import"
_RULE_NAME = "No Relative Import"
_SUMMARY = "相対インポートの使用を禁止する"


class NoRelativeImportRule:
    """相対インポート（from . import ...）の使用を AST で検出するルール"""

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return RuleMeta(rule_id=_RULE_ID, rule_name=_RULE_NAME, summary=_SUMMARY)

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
                        rule_id=_RULE_ID,
                        rule_name=_RULE_NAME,
                        message=f"相対インポートが使用されている（from {level_dots}{module} import ...）",
                        reason="相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる",
                        suggestion="プロジェクトルートからの絶対インポートに書き換える（例：from myapp.services.data import DataLoader）",
                    )
                )
        return tuple(violations)
