"""FileIgnoreDirective / LineIgnoreDirective のテスト"""

from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective


class TestFileIgnoreDirective:
    """FileIgnoreDirective クラスのテスト"""

    def test_FileIgnoreDirective_正常系_全ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = FileIgnoreDirective(
            file_path=Path("example.py"),
            ignore_all=True,
            ignored_rules=frozenset(),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.ignore_all is True
        assert directive.ignored_rules == frozenset()

    def test_FileIgnoreDirective_正常系_特定ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = FileIgnoreDirective(
            file_path=Path("example.py"),
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.ignore_all is False
        assert directive.ignored_rules == frozenset({"rule-a"})


class TestLineIgnoreDirective:
    """LineIgnoreDirective クラスのテスト"""

    def test_LineIgnoreDirective_正常系_全ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = LineIgnoreDirective(
            file_path=Path("example.py"),
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.target_line == 5
        assert directive.ignore_all is True
        assert directive.ignored_rules == frozenset()

    def test_LineIgnoreDirective_正常系_特定ルールignoreのインスタンスを生成できること(self):
        # Arrange / Act
        directive = LineIgnoreDirective(
            file_path=Path("example.py"),
            target_line=3,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )

        # Assert
        assert directive.file_path == Path("example.py")
        assert directive.target_line == 3
        assert directive.ignore_all is False
        assert directive.ignored_rules == frozenset({"rule-a"})


class TestMergeFileIgnoreDirectives:
    """FileIgnoreDirective.merge() のテスト"""

    def test_merge_エッジケース_両方空で空タプルを返すこと(self):
        # Arrange / Act
        result = FileIgnoreDirective.merge((), ())

        # Assert
        assert result == ()

    def test_merge_正常系_config_directivesのみの場合そのまま返すこと(self):
        # Arrange
        file_path = Path("a.py")
        directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=False, ignored_rules=frozenset({"rule-a"})
        )

        # Act
        result = FileIgnoreDirective.merge((directive,), ())

        # Assert
        assert len(result) == 1
        assert result[0] == directive

    def test_merge_正常系_comment_directivesのみの場合そのまま返すこと(self):
        # Arrange
        file_path = Path("a.py")
        directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=False, ignored_rules=frozenset({"rule-b"})
        )

        # Act
        result = FileIgnoreDirective.merge((), (directive,))

        # Assert
        assert len(result) == 1
        assert result[0] == directive

    def test_merge_正常系_同一ファイルでspecific_rulesの場合ignored_rulesが和集合になること(self):
        # Arrange
        file_path = Path("a.py")
        config_d = FileIgnoreDirective(
            file_path=file_path, ignore_all=False, ignored_rules=frozenset({"rule-a"})
        )
        comment_d = FileIgnoreDirective(
            file_path=file_path, ignore_all=False, ignored_rules=frozenset({"rule-b"})
        )

        # Act
        result = FileIgnoreDirective.merge((config_d,), (comment_d,))

        # Assert
        assert len(result) == 1
        assert result[0].file_path == file_path
        assert result[0].ignore_all is False
        assert result[0].ignored_rules == frozenset({"rule-a", "rule-b"})

    def test_merge_正常系_同一ファイルで片方がignore_all_Trueの場合マージ後もTrueになること(self):
        # Arrange
        file_path = Path("a.py")
        config_d = FileIgnoreDirective(
            file_path=file_path, ignore_all=True, ignored_rules=frozenset()
        )
        comment_d = FileIgnoreDirective(
            file_path=file_path, ignore_all=False, ignored_rules=frozenset({"rule-b"})
        )

        # Act
        result = FileIgnoreDirective.merge((config_d,), (comment_d,))

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_merge_正常系_異なるファイルの場合両方含まれること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        config_d = FileIgnoreDirective(
            file_path=file_a, ignore_all=False, ignored_rules=frozenset({"rule-a"})
        )
        comment_d = FileIgnoreDirective(
            file_path=file_b, ignore_all=False, ignored_rules=frozenset({"rule-b"})
        )

        # Act
        result = FileIgnoreDirective.merge((config_d,), (comment_d,))

        # Assert
        assert len(result) == 2
        paths = {d.file_path for d in result}
        assert paths == {file_a, file_b}
