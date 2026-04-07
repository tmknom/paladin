"""__init__.py 以外での __all__ 定義禁止ルール

仕様は docs/rules/no-non-init-all.md を参照。
"""

from paladin.rule.all_exports_extractor import AllExportsExtractor
from paladin.rule.types import RuleMeta, SourceFile, Violation


class NonInitAllDetector:
    """__init__.py 以外での __all__ 定義の Violation を生成する"""

    @staticmethod
    def detect(meta: RuleMeta, source_file: SourceFile, line: int) -> Violation:
        """Violation を生成する"""
        return meta.create_violation_at(
            location=source_file.location(line),
            message="__init__.py 以外のファイルに __all__ が定義されている",
            reason=meta.intent,
            suggestion=meta.suggestion,
        )


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
            background="__all__ はパッケージの公開インタフェースを制御するための仕組みです。__init__.py 以外で定義すると、公開APIの定義が一か所に集まらず、__init__.py の __all__ がパッケージの唯一の公開API定義であるという設計原則が崩れます。",
            steps=(
                "__init__.py 以外のファイルの __all__ を削除する",
                "公開すべきシンボルをパッケージの __init__.py の __all__ に追加する",
            ),
            detection_example='# 違反: __init__.py 以外に __all__ が定義されている\n# myapp/services/user.py\n__all__ = ["UserService"]  # 違反\n\n# 準拠: __init__.py の __all__ で管理する\n# myapp/services/__init__.py\n__all__ = ["UserService"]',
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
        return (NonInitAllDetector.detect(self._meta, source_file, all_exports.lineno),)
