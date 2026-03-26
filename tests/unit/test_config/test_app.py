from pathlib import Path

import pytest

from paladin.config import AppConfig, EnvVarConfig


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

    def test_build_正常系_EXAMPLE_TMP_DIR設定時はenv値がtmp_dirに使われる(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_TMP_DIR", str(tmp_path / "from_env"))

        # Act
        result = AppConfig.build(EnvVarConfig())

        # Assert
        assert result.tmp_dir == tmp_path / "from_env"

    def test_build_正常系_EXAMPLE_TMP_DIR未設定時はcwd配下のtmpがtmp_dirに使われる(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ):
        # Arrange
        monkeypatch.delenv("EXAMPLE_TMP_DIR", raising=False)
        monkeypatch.chdir(tmp_path)

        # Act
        result = AppConfig.build(EnvVarConfig())

        # Assert
        assert result.tmp_dir == tmp_path / "tmp"
