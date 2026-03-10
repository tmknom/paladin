"""require-all-export ルールの実装"""

import ast

from paladin.check.types import ParsedFile, RuleMeta, Violation

_RULE_ID = "require-all-export"
_RULE_NAME = "Require __all__ Export"
_SUMMARY = "__init__.py に __all__ の定義を要求する"


class RequireAllExportRule:
    """__init__.py に __all__ が定義されているかを AST で判定するルール"""

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return RuleMeta(rule_id=_RULE_ID, rule_name=_RULE_NAME, summary=_SUMMARY)

    def check(self, parsed_file: ParsedFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if parsed_file.file_path.name != "__init__.py":
            return ()
        if not self._has_substantial_code(parsed_file.tree):
            return ()
        if self._has_all_definition(parsed_file.tree):
            return ()
        return (
            Violation(
                file=parsed_file.file_path,
                line=1,
                column=0,
                rule_id=_RULE_ID,
                rule_name=_RULE_NAME,
                message="__init__.py に __all__ が定義されていない",
                reason="__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある",
                suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
            ),
        )

    def _has_substantial_code(self, tree: ast.Module) -> bool:
        """実質的なコード（コメント・docstring以外）が存在するか判定する"""
        for node in tree.body:
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                # docstring はスキップ
                continue
            return True
        return False

    def _has_all_definition(self, tree: ast.Module) -> bool:
        """トップレベルに __all__ の代入が存在するか判定する"""
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        return True
            elif (
                isinstance(node, ast.AugAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
            ):
                return True
        return False
