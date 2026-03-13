"""require-all-export ルールの実装"""

import ast

from paladin.check.rule.types import RuleMeta, Violation
from paladin.check.types import ParsedFile


class RequireAllExportRule:
    """__init__.py に __all__ が定義されているかを AST で判定するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            summary="__init__.py に __all__ の定義を要求する",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

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
                rule_id=self._meta.rule_id,
                rule_name=self._meta.rule_name,
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
