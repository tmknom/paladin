"""Configパッケージのアプリケーション設定合成モジュール

EnvVarConfig と PathConfig を合成し、実行時設定を提供する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from paladin.config.env_var import EnvVarConfig, LogLevel
from paladin.config.path import PathConfig


@dataclass(frozen=True)
class AppConfig:
    """実行時設定を保持する不変データコンテナ

    EnvVarConfig（環境変数）と PathConfig（デフォルト値）を合成する。
    環境変数が設定されていればその値を優先し、未設定の場合はデフォルト値を使用する。
    """

    log_level: LogLevel
    tmp_dir: Path

    @classmethod
    def build(cls, env: EnvVarConfig, *, log_level: LogLevel | None = None) -> AppConfig:
        """EnvVarConfig から AppConfig を生成する

        Args:
            env: 環境変数設定
            log_level: CLIオプションによるログレベル上書き（None の場合は env.log_level を使用）

        Flow:
            1. log_level は None でなければ引数値を優先、None の場合は env.log_level を使用
            2. tmp_dir は env.tmp_dir が None の場合 PathConfig.from_base_dir(Path.cwd()).tmp_dir にフォールバック
        """
        effective_log_level = log_level if log_level is not None else env.log_level
        tmp_dir = (
            env.tmp_dir if env.tmp_dir is not None else PathConfig.from_base_dir(Path.cwd()).tmp_dir
        )
        return AppConfig(log_level=effective_log_level, tmp_dir=tmp_dir)
