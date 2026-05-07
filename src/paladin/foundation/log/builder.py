"""Foundation 層のログ設定ビルダー。LogFormatter/LogHandler の結果を集約して dictConfig 形式の辞書を組み立てる。"""

from typing import Any

from paladin.foundation.log.config import LogConfig
from paladin.foundation.log.formatter import LogFormatter
from paladin.foundation.log.handler import LogHandler


class LogDictConfigBuilder:
    """ログ設定辞書ビルダー。

    Constraints:
        インスタンスは使い捨て。build() を呼び出すたびに新しい設定辞書を生成する。
        同一インスタンスの複数回呼び出しは可能だが、呼び出しごとに独立した辞書を返す。
    """

    def __init__(self) -> None:
        """LogFormatter と LogHandler を初期化する"""
        self._formatter = LogFormatter()
        self._handler = LogHandler()

    def build(self, config: LogConfig) -> dict[str, Any]:
        """DictConfig 用の設定辞書を組み立てる

        Returns:
            logging.config.dictConfig に渡す辞書。
            file_output が True かつ log_path が指定された場合のみ "file" ハンドラーが追加される。
        """
        formatters: dict[str, Any] = {
            "console": self._formatter.create_console_formatter(
                config.console_formatter_type, config.json_formatter_class
            ),
        }
        handlers: dict[str, Any] = {
            "console": self._handler.create_console_handler(config.stream, config.level),
        }
        handler_list = ["console"]

        if config.file_output and config.log_path:
            formatters["file"] = self._formatter.create_file_formatter()
            handlers["file"] = self._handler.create_file_handler(config.log_path)
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
