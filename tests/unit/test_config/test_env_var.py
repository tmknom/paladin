from pathlib import Path

import pydantic
import pytest

from paladin.config import EnvVarConfig


class TestEnvVarConfig:
    """EnvVarConfigクラスのテスト"""

    def test_デフォルト値_正常系_環境変数未設定時はデフォルト値が使われる(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.delenv("EXAMPLE_LOG_LEVEL", raising=False)
        monkeypatch.delenv("EXAMPLE_TMP_DIR", raising=False)

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.log_level == "WARNING"
        assert result.tmp_dir is None

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
        with pytest.raises(pydantic.ValidationError):
            EnvVarConfig()

    def test_tmp_dir_正常系_環境変数が設定されていればPathオブジェクトを返す(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("EXAMPLE_TMP_DIR", "/tmp/paladin")

        # Act
        result = EnvVarConfig()

        # Assert
        assert result.tmp_dir == Path("/tmp/paladin")
