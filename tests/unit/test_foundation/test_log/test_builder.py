"""paladin.foundation.log.builder のテスト"""

import logging
from pathlib import Path

from paladin.foundation.log.builder import LogDictConfigBuilder


class TestLogDictConfigBuilder:
    """LogDictConfigBuilder クラスのテスト"""

    def setup_method(self):
        self._builder = LogDictConfigBuilder()

    def test_build_console_only(self):
        # Act
        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
        )

        # Assert
        assert result["version"] == 1
        assert "console" in result["handlers"]
        assert "file" not in result["handlers"]
        assert result["root"]["handlers"] == ["console"]

    def test_build_with_file_output(self):
        # Arrange
        log_path = Path("/tmp/test.log")

        # Act
        result = self._builder.build(
            level="DEBUG",
            stream="stderr",
            file_output=True,
            log_path=log_path,
            console_formatter_type="color",
        )

        # Assert
        assert "file" in result["handlers"]
        assert "file" in result["root"]["handlers"]
        assert "file" in result["formatters"]

    def test_build_with_json_formatter_class(self):
        # Arrange
        class CustomFormatter(logging.Formatter):
            pass

        # Act
        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
            json_formatter_class=CustomFormatter,
        )

        # Assert
        assert result["formatters"]["console"]["()"] is CustomFormatter

    def test_build_disable_existing_loggers_false(self):
        # Act
        result = self._builder.build(
            level="INFO",
            stream="stdout",
            file_output=False,
            log_path=None,
            console_formatter_type="json_context",
        )

        # Assert
        assert result["disable_existing_loggers"] is False
