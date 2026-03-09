"""業務例外の基底定義

ユーザー向けメッセージと開発者向け詳細を分離して保持する。
"""


class ApplicationError(Exception):
    """全ての業務例外の基底クラス

    ユーザー向けメッセージ(message)と開発者向け詳細(cause)を保持する。
    """

    def __init__(
        self,
        message: str,
        cause: Exception | str = "unexpected error occurred",
    ):
        """初期化

        Args:
            message: ユーザー向けの分かりやすいエラーメッセージ（日本語）
            cause: 開発者向けの技術的詳細（デバッグ用、例外オブジェクトまたは英語文字列）
        """
        self.message = message
        self.cause = cause
        super().__init__(message)
