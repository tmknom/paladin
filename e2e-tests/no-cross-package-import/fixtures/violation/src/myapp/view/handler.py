"""view ハンドラーモジュール（違反フィクスチャ）"""

__all__: list[str] = ["Handler"]

from myapp.check.context import CheckContext  # 違反: check は allow-dirs に含まれない


class Handler:
    """ビューのハンドラークラス"""

    def __init__(self, context: CheckContext) -> None:
        self._context = context
