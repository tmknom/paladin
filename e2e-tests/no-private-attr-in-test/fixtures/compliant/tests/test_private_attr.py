"""準拠フィクスチャ: 公開メソッドの戻り値のみを検証するパターン"""


class TestPrivateAttr:
    def test_正常系_公開メソッドの戻り値を検証する(self) -> None:
        # Arrange
        result = len("hello")
        # Act & Assert
        assert result == 5

    def test_正常系_selfのプライベートヘルパーは問題ない(self) -> None:
        # Arrange
        expected = 42
        # Act
        value = self._compute()
        # Assert
        assert value == expected

    def _compute(self) -> int:
        return 42
