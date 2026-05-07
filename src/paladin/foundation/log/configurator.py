"""Foundation 層のロギング設定エントリーポイント。実行環境（ローカル/本番）に応じてログ出力形式を切り替える。"""

import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from paladin.foundation.log.builder import LogDictConfigBuilder
from paladin.foundation.log.config import LogConfig


class LogConfigurator:
    """ログ設定を環境に応じて切り替えるクラス。

    Constraints:
        再初期化防止ガードが存在する。root logger にハンドラーが既に登録されている場合、
        configure_plain() / configure_json() の2回目以降の呼び出しは設定を変更せず、
        既存 FileHandler のパス（存在しない場合は None）を返して終了する。
    """

    def __init__(self, level: str, app_name: str | None = None) -> None:
        """ログ設定を初期化

        Args:
            level: コンソール出力のログレベル（DEBUG, INFO, WARNING, ERROR）
            app_name: アプリケーション名（ログファイル名の一部として使用）。省略時は "log" を使用
        """
        self.app_name = app_name or "log"
        self.level = level.upper()

    def configure_plain(self) -> Path | None:
        """プレーンテキスト形式でログ設定を構成（ローカル環境用）

        - フォーマット: プレーンテキスト（カラー表示）
        - 出力先: stderr（コンソール）+ ファイル
        - レベル: コンソール=指定されたlevel、ファイル=DEBUG
        - RequestContext: なし

        Returns:
            初回構成時は作成したログファイルのパスを返す。
            既にハンドラーが存在する場合は既存 FileHandler のパス（存在しない場合は None）。
        """
        log_path = self._resolve_log_path()
        return self._configure(
            LogConfig(
                level=self.level,
                stream="stderr",
                file_output=True,
                console_formatter_type="color",
                log_path=log_path,
            )
        )

    def configure_json(
        self, json_formatter_class: type[logging.Formatter] | None = None
    ) -> Path | None:
        """JSON形式でログ設定を構成（開発・本番環境用）

        - フォーマット: JSON
        - 出力先: stdout（コンソールのみ）
        - レベル: コンソール=指定されたlevel
        - RequestContext: カスタムフォーマッターを指定した場合のみ利用可能

        Args:
            json_formatter_class: JSONフォーマッタークラス（logging.Formatterを継承したクラス）
                指定しない場合は標準の logging.Formatter を使用

        Returns:
            常に None を返す。ファイル出力を行わないため。
        """
        return self._configure(
            LogConfig(
                level=self.level,
                stream="stdout",
                file_output=False,
                console_formatter_type="json_context",
                json_formatter_class=json_formatter_class,
            )
        )

    def _configure(self, log_config: LogConfig) -> Path | None:
        # 再初期化を防ぐためのガード処理
        root_logger = logging.getLogger()
        if root_logger.handlers:
            return self._find_existing_log_path(root_logger.handlers)

        logging.config.dictConfig(LogDictConfigBuilder().build(log_config))
        logging.captureWarnings(True)
        sys.stderr.flush()
        return log_config.log_path

    def _resolve_log_path(self) -> Path | None:
        log_dir = Path("tmp/logs/paladin")
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d_%H%M%S")
        return (log_dir / f"{self.app_name}_{ts}.log").resolve()

    def _find_existing_log_path(self, handlers: list[logging.Handler]) -> Path | None:
        """既存のファイルハンドラーからログファイルパスを返す。なければ None を返す"""
        for h in handlers:
            if isinstance(h, logging.FileHandler):
                return Path(h.baseFilename)
        return None
