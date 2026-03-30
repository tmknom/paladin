"""consumer アプリケーション（違反フィクスチャ）"""

from alpha.check.context import CheckContext


class App:
    """アプリケーションのメインクラス"""

    def __init__(self) -> None:
        self.context = CheckContext()
