"""dictConfig 用ハンドラー定義生成"""

from pathlib import Path
from typing import Any


class LogHandler:
    """dictConfig 用の handlers 辞書を生成するクラス。状態を持たない。"""

    def create_console_handler(self, stream: str, level: str) -> dict[str, Any]:
        """コンソール用ハンドラー辞書を返す

        Args:
            stream: 出力先（"stdout" または "stderr"）
            level: ログレベル

        Returns:
            dictConfig の handlers エントリ用辞書
        """
        return {
            "class": "logging.StreamHandler",
            "stream": f"ext://sys.{stream}",
            "level": level,
            "formatter": "console",
        }

    def create_file_handler(self, log_path: Path) -> dict[str, Any]:
        """ファイル用ハンドラー辞書を返す

        Args:
            log_path: ログファイルのパス

        Returns:
            dictConfig の handlers エントリ用辞書
        """
        return {
            "class": "logging.FileHandler",
            "filename": str(log_path),
            "encoding": "utf-8",
            "mode": "a",
            "level": "DEBUG",
            "formatter": "file",
        }
