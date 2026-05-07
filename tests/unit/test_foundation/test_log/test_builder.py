"""paladin.foundation.log.builder のテスト"""

import logging
from pathlib import Path

from paladin.foundation.log.builder import LogDictConfigBuilder
from paladin.foundation.log.config import LogConfig


class TestLogDictConfigBuilder:
    """LogDictConfigBuilder クラスのテスト"""

    def test_build_正常系_コンソールのみの設定でコンソールハンドラのみが設定されること(self):
        # Arrange
        builder = LogDictConfigBuilder()

        # Act
        result = builder.build(
            LogConfig(
                level="INFO",
                stream="stdout",
                file_output=False,
                console_formatter_type="json_context",
            )
        )

        # Assert
        assert result["version"] == 1
        assert "console" in result["handlers"]
        assert "file" not in result["handlers"]
        assert result["root"]["handlers"] == ["console"]

    def test_build_正常系_ファイル出力有効時にfileハンドラが追加されること(self):
        # Arrange
        builder = LogDictConfigBuilder()
        log_path = Path("/tmp/test.log")

        # Act
        result = builder.build(
            LogConfig(
                level="DEBUG",
                stream="stderr",
                file_output=True,
                console_formatter_type="color",
                log_path=log_path,
            )
        )

        # Assert
        assert "file" in result["handlers"]
        assert "file" in result["root"]["handlers"]
        assert "file" in result["formatters"]

    def test_build_正常系_カスタムjsonフォーマッタクラスが設定されること(self):
        # Arrange
        builder = LogDictConfigBuilder()

        class CustomFormatter(logging.Formatter):
            pass

        # Act
        result = builder.build(
            LogConfig(
                level="INFO",
                stream="stdout",
                file_output=False,
                console_formatter_type="json_context",
                json_formatter_class=CustomFormatter,
            )
        )

        # Assert
        assert result["formatters"]["console"]["()"] is CustomFormatter

    def test_build_正常系_disable_existing_loggers_がFalseであること(self):
        # Arrange
        builder = LogDictConfigBuilder()

        # Act
        result = builder.build(
            LogConfig(
                level="INFO",
                stream="stdout",
                file_output=False,
                console_formatter_type="json_context",
            )
        )

        # Assert
        assert result["disable_existing_loggers"] is False
