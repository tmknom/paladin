"""view サブコマンドのインテグレーションテスト"""

import subprocess
import sys


class TestIntegrationView:
    """view サブコマンドのインテグレーションテスト"""

    def test_view_正常系_rule_id指定で対象ルールの詳細を出力しexit_code_0で終了すること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "view", "require-all-export"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert result.stdout != ""
        assert "require-all-export" in result.stdout

    def test_view_正常系_テキスト形式で新フィールドのセクションが表示されること(self):
        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "view", "max-file-length"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        assert "背景と意図:" in result.stdout
        assert "改善手順:" in result.stdout
        assert "設定例:" in result.stdout
        assert "検出パターン:" in result.stdout

    def test_view_正常系_JSON形式で新フィールドが含まれること(self):
        # Arrange
        import json

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "view", "max-file-length", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "background" in data
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "config_example" in data
        assert "detection_example" in data
