"""共有 Fake 実装パッケージ"""

from tests.fake.fs import ErrorFsReader, InMemoryFsReader
from tests.fake.rule import FakeMultiFileRule, FakePreparableRule, FakeRule

__all__ = [
    "ErrorFsReader",
    "FakeMultiFileRule",
    "FakePreparableRule",
    "FakeRule",
    "InMemoryFsReader",
]
