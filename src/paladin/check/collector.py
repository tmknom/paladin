"""Check層のファイル収集・除外機能

パイプライン第1段階として、解析対象を確定する。
"""

from pathlib import Path, PurePath

from paladin.check.types import TargetFiles

__all__ = ["FileCollector", "PathExcluder"]


class FileCollector:
    """ターゲットパスから .py ファイルを再帰的に列挙するコレクター

    Behavior:
        - ファイル指定: .py であれば対象に含める。それ以外は無視する
        - ディレクトリ指定: rglob("*.py") で再帰探索する
        - 存在しないパス: FileNotFoundError を送出する（Fail Fast 原則）
        - 重複排除: Path.resolve() で正規化してから set で排除する
        - ソート: sorted() で辞書順に並べ、安定した順序を保証する
    """

    def collect(self, targets: tuple[Path, ...]) -> TargetFiles:
        """ターゲットパスから .py ファイルを列挙する

        Args:
            targets: 解析対象のファイルまたはディレクトリパス群

        Returns:
            重複排除・ソート済みの .py ファイルパス群

        Raises:
            FileNotFoundError: 存在しないパスが指定された場合
        """
        collected: set[Path] = set()

        for target in targets:
            if not target.exists():
                raise FileNotFoundError(f"指定されたパスが存在しません: {target}")

            if target.is_file():
                self._collect_from_file(target, collected)
            else:
                self._collect_from_directory(target, collected)

        sorted_files = tuple(sorted(collected))
        return TargetFiles(files=sorted_files)

    def _collect_from_file(self, path: Path, collected: set[Path]) -> None:
        """単一ファイルを収集対象に追加する

        .py ファイルのみを対象とし、それ以外は無視する。

        Args:
            path: 対象ファイルパス
            collected: 収集済みパスのセット（in-place 更新）
        """
        if path.suffix == ".py":
            collected.add(path.resolve())

    def _collect_from_directory(self, path: Path, collected: set[Path]) -> None:
        """ディレクトリ配下の .py ファイルを再帰的に収集する

        Args:
            path: 対象ディレクトリパス
            collected: 収集済みパスのセット（in-place 更新）
        """
        for py_file in path.rglob("*.py"):
            collected.add(py_file.resolve())


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
