from pathlib import Path

import pytest

from example.config import AppConfig, EnvVarConfig


class TestAppConfig:
    """AppConfigクラスのテスト"""

    def test_build_正常系_log_level指定時はその値が環境変数より優先される(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_LOG_LEVEL", "DEBUG")

        # Act
        result = AppConfig.build(EnvVarConfig(), log_level="WARNING")

        # Assert
        assert result.log_level == "WARNING"

    def test_build_正常系_EXAMPLE_TMP_DIR設定時はenv値をTMP_DIR未設定時はcwd配下のtmpを使用(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        # Arrange - 環境変数設定時: env値が使われること
        monkeypatch.setenv("EXAMPLE_TMP_DIR", str(tmp_path / "from_env"))
        assert AppConfig.build(EnvVarConfig()).tmp_dir == tmp_path / "from_env"

        # Arrange - 環境変数未設定時: PathConfig経由でcwd/tmpが使われること
        monkeypatch.delenv("EXAMPLE_TMP_DIR")
        monkeypatch.chdir(tmp_path)
        assert AppConfig.build(EnvVarConfig()).tmp_dir == tmp_path / "tmp"
