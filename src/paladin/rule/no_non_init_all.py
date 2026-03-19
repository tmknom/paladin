"""__init__.py 以外での __all__ 定義禁止ルール

仕様は docs/rules/no-non-init-all.md を参照。
"""

import ast

from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoNonInitAllRule:
    """__init__.py 以外のファイルで __all__ が定義されていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-non-init-all",
            rule_name="No Non-Init All",
            summary="__init__.py 以外のファイルに __all__ を定義することを禁止する",
            intent="__all__ はパッケージの公開インタフェース定義であり、__init__.py のみで管理すべき",
            guidance="__init__.py 以外のファイルに __all__ の代入文が存在する箇所を確認する",
            suggestion="__all__ を削除してください。このモジュールのシンボルを公開する場合は、パッケージの __init__.py の __all__ に追加してください",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        if source_file.is_init_py:
            return ()
        for node in source_file.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        return (self._violation(source_file, node.lineno),)
            elif (
                isinstance(node, ast.AugAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
            ):
                return (self._violation(source_file, node.lineno),)
        return ()

    def _violation(self, source_file: SourceFile, line: int) -> Violation:
        return self._meta.create_violation(
            file=source_file.file_path,
            line=line,
            column=0,
            message="__init__.py 以外のファイルに __all__ が定義されている",
            reason=self._meta.intent,
            suggestion=self._meta.suggestion,
        )
