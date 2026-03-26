"""Configパッケージの環境変数設定モジュール

外部環境からの設定値注入を担い、Foundation層の CoreSettings に依存する。
"""

from pathlib import Path
from typing import Literal

from paladin.foundation.model import CoreSettings, SettingsConfigDict

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]


class EnvVarConfig(CoreSettings):
    """環境変数から設定値を読み込む不変データコンテナ

    指定したプレフィックスの環境変数を自動マッピングする。
    未設定項目はデフォルト値を使用し、未知の環境変数は禁止する。
    """

    model_config = SettingsConfigDict(
        env_prefix="EXAMPLE_",
    )

    log_level: LogLevel = "WARNING"
    tmp_dir: Path | None = None
