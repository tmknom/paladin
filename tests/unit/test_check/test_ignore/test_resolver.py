"""ConfigIgnoreResolver のテスト"""

from pathlib import Path

from paladin.check.ignore.resolver import ConfigIgnoreResolver
from paladin.rule import PerFileIgnoreEntry


class TestConfigIgnoreResolver:
    """ConfigIgnoreResolver クラスのテスト"""

    def test_resolve_正常系_glob_パターンにマッチするファイルのFileIgnoreDirectiveを返すこと(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("tests/test_main.py")
        assert directive.ignored_rules == frozenset({"R-001"})
        assert directive.ignore_all is False

    def test_resolve_正常系_ignore_allパターンで全ルールignoreのDirectiveを返すこと(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset(),
                ignore_all=True,
            ),
        )
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("tests/test_main.py")
        assert directive.ignore_all is True

    def test_resolve_正常系_複数パターンが同一ファイルにマッチした場合ルールの和集合になること(
        self,
    ):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
            PerFileIgnoreEntry(
                pattern="tests/test_main.py",
                rule_ids=frozenset({"R-002"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.ignored_rules == frozenset({"R-001", "R-002"})
        assert directive.ignore_all is False

    def test_resolve_正常系_マッチしないファイルはDirectiveに含まれないこと(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("src/main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_エッジケース_空のper_file_ignoresで空タプルを返すこと(self):
        # Arrange
        per_file_ignores: tuple[()] = ()
        file_paths = (Path("tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_エッジケース_空のfile_pathsで空タプルを返すこと(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths: tuple[Path, ...] = ()
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_正常系_ディレクトリパターンが絶対パスにマッチすること(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("/fake/project/tests/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("/fake/project/tests/test_main.py")
        assert directive.ignored_rules == frozenset({"R-001"})

    def test_resolve_正常系_ディレクトリパターンがネストした絶対パスにマッチすること(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("/fake/project/tests/unit/test_check/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        directive = result[0]
        assert directive.file_path == Path("/fake/project/tests/unit/test_check/test_main.py")
        assert directive.ignored_rules == frozenset({"R-001"})

    def test_resolve_正常系_ディレクトリパターンが絶対パスのマッチしないファイルを除外すること(
        self,
    ):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("/fake/project/src/main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert result == ()

    def test_resolve_正常系_複数ディレクトリパターンが異なる絶対パスにマッチすること(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
            PerFileIgnoreEntry(
                pattern="scripts/**",
                rule_ids=frozenset({"R-002"}),
                ignore_all=False,
            ),
        )
        file_paths = (
            Path("/abs/tests/unit/test_main.py"),
            Path("/abs/scripts/deploy.py"),
            Path("/abs/src/main.py"),
        )
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 2
        paths = {d.file_path for d in result}
        assert paths == {
            Path("/abs/tests/unit/test_main.py"),
            Path("/abs/scripts/deploy.py"),
        }

    def test_resolve_正常系_ディレクトリパターンのignore_allが絶対パスで機能すること(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**",
                rule_ids=frozenset(),
                ignore_all=True,
            ),
        )
        file_paths = (Path("/abs/tests/unit/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_resolve_正常系_init_py固有パターンが絶対パスでマッチすること(self):
        # Arrange
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="tests/**/__init__.py",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (
            Path("/abs/tests/__init__.py"),
            Path("/abs/tests/unit/__init__.py"),
            Path("/abs/tests/unit/test_main.py"),
        )
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 2
        paths = {d.file_path for d in result}
        assert paths == {
            Path("/abs/tests/__init__.py"),
            Path("/abs/tests/unit/__init__.py"),
        }

    def test_resolve_正常系_ダブルスター始まりのパターンが絶対パスにマッチすること(self):
        # Arrange: パターンが既に **/ で始まっている場合もマッチすること
        per_file_ignores = (
            PerFileIgnoreEntry(
                pattern="**/tests/**",
                rule_ids=frozenset({"R-001"}),
                ignore_all=False,
            ),
        )
        file_paths = (Path("/abs/tests/unit/test_main.py"),)
        resolver = ConfigIgnoreResolver()

        # Act
        result = resolver.resolve(per_file_ignores=per_file_ignores, file_paths=file_paths)

        # Assert
        assert len(result) == 1
        assert result[0].ignored_rules == frozenset({"R-001"})
