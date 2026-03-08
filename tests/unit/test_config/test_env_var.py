from pathlib import Path

import pytest
from pydantic import ValidationError

from example.config import EnvVarConfig


class TestEnvVarConfig:
    """EnvVarConfigクラスのテスト"""

    def test_log_level_正常系_環境変数未設定時はINFOがデフォルト(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.delenv("EXAMPLE_LOG_LEVEL", raising=False)

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.log_level == "INFO"

    def test_log_level_正常系_環境変数が設定されていればその値を返す(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_LOG_LEVEL", "DEBUG")

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.log_level == "DEBUG"

    def test_log_level_異常系_不正な値はValidationErrorを送出(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_LOG_LEVEL", "INVALID")

        # Act & Assert
        with pytest.raises(ValidationError):
            EnvVarConfig()

    def test_tmp_dir_正常系_環境変数未設定時はNoneがデフォルト(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.delenv("EXAMPLE_TMP_DIR", raising=False)

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.tmp_dir is None

    def test_tmp_dir_正常系_環境変数が設定されていればPathオブジェクトを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_TMP_DIR", "/tmp/example")

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.tmp_dir == Path("/tmp/example")
