"""example.foundation.error.ErrorHandler のテスト

エラーハンドラーのログ出力処理をテストします。
sys.exit は含まれず、エラーメッセージのログ出力のみを担当します。
"""

import logging

import pytest

from example.foundation.error import ApplicationError, ErrorHandler


class TestErrorHandler:
    """ErrorHandler クラスのテスト"""

    def test_handle_正常系_ApplicationErrorをログ出力(self, caplog: pytest.LogCaptureFixture):
        # Arrange
        app_error = ApplicationError("API呼び出しに失敗しました", "Connection timeout after 30s")
        handler = ErrorHandler()

        # Act
        handler.handle(app_error)

        # Assert
        assert caplog.records[0].levelno == logging.ERROR

    def test_handle_正常系_一般Exceptionをログ出力(self, caplog: pytest.LogCaptureFixture):
        # Arrange
        general_error = ValueError("Invalid input value")
        handler = ErrorHandler()

        # Act
        handler.handle(general_error)

        # Assert
        assert caplog.records[0].levelno == logging.ERROR
