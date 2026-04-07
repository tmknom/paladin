"""相対インポート禁止ルール

仕様は docs/rules/no-relative-import.md を参照。
"""

from paladin.rule.import_statement import ImportStatement
from paladin.rule.types import RuleMeta, SourceFile, Violation


class RelativeImportDetector:
    """相対インポートの Violation を生成する"""

    @staticmethod
    def detect(stmt: ImportStatement, source_file: SourceFile, meta: RuleMeta) -> Violation:
        """相対インポートの Violation を生成する"""
        names_str = ", ".join(imported.name for imported in stmt.names)
        return meta.create_violation_at(
            location=source_file.location_from(stmt),
            message=f"相対インポートが使用されている（from {stmt.level_dots}{stmt.module_str} import ...）",
            reason="相対インポートは依存関係を不透明にし、モジュール移動時にインポートパスの修正が必要になる",
            suggestion=f"`from {stmt.level_dots}{stmt.module_str} import {names_str}` をプロジェクトルートからの絶対インポートに書き換えてください",
        )


class NoRelativeImportRule:
    """相対インポート（from . import ...）の使用を AST で検出するルール"""

    def __init__(self) -> None:
        """ルールを初期化する"""
        self._meta = RuleMeta(
            rule_id="no-relative-import",
            rule_name="No Relative Import",
            summary="相対インポートの使用を禁止する",
            intent="依存関係を明示的にし、モジュール移動時の影響を局所化する",
            guidance="from .xxx import ... の形式が使われている箇所を確認する",
            suggestion="プロジェクトルートからの絶対インポートに書き換える",
            background="相対インポートはモジュール間の依存関係を暗黙的にします。どのパッケージに依存しているかをファイル単体で把握できず、モジュールを別のパッケージへ移動した場合に相対インポートをすべて書き直す必要があります。絶対インポートを強制することで依存関係を明示的に保ちます。",
            steps=(
                "相対インポートのドット数とモジュール名からプロジェクトルートからの絶対パスを計算する",
                "相対インポートを絶対インポートに書き換える",
            ),
            detection_example="# 違反: 相対インポートを使用している\nfrom . import DataLoader  # 違反\nfrom ..error import ApplicationError  # 違反\n\n# 準拠: 絶対インポートを使用する\nfrom myapp.services.data import DataLoader\nfrom myapp.services.error import ApplicationError",
        )

    @property
    def meta(self) -> RuleMeta:
        """ルールのメタ情報を返す"""
        return self._meta

    def check(self, source_file: SourceFile) -> tuple[Violation, ...]:
        """単一ファイルに対する違反判定を行う"""
        violations: list[Violation] = []
        for stmt in source_file.imports:
            if not stmt.is_relative:
                continue
            violations.append(RelativeImportDetector.detect(stmt, source_file, self._meta))
        return tuple(violations)
