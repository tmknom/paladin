"""準拠フィクスチャ: フラットなテストクラス構造"""


class TestCheckOrchestratorOrchestrate:
    """CheckOrchestrator.orchestrate メソッドのテスト"""

    def test_正常系_レポートを返す(self) -> None:
        # Arrange
        value = "test"

        # Act
        result = value.upper()

        # Assert
        assert result == "TEST"


class TestCheckOrchestratorEdgeCases:
    """CheckOrchestrator のエッジケースのテスト"""

    def test_正常系_空のファイルで空レポートを返す(self) -> None:
        # Arrange
        items: list[str] = []

        # Act
        result = len(items)

        # Assert
        assert result == 0
