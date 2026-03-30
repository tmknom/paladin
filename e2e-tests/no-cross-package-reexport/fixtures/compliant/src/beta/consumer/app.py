"""consumer アプリケーション（準拠フィクスチャ）"""

from beta.check import CheckContext


class App:
    """アプリケーションのメインクラス"""

    def __init__(self) -> None:
        self.context = CheckContext()
