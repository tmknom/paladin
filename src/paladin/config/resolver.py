"""解析対象パスの解決機能

CLI ターゲット引数と設定ファイルの include を統合して解析対象パスを決定する
TargetResolver を提供する。
"""

from pathlib import Path

from paladin.foundation.error import ApplicationError


class TargetResolver:
    """CLI 引数と設定ファイルの include を解決して解析対象パスを返す純粋計算クラス"""

    def resolve(
        self,
        targets: tuple[Path, ...],
        include: tuple[str, ...],
    ) -> tuple[Path, ...]:
        """CLI ターゲットと include を解決し、最終的な解析対象パスを返す

        解決ロジック:
        1. targets が空でない場合 → targets を返す
        2. include が空でない場合 → include の各パスを Path に変換して返す
        3. カレントディレクトリの src / tests の存在を確認し、存在するものを返す
        4. いずれも該当しない場合 → ApplicationError を送出する

        Args:
            targets: CLI から受け取ったターゲットパス群
            include: 設定ファイルの include パターン群

        Returns:
            解決済みの解析対象パスのタプル

        Raises:
            ApplicationError: CLI ターゲットも include も未指定で src / tests も存在しない場合
        """
        if targets:
            return targets

        if include:
            return tuple(Path(p) for p in include)

        defaults = tuple(p for p in (Path("src"), Path("tests")) if p.is_dir())
        if defaults:
            return defaults

        raise ApplicationError(
            message="解析対象が指定されていません。TARGET 引数か pyproject.toml の [tool.paladin] include を指定してください。",
            cause="no targets specified: neither CLI targets nor config include",
        )
