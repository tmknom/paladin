"""解析対象パスの解決・除外機能

CLI ターゲット引数と設定ファイルの include を統合して解析対象パスを決定する
TargetResolver と、exclude パターンに基づいてファイルを除外する PathExcluder を提供する。
"""

from pathlib import Path, PurePath

from paladin.check.config import ProjectConfig
from paladin.check.context import CheckContext
from paladin.check.types import TargetFiles
from paladin.foundation.error.error import ApplicationError

__all__ = ["PathExcluder", "TargetResolver"]


class TargetResolver:
    """CLI 引数と設定ファイルの include を解決して解析対象パスを返す純粋計算クラス"""

    def resolve(self, context: CheckContext, config: ProjectConfig) -> tuple[Path, ...]:
        """CLI ターゲットと include を解決し、最終的な解析対象パスを返す

        解決ロジック:
        1. context.has_cli_targets が True の場合 → context.targets を返す
        2. config.include が空でない場合 → include の各パスを Path に変換して返す
        3. いずれも該当しない場合 → ApplicationError を送出する

        Args:
            context: Check 処理の実行時コンテキスト
            config: プロジェクト設定

        Returns:
            解決済みの解析対象パスのタプル

        Raises:
            ApplicationError: CLI ターゲットも include も未指定の場合
        """
        if context.has_cli_targets:
            return context.targets

        if config.include:
            return tuple(Path(p) for p in config.include)

        raise ApplicationError(
            message="解析対象が指定されていません。TARGET 引数か pyproject.toml の [tool.paladin] include を指定してください。",
            cause="no targets specified: neither CLI targets nor config include",
        )


class PathExcluder:
    """exclude パターンに基づいてファイルパスを除外する純粋計算クラス"""

    def exclude(self, files: TargetFiles, patterns: tuple[str, ...]) -> TargetFiles:
        """Exclude パターンにマッチするファイルを除外した TargetFiles を返す

        Args:
            files: フィルタリング対象のファイル群
            patterns: 除外パターンのタプル（glob パターン可）

        Returns:
            マッチしなかったファイルのみを含む TargetFiles
        """
        if not patterns:
            return files

        normalized = [self._normalize_exclude_pattern(p) for p in patterns]

        kept = tuple(
            f for f in files.files if not any(PurePath(str(f)).full_match(p) for p in normalized)
        )
        return TargetFiles(files=kept)

    def _normalize_glob_pattern(self, pattern: str) -> str:
        if pattern.startswith("/") or pattern.startswith("**/"):
            return pattern
        return "**/" + pattern

    def _normalize_exclude_pattern(self, pattern: str) -> str:
        """Exclude パターンを正規化する

        末尾スラッシュがある場合、または拡張子なしかつパス区切りを含まない単純名の場合は
        ディレクトリとして扱い、配下すべてにマッチさせる。
        それ以外は _normalize_glob_pattern() で前置処理を行う。

        Args:
            pattern: 除外パターン

        Returns:
            正規化済みパターン
        """
        if pattern.endswith("/"):
            # 末尾スラッシュ付きはディレクトリ → 配下すべてにマッチ
            stripped = pattern.rstrip("/")
            return self._normalize_glob_pattern(stripped + "/**")
        # 拡張子なし、パス区切りなし、ワイルドカードなしの単純名 → ディレクトリとして扱う
        stripped = pattern.rstrip("/")
        if "/" not in stripped and "." not in stripped.lstrip(".") and "*" not in stripped:
            return self._normalize_glob_pattern(stripped + "/**")
        return self._normalize_glob_pattern(pattern)
