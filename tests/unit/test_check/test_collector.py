from pathlib import Path

import pytest

from paladin.check.collector import FileCollector, PathExcluder
from paladin.check.types import TargetFiles


class TestFileCollector:
    """FileCollectorクラスのテスト"""

    def test_collect_正常系_単一pyファイルを返すこと(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "a.py"
        py_file.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((py_file,))

        # Assert
        assert isinstance(result, TargetFiles)
        assert len(result) == 1
        assert py_file.resolve() in list(result)

    def test_collect_正常系_ディレクトリ配下のpyファイルを再帰的に列挙すること(
        self, tmp_path: Path
    ):
        # Arrange
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        sub_dir = pkg_dir / "sub"
        sub_dir.mkdir()
        mod_py = pkg_dir / "mod.py"
        mod_py.write_text("")
        inner_py = sub_dir / "inner.py"
        inner_py.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((tmp_path,))

        # Assert
        assert len(result) == 2
        files = list(result)
        assert mod_py.resolve() in files
        assert inner_py.resolve() in files

    def test_collect_正常系_py以外のファイルを除外すること(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "main.py"
        py_file.write_text("")
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("")
        md_file = tmp_path / "doc.md"
        md_file.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((tmp_path,))

        # Assert
        assert len(result) == 1
        assert py_file.resolve() in list(result)

    def test_collect_正常系_重複するファイルパスが排除されること(self, tmp_path: Path):
        # Arrange
        py_file = tmp_path / "a.py"
        py_file.write_text("")
        collector = FileCollector()

        # Act: 同一ファイルをファイル指定・ディレクトリ指定の両方で含める
        result = collector.collect((py_file, tmp_path))

        # Assert
        assert len(result) == 1

    def test_collect_正常系_結果がソートされて安定した順序で返されること(self, tmp_path: Path):
        # Arrange
        c_py = tmp_path / "c.py"
        c_py.write_text("")
        a_py = tmp_path / "a.py"
        a_py.write_text("")
        b_py = tmp_path / "b.py"
        b_py.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((tmp_path,))

        # Assert
        files = list(result)
        assert files == sorted(files)

    def test_collect_正常系_ファイルとディレクトリの混在指定ができること(self, tmp_path: Path):
        # Arrange
        single_file = tmp_path / "single.py"
        single_file.write_text("")
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        sub_py = sub_dir / "sub.py"
        sub_py.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((single_file, sub_dir))

        # Assert
        assert len(result) == 2
        files = list(result)
        assert single_file.resolve() in files
        assert sub_py.resolve() in files

    def test_collect_異常系_存在しないパスでエラーを送出すること(self, tmp_path: Path):
        # Arrange
        non_existent = tmp_path / "non_existent"
        collector = FileCollector()

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            collector.collect((non_existent,))

    def test_collect_エッジケース_空のディレクトリで空のTargetFilesを返すこと(self, tmp_path: Path):
        # Arrange
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        collector = FileCollector()

        # Act
        result = collector.collect((empty_dir,))

        # Assert
        assert len(result) == 0

    def test_collect_エッジケース_py以外のファイルを直接指定した場合に除外されること(
        self, tmp_path: Path
    ):
        # Arrange
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("")
        collector = FileCollector()

        # Act
        result = collector.collect((txt_file,))

        # Assert
        assert len(result) == 0


class TestPathExcluder:
    def test_exclude_正常系_excludeパターンにマッチするファイルを除外すること(self):
        # Arrange
        files = TargetFiles(files=(Path(".venv/lib/foo.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path(".venv/lib/foo.py") not in result.files

    def test_exclude_正常系_マッチしないファイルは残ること(self):
        # Arrange
        files = TargetFiles(files=(Path("src/main.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path("src/main.py") in result.files

    def test_exclude_正常系_globパターンでマッチするファイルを除外すること(self):
        # Arrange
        files = TargetFiles(files=(Path("src/foo_pb2.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=("**/*_pb2.py",))

        # Assert
        assert Path("src/foo_pb2.py") not in result.files

    def test_exclude_エッジケース_空のpatternsでファイルをそのまま返すこと(self):
        # Arrange
        files = TargetFiles(files=(Path("src/main.py"), Path("src/sub.py")))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=())

        # Assert
        assert result.files == files.files

    def test_exclude_エッジケース_空のTargetFilesで空を返すこと(self):
        # Arrange
        files = TargetFiles(files=())
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert result.files == ()

    def test_exclude_正常系_複数のexcludeパターンを適用できること(self):
        # Arrange
        files = TargetFiles(
            files=(
                Path(".venv/lib/foo.py"),
                Path("build/out.py"),
                Path("src/main.py"),
            )
        )
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/", "build/"))

        # Assert
        assert Path(".venv/lib/foo.py") not in result.files
        assert Path("build/out.py") not in result.files
        assert Path("src/main.py") in result.files

    def test_exclude_正常系_絶対パスに対してexcludeパターンがマッチすること(self):
        # Arrange
        files = TargetFiles(files=(Path("/abs/path/.venv/foo.py"),))
        excluder = PathExcluder()

        # Act
        result = excluder.exclude(files, patterns=(".venv/",))

        # Assert
        assert Path("/abs/path/.venv/foo.py") not in result.files

    def test_exclude_正常系_ディレクトリパスの末尾スラッシュの有無によらずマッチすること(self):
        # Arrange: 末尾スラッシュなし ".venv" でも除外される
        files = TargetFiles(files=(Path(".venv/lib/foo.py"),))
        excluder = PathExcluder()

        # Act
        result_with_slash = excluder.exclude(files, patterns=(".venv/",))
        result_without_slash = excluder.exclude(files, patterns=(".venv",))

        # Assert
        assert Path(".venv/lib/foo.py") not in result_with_slash.files
        assert Path(".venv/lib/foo.py") not in result_without_slash.files
