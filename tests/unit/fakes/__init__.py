"""共有 Fake 実装パッケージ"""

from tests.unit.fakes.fs import InMemoryFsReader
from tests.unit.fakes.rule import FakeMultiFileRule, FakePreparableRule, FakeRule

__all__ = ["FakeMultiFileRule", "FakePreparableRule", "FakeRule", "InMemoryFsReader"]
