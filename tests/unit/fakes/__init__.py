"""共有 Fake 実装パッケージ"""

from tests.unit.fakes.fs import InMemoryFsReader
from tests.unit.fakes.rule import FakeMultiFileRule, FakeRule

__all__ = ["FakeMultiFileRule", "FakeRule", "InMemoryFsReader"]
