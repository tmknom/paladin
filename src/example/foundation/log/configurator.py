"""ロギング設定セットアップ機能"""

import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import colorlog  # noqa: F401  # pyright: ignore[reportUnusedImport]


class LogConfigurator:
    """ログ設定を環境に応じて切り替えるクラス

    使用例:
        # ローカル環境用（プレーンテキスト・stderr・ファイル出力あり・カラー）
        configurator = LogConfigurator(app_name="api", level="INFO")
        log_path = configurator.configure_plain()

        # 開発・本番環境用（JSON・stdout・ファイル出力なし）
        configurator = LogConfigurator(app_name="api", level="DEBUG")
        log_path = configurator.configure_json()
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
            作成したログファイルのパス。既にハンドラーが存在する場合はNoneまたはファイルパス
        """
        return self._configure(
            stream="stderr",
            file_output=True,
            console_formatter_type="color",
            file_formatter_type="plain",
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
            None（ファイル出力なし）。既にハンドラーが存在する場合はNone
        """
        return self._configure(
            stream="stdout",
            file_output=False,
            console_formatter_type="json_context",
            file_formatter_type="",  # 使用しない
            json_formatter_class=json_formatter_class,
        )

    def _configure(
        self,
        stream: str,
        file_output: bool,
        console_formatter_type: str,
        file_formatter_type: str,
        json_formatter_class: type[logging.Formatter] | None = None,
    ) -> Path | None:
        """ログ設定を構成する内部メソッド

        Args:
            stream: 出力先（"stdout" または "stderr"）
            file_output: ファイル出力の有無
            console_formatter_type: コンソール用フォーマッタータイプ
                - "color": カラー表示（プレーンテキスト）
                - "json_context": JSON形式（カスタムフォーマッター使用）
            file_formatter_type: ファイル用フォーマッタータイプ
                - "plain": プレーンテキスト
                - "": 使用しない
            json_formatter_class: JSONフォーマッタークラス（logging.Formatterを継承したクラス）
                console_formatter_type="json_context"の場合のみ使用

        Returns:
            作成したログファイルのパス。ファイル出力なしの場合やハンドラー存在時はNone
        """
        # 再初期化を防ぐためのガード処理
        root_logger = logging.getLogger()
        if root_logger.handlers:
            for h in root_logger.handlers:
                if isinstance(h, logging.FileHandler):
                    return Path(h.baseFilename)
            return None

        # ログファイルパスの設定（ファイル出力ありの場合のみ）
        log_path = None
        if file_output:
            log_dir = Path("tmp/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d_%H%M%S")
            log_path = (log_dir / f"{self.app_name}_{ts}.log").resolve()  # 絶対パスに変換

        # 設定辞書の生成
        config = self._build_dictconfig(
            stream=stream,
            file_output=file_output,
            log_path=log_path,
            console_formatter_type=console_formatter_type,
            file_formatter_type=file_formatter_type,
            json_formatter_class=json_formatter_class,
        )

        logging.config.dictConfig(config)
        logging.captureWarnings(True)
        sys.stderr.flush()
        return log_path

    def _build_dictconfig(
        self,
        stream: str,
        file_output: bool,
        log_path: Path | None,
        console_formatter_type: str,
        file_formatter_type: str,
        json_formatter_class: type[logging.Formatter] | None = None,
    ) -> dict[str, Any]:
        """ログ設定辞書を生成する

        Args:
            stream: 出力先（"stdout" または "stderr"）
            file_output: ファイル出力の有無
            log_path: ログファイルのパス（file_output=Trueの場合のみ）
            console_formatter_type: コンソール用フォーマッタータイプ
            file_formatter_type: ファイル用フォーマッタータイプ
            json_formatter_class: JSONフォーマッタークラス（logging.Formatterを継承したクラス）

        Returns:
            logging.config.dictConfig用の設定辞書
        """
        # フォーマッター定義
        formatters: dict[str, Any] = {}

        if console_formatter_type == "color":
            formatters["console"] = {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)-8s%(reset)s %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            }
        elif console_formatter_type == "json_context":
            if json_formatter_class:
                # クラスオブジェクトを直接使用（文字列パスではなく）
                # これにより循環importの問題を回避できる
                formatters["console"] = {
                    "()": json_formatter_class,
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            else:
                # デフォルトは標準のFormatterを使用（JSON形式ではない）
                formatters["console"] = {
                    "format": "%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d - %(name)s %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }

        if file_formatter_type == "plain":
            formatters["file"] = {
                "format": "%(asctime)s %(levelname)-8s %(filename)s:%(lineno)d - %(name)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            }

        # ハンドラー定義
        handlers: dict[str, Any] = {
            "console": {
                "class": "logging.StreamHandler",
                "stream": f"ext://sys.{stream}",
                "level": self.level,
                "formatter": "console",
            },
        }

        handler_list = ["console"]

        if file_output and log_path:
            handlers["file"] = {
                "class": "logging.FileHandler",
                "filename": str(log_path),
                "encoding": "utf-8",
                "mode": "a",
                "level": "DEBUG",
                "formatter": "file",
            }
            handler_list.append("file")

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "root": {
                "level": "DEBUG",
                "handlers": handler_list,
            },
            "loggers": {
                # よく騒ぐライブラリを静かにするプリセット（未使用ならコメントアウトのままで可）
                "asyncio": {"level": "WARNING"},
                # "urllib3": {"level": "WARNING"},
                # "botocore": {"level": "WARNING"},
            },
        }
