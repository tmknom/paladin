"""E2Eテスト用の共通ヘルパー"""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

collect_ignore_glob = ["**/fixtures/**"]


@pytest.fixture
def run_paladin_check() -> Callable[[Path], subprocess.CompletedProcess[str]]:
    """Paladin check を子プロセスとして実行するヘルパーを返すフィクスチャ"""

    def _run(target: Path) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, "-m", "paladin.cli", "check", str(target)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    return _run
