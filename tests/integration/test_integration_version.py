"""version サブコマンドのインテグレーションテスト"""

import re
import subprocess
import sys


class TestIntegrationVersion:
    """version サブコマンドのインテグレーションテスト"""

    def test_version_正常系_バージョン文字列を出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "version"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert re.search(r"\d+\.\d+\.\d+", result.stdout) is not None
