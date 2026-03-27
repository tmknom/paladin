from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """インテグレーションテスト用の一時ディレクトリ"""
    test_dir = tmp_path / "integration_test"
    test_dir.mkdir()
    return test_dir
