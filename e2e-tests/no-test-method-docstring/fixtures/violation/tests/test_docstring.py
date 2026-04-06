"""違反フィクスチャ: テストメソッドに docstring が記述されているパターンを含む"""


class TestDocstring:
    """TestDocstring クラスのテスト"""

    def test_正常系_何かを検証する(self) -> None:
        """正常にテストが通ることを確認する"""  # 違反: docstring が不要
        # Arrange
        expected = 1
        # Act
        result = 1
        # Assert
        assert result == expected
