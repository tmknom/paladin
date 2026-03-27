"""list サブコマンドのインテグレーションテスト"""

import subprocess
import sys


class TestIntegrationList:
    """list サブコマンドのインテグレーションテスト"""

    def test_list_正常系_ルール一覧をtext形式で出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "list"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert result.stdout != ""
