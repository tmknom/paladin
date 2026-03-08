"""example.foundation.log.configurator のテスト

ログ設定機能のテストを実装します。
"""

import logging
from pathlib import Path

from example.foundation.log.configurator import LogConfigurator


class TestLogConfigurator:
    """LogConfigurator クラスのテスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)

    def teardown_method(self):
        """各テストメソッド実行後のクリーンアップ"""
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        logger.setLevel(logging.NOTSET)

    def test_init_デフォルト値_app_nameを省略すると_logになる(self):
        """app_name を省略すると self.app_name が "log" になる"""
        configurator = LogConfigurator(level="INFO")
        assert configurator.app_name == "log"

    def test_configure_plain_正常系_Pathを返す(self):
        """configure_plain はログファイルの Path を返す"""
        logger = logging.getLogger()
        pytest_handlers = logger.handlers[:]
        for handler in pytest_handlers:
            logger.removeHandler(handler)
        try:
            configurator = LogConfigurator(app_name="test_app", level="INFO")
            log_path = configurator.configure_plain()

            assert isinstance(log_path, Path)
        finally:
            for handler in pytest_handlers:
                logger.addHandler(handler)

    def test_configure_plain_正常系_再初期化防止(self):
        """同じロガーに2回 configure_plain を呼ぶと2回目は None を返す"""
        logger = logging.getLogger()
        pytest_handlers = logger.handlers[:]
        for handler in pytest_handlers:
            logger.removeHandler(handler)
        try:
            configurator = LogConfigurator(app_name="test_app", level="INFO")
            configurator.configure_plain()

            # ハンドラーがある状態で再度呼ぶと再初期化しない
            configurator2 = LogConfigurator(app_name="test_app", level="INFO")
            log_path_2 = configurator2.configure_plain()

            # FileHandler があるため既存パスを返す（None ではない）
            assert isinstance(log_path_2, Path)

            # FileHandler のないコンソールのみの状態で再初期化を試みると None を返す
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.removeHandler(handler)

            configurator3 = LogConfigurator(app_name="test_app", level="INFO")
            log_path_3 = configurator3.configure_plain()

            assert log_path_3 is None
        finally:
            for handler in pytest_handlers:
                logger.addHandler(handler)

    def test_configure_json_正常系_Noneを返す(self):
        """configure_json はファイル出力なしのため None を返す"""
        logger = logging.getLogger()
        pytest_handlers = logger.handlers[:]
        for handler in pytest_handlers:
            logger.removeHandler(handler)
        try:
            configurator = LogConfigurator(app_name="test_app", level="DEBUG")
            log_path = configurator.configure_json()

            assert log_path is None
        finally:
            for handler in pytest_handlers:
                logger.addHandler(handler)

    def test_configure_json_with_custom_formatter_正常系_カスタムフォーマッターを使用(self):
        """configure_json にカスタムフォーマッタークラスを渡すと None を返す"""
        logger = logging.getLogger()
        pytest_handlers = logger.handlers[:]
        for handler in pytest_handlers:
            logger.removeHandler(handler)
        try:

            class CustomFormatter(logging.Formatter):
                def format(self, record: logging.LogRecord) -> str:
                    return f"CUSTOM: {record.getMessage()}"

            configurator = LogConfigurator(app_name="test_app", level="DEBUG")
            log_path = configurator.configure_json(json_formatter_class=CustomFormatter)

            assert log_path is None
        finally:
            for handler in pytest_handlers:
                logger.addHandler(handler)
