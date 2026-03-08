"""ファイルシステム関連例外

ファイル操作に特化した例外クラスを定義します。
ファイルの読み書き、パス操作などのエラーを処理します。
"""

from example.foundation.error import ApplicationError


class FileSystemError(ApplicationError):
    """ファイルシステムエラー

    ファイルの読み書き、ディレクトリ操作、パス操作などでエラーが発生した場合に使用します。
    """

    pass
