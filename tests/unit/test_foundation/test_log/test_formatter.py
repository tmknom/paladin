"""paladin.foundation.log.formatter のテスト"""

import logging

from paladin.foundation.log.formatter import LogFormatter


class TestLogFormatter:
    """LogFormatter クラスのテスト"""

    def setup_method(self):
        self._formatter = LogFormatter()

    def test_create_console_formatter_color(self):
        """formatter_type="color" の場合 colorlog.ColoredFormatter を使う辞書を返す"""
        # Act
        result = self._formatter.create_console_formatter("color")

        # Assert
        assert result["()"] == "colorlog.ColoredFormatter"
        assert "log_colors" in result

    def test_create_console_formatter_json_context_with_class(self):
        """formatter_type="json_context" かつ json_formatter_class 指定時はクラスを使う辞書を返す"""

        # Arrange
        class CustomFormatter(logging.Formatter):
            pass

        # Act
        result = self._formatter.create_console_formatter(
            "json_context", json_formatter_class=CustomFormatter
        )

        # Assert
        assert result["()"] is CustomFormatter
        assert "datefmt" in result

    def test_create_console_formatter_json_context_without_class(self):
        """formatter_type="json_context" で json_formatter_class 未指定時はデフォルトフォーマットを返す"""
        # Act
        result = self._formatter.create_console_formatter("json_context")

        # Assert
        assert "format" in result
        assert "datefmt" in result
        assert "()" not in result

    def test_create_file_formatter(self):
        """create_file_formatter は plain 形式の辞書を返す"""
        # Act
        result = self._formatter.create_file_formatter()

        # Assert
        assert "format" in result
        assert "datefmt" in result
