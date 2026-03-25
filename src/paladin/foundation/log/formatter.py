"""dictConfig 用フォーマッター定義生成"""

import logging
from typing import Any, Literal

import colorlog  # noqa: F401  # pyright: ignore[reportUnusedImport]

_DATEFMT = "%Y-%m-%dT%H:%M:%S"
_PLAIN_FORMAT = "%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d - %(name)s %(message)s"

FormatterType = Literal["color", "json_context"]


class LogFormatter:
    """dictConfig 用の formatters 辞書を生成するクラス。状態を持たない。"""

    def create_console_formatter(
        self,
        formatter_type: FormatterType,
        json_formatter_class: type[logging.Formatter] | None = None,
    ) -> dict[str, Any]:
        """コンソール用フォーマッター辞書を返す

        Args:
            formatter_type: フォーマッタータイプ（"color" / "json_context"）
            json_formatter_class: JSONフォーマッタークラス（json_context 時のみ使用）

        Returns:
            dictConfig の formatters エントリ用辞書
        """
        if formatter_type == "color":
            return {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(name)s: %(message)s",
                "datefmt": _DATEFMT,
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            }

        # json_context
        if json_formatter_class:
            return {
                "()": json_formatter_class,
                "datefmt": _DATEFMT,
            }
        return {
            "format": _PLAIN_FORMAT,
            "datefmt": _DATEFMT,
        }

    def create_file_formatter(self) -> dict[str, Any]:
        """ファイル用フォーマッター辞書を返す（plain 形式固定）

        Returns:
            dictConfig の formatters エントリ用辞書
        """
        return {
            "format": _PLAIN_FORMAT,
            "datefmt": _DATEFMT,
        }
