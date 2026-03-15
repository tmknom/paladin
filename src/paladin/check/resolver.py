"""解析対象パスの解決機能

CLI ターゲット引数と設定ファイルの include を統合して解析対象パスを決定する
TargetResolver を提供する。
"""

from pathlib import Path

from paladin.check.context import CheckContext
from paladin.foundation.error.error import ApplicationError

__all__ = ["TargetResolver"]


class TargetResolver:
    """CLI 引数と設定ファイルの include を解決して解析対象パスを返す純粋計算クラス"""

    def resolve(self, context: CheckContext) -> tuple[Path, ...]:
        """CLI ターゲットと include を解決し、最終的な解析対象パスを返す

        解決ロジック:
        1. context.targets が空でない場合 → context.targets を返す
        2. context.include が空でない場合 → include の各パスを Path に変換して返す
        3. いずれも該当しない場合 → ApplicationError を送出する

        Args:
            context: Check 処理の実行時コンテキスト

        Returns:
            解決済みの解析対象パスのタプル

        Raises:
            ApplicationError: CLI ターゲットも include も未指定の場合
        """
        if context.targets:
            return context.targets

        if context.include:
            return tuple(Path(p) for p in context.include)

        raise ApplicationError(
            message="解析対象が指定されていません。TARGET 引数か pyproject.toml の [tool.paladin] include を指定してください。",
            cause="no targets specified: neither CLI targets nor config include",
        )
