"""ファイル列挙の中核ロジック

指定されたファイルパスまたはディレクトリパスから、
解析対象となる .py ファイルを再帰的に列挙する。
"""

from pathlib import Path

from paladin.check.types import TargetFiles


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
