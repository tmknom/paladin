"""paladin.foundation.log.builder のテスト"""

import logging
from pathlib import Path

from paladin.foundation.log.builder import LogDictConfigBuilder


class TestLogDictConfigBuilder:
    """LogDictConfigBuilder クラスのテスト"""

    def setup_method(self):
        self._builder = LogDictConfigBuilder()

    def test_build_console_only(self):
        """file_output=False の場合 console ハンドラーのみ含む辞書を返す"""
        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
        )

        assert result["version"] == 1
        assert "console" in result["handlers"]
        assert "file" not in result["handlers"]
        assert result["root"]["handlers"] == ["console"]

    def test_build_with_file_output(self):
        """file_output=True の場合 file ハンドラーを追加する"""
        log_path = Path("/tmp/test.log")
        result = self._builder.build(
            level="DEBUG",
            stream="stderr",
            file_output=True,
            log_path=log_path,
            console_formatter_type="color",
        )

        assert "file" in result["handlers"]
        assert "file" in result["root"]["handlers"]
        assert "file" in result["formatters"]

    def test_build_with_json_formatter_class(self):
        """json_formatter_class を渡すと formatters.console にクラスが設定される"""

        class CustomFormatter(logging.Formatter):
            pass

        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
            json_formatter_class=CustomFormatter,
        )

        assert result["formatters"]["console"]["()"] is CustomFormatter

    def test_build_disable_existing_loggers_false(self):
        """disable_existing_loggers は常に False"""
        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
        )

        assert result["disable_existing_loggers"] is False
