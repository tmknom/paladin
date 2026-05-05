"""クラスメソッドのみの準拠フィクスチャ"""


class FileLengthCalculator:
    """ファイルの行数を計算するクラス"""

    @staticmethod
    def calc(source: str) -> int:  # 準拠: クラスの静的メソッドとして定義されている
        if not source:
            return 0
        return len(source.splitlines())
