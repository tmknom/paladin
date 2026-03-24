"""__init__.py 以外での __all__ 定義禁止ルール

仕様は docs/rules/no-non-init-all.md を参照。
"""

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.types import RuleMeta, SourceFile, Violation


class NoNonInitAllRule:
    """__init__.py 以外のファイルで __all__ が定義されていないかを AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._extractor = AllExportsExtractor()
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
        all_exports = self._extractor.extract(source_file)
        if not all_exports.is_defined:
            return ()
        return (NoNonInitAllRule._make_violation(self._meta, source_file, all_exports.lineno),)

    @staticmethod
    def _make_violation(meta: RuleMeta, source_file: SourceFile, line: int) -> Violation:
        return meta.create_violation_at(
            location=source_file.location(line),
            message="__init__.py 以外のファイルに __all__ が定義されている",
            reason=meta.intent,
            suggestion=meta.suggestion,
        )
