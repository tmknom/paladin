"""ディレクトリ別設定のオーバーライド解決

[[tool.paladin.overrides]] セクションで定義されたオーバーライドを
ファイルパスに対して照合し、後勝ちロジックで最終的な rules を返す。
"""

from pathlib import Path, PurePath

from paladin.rule import OverrideEntry


class OverrideResolver:
    """ファイルパスに対してオーバーライドの後勝ち解決を行う純粋計算クラス

    glob パターンの照合には PurePath.full_match() を使用する。
    相対パターンには自動的に "**/" を前置して絶対パスにもマッチできるようにする。
    """

    def _normalize_glob_pattern(self, pattern: str) -> str:
        if pattern.startswith("/") or pattern.startswith("**/"):
            return pattern
        return "**/" + pattern

    def _matches_any_pattern(self, patterns: tuple[str, ...], file_path: Path) -> bool:
        """ファイルパスがパターンのいずれかにマッチするかを返す"""
        for pattern in patterns:
            normalized = self._normalize_glob_pattern(pattern)
            if PurePath(file_path).full_match(normalized):
                return True
        return False

    def resolve(
        self,
        overrides: tuple[OverrideEntry, ...],
        file_path: Path,
        base_rules: dict[str, bool],
    ) -> dict[str, bool]:
        """ファイルパスに対してオーバーライドを解決し、最終的な rules を返す

        overrides を先頭から順にイテレートし、最後にマッチしたオーバーライドの
        rules のみを base_rules にマージして返す（後勝ちロジック）。

        Args:
            overrides: オーバーライドエントリのタプル
            file_path: 照合対象のファイルパス
            base_rules: トップレベルのルール有効/無効設定

        Returns:
            マージ後の rules dict。マッチしない場合は base_rules をそのまま返す
        """
        last_match: OverrideEntry | None = None
        for override in overrides:
            if self._matches_any_pattern(override.files, file_path):
                last_match = override

        if last_match is None:
            return base_rules

        return {**base_rules, **last_match.rules}
