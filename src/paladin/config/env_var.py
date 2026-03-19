"""Config層の環境変数設定

環境変数から設定値を読み込む。プレフィックス EXAMPLE_ を付与した環境変数を対象とする。
"""

from pathlib import Path
from typing import Literal

from paladin.foundation.model import CoreSettings, SettingsConfigDict

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


class EnvVarConfig(CoreSettings):
    """環境変数から設定値を読み込む不変データコンテナ

    EXAMPLE_ プレフィックスの環境変数を自動マッピングする。
    未設定項目はデフォルト値を使用し、未知の環境変数は禁止する。
    """

    model_config = SettingsConfigDict(
        env_prefix="EXAMPLE_",
    )

    log_level: LogLevel = "WARNING"
    tmp_dir: Path | None = None
