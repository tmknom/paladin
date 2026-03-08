from pathlib import Path

from example.config.path import PathConfig


class TestPathConfig:
    """PathConfigクラスのテスト"""

    def test_from_base_dir_正常系_tmpディレクトリを生成(self, tmp_path: Path):
        # Act
        result = PathConfig.from_base_dir(tmp_path)

        # Assert
        assert result.tmp_dir == tmp_path / "tmp"
