"""違反フィクスチャ: テスト対象オブジェクトのプライベート属性に直接アクセスするパターンを含む"""


class TestPrivateAttr:
    def test_正常系_プライベート属性に直接アクセスする(self) -> None:
        # Arrange
        parser = object()
        # Act & Assert
        assert parser._cache is not None  # noqa: SLF001
