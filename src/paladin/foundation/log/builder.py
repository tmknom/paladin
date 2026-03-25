"""dictConfig 用設定辞書の組み立て"""

import logging
from pathlib import Path
from typing import Any

from paladin.foundation.log.formatter import FormatterType, LogFormatter
from paladin.foundation.log.handler import LogHandler


class LogDictConfigBuilder:
    """LogFormatter と LogHandler の結果を集約し、dictConfig 用の完全な設定辞書を返す。"""

    def __init__(self) -> None:
        """LogFormatter と LogHandler を初期化する。"""
        self._formatter = LogFormatter()
        self._handler = LogHandler()

    def build(
        self,
        level: str,
        stream: str,
        file_output: bool,
        log_path: Path | None,
        console_formatter_type: FormatterType,
        json_formatter_class: type[logging.Formatter] | None = None,
    ) -> dict[str, Any]:
        """DictConfig 用の設定辞書を組み立てる

        Args:
            level: コンソールハンドラーのログレベル
            stream: 出力先（"stdout" または "stderr"）
            file_output: ファイル出力の有無
            log_path: ログファイルのパス（file_output=True の場合のみ使用）
            console_formatter_type: コンソール用フォーマッタータイプ
            json_formatter_class: JSONフォーマッタークラス（json_context 時のみ使用）

        Returns:
            logging.config.dictConfig 用の設定辞書
        """
        formatters: dict[str, Any] = {
            "console": self._formatter.create_console_formatter(
                console_formatter_type, json_formatter_class
            ),
        }
        handlers: dict[str, Any] = {
            "console": self._handler.create_console_handler(stream, level),
        }
        handler_list = ["console"]

        if file_output and log_path:
            formatters["file"] = self._formatter.create_file_formatter()
            handlers["file"] = self._handler.create_file_handler(log_path)
            handler_list.append("file")

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "root": {
                "level": "DEBUG",
                "handlers": handler_list,
            },
            "loggers": {
                "asyncio": {"level": "WARNING"},
            },
        }
