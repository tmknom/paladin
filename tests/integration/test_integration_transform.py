"""transform サブコマンドのインテグレーションテスト"""

import json
import os
import subprocess
import sys
from pathlib import Path


class TestIntegrationTransform:
    """transform サブコマンドのインテグレーションテスト"""

    def test_transform_正常系_変換結果のjsonとファイルが出力されること(self, tmp_dir: Path):
        # Arrange
        input_file = tmp_dir / "input.txt"
        input_file.write_text("test line", encoding="utf-8")
        tmp_output_dir = tmp_dir / "tmp"
        tmp_output_dir.mkdir()

        # Act
        cmd = [sys.executable, "-m", "paladin.cli", "transform", str(input_file)]
        result = subprocess.run(cmd, cwd=tmp_dir, capture_output=True, text=True, timeout=10)

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "src_length" in data
        assert "dst_length" in data

        # 出力ファイルが作成されていることを確認
        output_file = tmp_output_dir / "input.txt"
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "1: test line" in content

    def test_transform_正常系_tmp_dirオプションが環境変数より優先される(self, tmp_dir: Path):
        # Arrange
        input_file = tmp_dir / "input.txt"
        input_file.write_text("test line", encoding="utf-8")
        env_tmp_dir = tmp_dir / "env_tmp"
        env_tmp_dir.mkdir()
        cli_tmp_dir = tmp_dir / "cli_tmp"
        cli_tmp_dir.mkdir()

        # Act
        cmd = [
            sys.executable,
            "-m",
            "paladin.cli",
            "transform",
            str(input_file),
            "--tmp-dir",
            str(cli_tmp_dir),
        ]
        result = subprocess.run(
            cmd,
            cwd=tmp_dir,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "EXAMPLE_TMP_DIR": str(env_tmp_dir)},
        )

        # Assert
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "src_length" in data
        assert (cli_tmp_dir / "input.txt").exists()
        assert not (env_tmp_dir / "input.txt").exists()
