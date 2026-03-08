"""アプリケーション共通のパス設定

各層から参照されるパス情報を一元管理する不変データコンテナ。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PathConfig:
    """パス情報を保持する不変データコンテナ

    アプリケーションライフサイクル全体で不変。
    from_base_dir()ファクトリーで標準的なパス構成を生成できる。
    """

    tmp_dir: Path

    @classmethod
    def from_base_dir(cls, base_dir: Path) -> PathConfig:
        """base_dirを基に標準的なパス構成でPathConfigを作成

        Args:
            base_dir: ベースとなるディレクトリパス（リポジトリルートなど）

        Returns:
            標準的なパス構成のPathConfigインスタンス
        """
        tmp_dir = base_dir / "tmp"
        return PathConfig(
            tmp_dir=tmp_dir,
        )
