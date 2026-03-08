"""基盤層のエラーログ出力

例外の種類に応じてログフォーマットを切り替える。
sys.exitは実行せず、ログ出力のみを担当する。
"""

import logging

from example.foundation.error.error import ApplicationError


class ErrorHandler:
    """例外をログ出力用メッセージにフォーマットして記録する

    例外の型（ApplicationError or 汎用Exception）に応じてフォーマットを切り替える。

    Constraints:
        - sys.exitは呼ばない（終了判断は呼び出し元が行う）
        - ログ出力のみを担当（例外の再送出や変換は行わない）
    """

    def handle(self, exception: Exception) -> None:
        """例外処理を実行"""
        if isinstance(exception, ApplicationError):
            msg = self._format_application_error(exception)
        else:
            msg = self._format_general_exception(exception)

        logger = logging.getLogger(__name__)
        logger.log(logging.ERROR, msg, exc_info=True)

    def _format_application_error(self, exception: ApplicationError) -> str:
        """ApplicationError用のログメッセージを生成

        Args:
            exception: ApplicationError例外オブジェクト

        Returns:
            ログ出力用フォーマット済みメッセージ
        """
        cause_type = f"{type(exception.cause).__module__}.{type(exception.cause).__name__}"
        cause_message = str(exception.cause)

        return (
            f"type={type(exception).__module__}.{type(exception).__name__} "
            f"message={exception.message} "
            f"cause_type={cause_type} "
            f"cause_message={cause_message}"
        )

    def _format_general_exception(self, exception: Exception) -> str:
        """汎用Exception用のログメッセージを生成

        Args:
            exception: Exception例外オブジェクト

        Returns:
            ログ出力用フォーマット済みメッセージ
        """
        cause_type = f"{type(exception.__cause__).__module__}.{type(exception.__cause__).__name__}"
        cause_message = str(exception.__cause__)

        return (
            f"type={type(exception).__module__}.{type(exception).__name__} "
            f"message={exception} "
            f"cause_type={cause_type} "
            f"cause_message={cause_message}"
        )
