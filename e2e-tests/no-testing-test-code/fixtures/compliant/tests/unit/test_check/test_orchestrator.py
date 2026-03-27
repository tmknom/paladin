"""準拠fixture: Fakeをセットアップに使うテスト（no-testing-test-code 非違反）"""

from tests.unit.fake.fs import InMemoryFsReader


class TestOrchestrator:
    def test_orchestrate(self) -> None:
        reader = InMemoryFsReader(content="# code")
        assert reader is not None
