"""consumer アプリケーション（準拠フィクスチャ）"""

from delta.check import UsedSymbol


class App:
    """アプリケーションのメインクラス"""

    def __init__(self) -> None:
        self.symbol = UsedSymbol()
