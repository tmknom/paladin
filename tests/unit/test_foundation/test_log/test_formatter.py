"""paladin.foundation.log.formatter のテスト"""

import logging

from paladin.foundation.log.formatter import LogFormatter


class TestLogFormatter:
    """LogFormatter クラスのテスト"""

    def setup_method(self):
        self._formatter = LogFormatter()

    def test_create_console_formatter_color(self):
        # Act
        result = self._formatter.create_console_formatter("color")

        # Assert
        assert result["()"] == "colorlog.ColoredFormatter"
        assert "log_colors" in result

    def test_create_console_formatter_json_context_with_class(self):
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
        # Act
        result = self._formatter.create_console_formatter("json_context")

        # Assert
        assert "format" in result
        assert "datefmt" in result
        assert "()" not in result

    def test_create_file_formatter(self):
        # Act
        result = self._formatter.create_file_formatter()

        # Assert
        assert "format" in result
        assert "datefmt" in result
