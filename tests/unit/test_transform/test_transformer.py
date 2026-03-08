from datetime import datetime

from example.transform.transformer import TextTransformer
from example.transform.types import DstText, SrcText, TransformedDatetime


class TestTextTransformer:
    """TextTransformerクラスのテスト"""

    def test_transform_正常系_複数行テキストに行番号と日時ヘッダーを付与(self):
        # Arrange
        text = SrcText("first\nsecond\nthird")
        current_datetime = TransformedDatetime(datetime(2026, 2, 18, 12, 0, 0))
        transformer = TextTransformer()

        # Act
        result = transformer.transform(text, current_datetime)

        # Assert
        assert result == DstText("2026-02-18 12:00:00\n1: first\n2: second\n3: third")

    def test_transform_正常系_空テキストは日時のみ(self):
        # Arrange
        text = SrcText("")
        current_datetime = TransformedDatetime(datetime(2026, 2, 18, 12, 0, 0))
        transformer = TextTransformer()

        # Act
        result = transformer.transform(text, current_datetime)

        # Assert
        assert result == DstText("2026-02-18 12:00:00")

    def test_transform_正常系_日本語テキストに行番号と日時ヘッダーを付与(self):
        # Arrange
        text = SrcText("こんにちは\n世界")
        current_datetime = TransformedDatetime(datetime(2026, 2, 18, 0, 0, 0))
        transformer = TextTransformer()

        # Act
        result = transformer.transform(text, current_datetime)

        # Assert
        assert result == DstText("2026-02-18 00:00:00\n1: こんにちは\n2: 世界")
