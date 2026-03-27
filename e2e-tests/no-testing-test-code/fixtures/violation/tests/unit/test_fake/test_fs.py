"""違反fixture: Fakeクラスに対するテスト（no-testing-test-code 違反）"""

from tests.unit.fake.fs import InMemoryFsReader


class TestInMemoryFsReader:
    def test_read_returns_content(self) -> None:
        reader = InMemoryFsReader(content="hello")
        assert reader.read.__name__ == "read"
