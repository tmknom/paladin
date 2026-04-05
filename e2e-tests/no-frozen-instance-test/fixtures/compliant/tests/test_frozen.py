"""準拠フィクスチャ: FrozenInstanceError テストを含まない"""


class TestFrozen:
    def test_正常系_属性を取得できる(self) -> None:
        # Arrange
        value = "test"
        # Act & Assert
        assert value == "test"
