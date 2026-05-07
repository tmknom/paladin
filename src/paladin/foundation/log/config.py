"""Foundation 層のログ設定値オブジェクト。LogConfigurator から受け取った設定値を不変集約する。"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from paladin.foundation.log.formatter import FormatterType


@dataclass(frozen=True)
class LogConfig:
    """ログ設定値を集約する不変バリューオブジェクト。console/file 両ハンドラーの設定を一括保持する。"""

    level: str
    stream: str
    file_output: bool
    console_formatter_type: FormatterType
    log_path: Path | None = field(default=None)
    json_formatter_class: type[logging.Formatter] | None = field(default=None)
