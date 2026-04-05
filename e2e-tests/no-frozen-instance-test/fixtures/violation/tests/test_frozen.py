"""違反フィクスチャ: FrozenInstanceError テストを含む"""

import dataclasses
from dataclasses import FrozenInstanceError

import pytest


class TestFrozen:
    def test_異常系_dataclasses経由のFrozenInstanceError(self) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            pass

    def test_異常系_直接インポートのFrozenInstanceError(self) -> None:
        with pytest.raises(FrozenInstanceError):
            pass
