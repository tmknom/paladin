"""準拠フィクスチャ: テストメソッドに docstring が記述されていないパターン"""


class TestDocstring:
    """TestDocstring クラスのテスト"""

    def test_正常系_何かを検証する(self) -> None:
        # Arrange
        expected = 1
        # Act
        result = 1
        # Assert
        assert result == expected
