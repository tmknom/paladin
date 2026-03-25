"""paladin.foundation.log.handler のテスト"""

from pathlib import Path

from paladin.foundation.log.handler import LogHandler


class TestLogHandler:
    """LogHandler クラスのテスト"""

    def setup_method(self):
        self._handler = LogHandler()

    def test_create_console_handler(self):
        """create_console_handler は StreamHandler の辞書を返す"""
        result = self._handler.create_console_handler(stream="stderr", level="INFO")

        assert result["class"] == "logging.StreamHandler"
        assert result["stream"] == "ext://sys.stderr"
        assert result["level"] == "INFO"
        assert result["formatter"] == "console"

    def test_create_console_handler_stdout(self):
        """stream="stdout" の場合 ext://sys.stdout を返す"""
        result = self._handler.create_console_handler(stream="stdout", level="DEBUG")

        assert result["stream"] == "ext://sys.stdout"
        assert result["level"] == "DEBUG"

    def test_create_file_handler(self):
        """create_file_handler は FileHandler の辞書を返す"""
        log_path = Path("/tmp/test.log")
        result = self._handler.create_file_handler(log_path)

        assert result["class"] == "logging.FileHandler"
        assert result["filename"] == str(log_path)
        assert result["encoding"] == "utf-8"
        assert result["level"] == "DEBUG"
        assert result["formatter"] == "file"
