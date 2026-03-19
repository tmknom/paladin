"""CoreSettingsのテスト"""

import pydantic
import pytest

from paladin.foundation.model import CoreSettings, SettingsConfigDict


class SampleSettings(CoreSettings):
    """テスト用のCoreSettingsサブクラス"""

    model_config = SettingsConfigDict(env_prefix="TEST_CORE_")

    value: str = "default"


class TestCoreSettings:
    """CoreSettingsのテスト"""

    def test_extra_forbid_異常系_未知フィールドでValidationError(self):
        # Act & Assert
        with pytest.raises(pydantic.ValidationError):
            SampleSettings.model_validate({"value": "ok", "unknown": "bad"})

    def test_case_insensitive_正常系_環境変数名の大小文字を区別しない(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange: 小文字の環境変数名で設定する
        monkeypatch.setenv("test_core_value", "from_lowercase")

        # Act
        result = SampleSettings()

        # Assert
        assert result.value == "from_lowercase"

    def test_env_prefix_正常系_サブクラスのenv_prefixが適用される(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.setenv("TEST_CORE_VALUE", "hello")

        # Act
        result = SampleSettings()

        # Assert
        assert result.value == "hello"

    def test_default_正常系_環境変数未設定時はデフォルト値を使用(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        # Arrange
        monkeypatch.delenv("TEST_CORE_VALUE", raising=False)

        # Act
        result = SampleSettings()

        # Assert
        assert result.value == "default"
