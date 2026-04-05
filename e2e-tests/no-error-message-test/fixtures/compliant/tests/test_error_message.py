"""準拠フィクスチャ: 例外の型のみを検証するパターン"""


class TestErrorMessage:
    def test_異常系_例外型のみを検証する(self) -> None:
        # Arrange
        value = ""
        # Act & Assert
        try:
            if not value:
                raise ValueError
        except ValueError:
            pass
