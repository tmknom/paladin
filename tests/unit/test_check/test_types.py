from pathlib import Path

from paladin.check.types import TargetFiles


class TestTargetFiles:
    """TargetFilesクラスのテスト"""

    def test_len_正常系_ファイル数を返すこと(self):
        # Arrange
        target_files = TargetFiles(files=(Path("a.py"), Path("b.py")))

        # Act
        result = len(target_files)

        # Assert
        assert result == 2

    def test_iter_正常系_ファイルパスをイテレーションできること(self):
        # Arrange
        paths = (Path("a.py"), Path("b.py"))
        target_files = TargetFiles(files=paths)

        # Act
        result = list(target_files)

        # Assert
        assert result == [Path("a.py"), Path("b.py")]

    def test_len_エッジケース_空のファイル群で0を返すこと(self):
        # Arrange
        target_files = TargetFiles(files=())

        # Act
        result = len(target_files)

        # Assert
        assert result == 0
