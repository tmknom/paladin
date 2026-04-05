"""TestApp のテスト（compliant_test_export フィクスチャ）"""

from tests.unit.fake import FakeHelper


class TestApp:
    def test_something(self) -> None:
        # Act
        helper = FakeHelper()
        assert helper is not None
