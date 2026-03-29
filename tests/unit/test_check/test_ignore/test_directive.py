"""FileIgnoreDirective / LineIgnoreDirective のテスト"""

from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective


class TestMergeFileIgnoreDirectives:
    """FileIgnoreDirective.merge() のテスト"""

    def test_merge_エッジケース_両方空で空タプルを返すこと(self):
        # Act
        result = FileIgnoreDirective.merge((), ())

        # Assert
        assert result == ()

    def test_merge_正常系_単一ディレクティブがそのまま返ること(self):
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


class TestMergeLineIgnoreDirectives:
    """LineIgnoreDirective.merge() のテスト"""

    def test_merge_エッジケース_空タプルで空タプルを返すこと(self):
        # Act
        result = LineIgnoreDirective.merge(())

        # Assert
        assert result == ()

    def test_merge_正常系_単一ディレクティブがそのまま返ること(self):
        # Arrange
        file_path = Path("a.py")
        directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=1,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )

        # Act
        result = LineIgnoreDirective.merge((directive,))

        # Assert
        assert len(result) == 1
        assert result[0] == directive

    def test_merge_正常系_異なる行のディレクティブが両方含まれること(self):
        # Arrange
        file_path = Path("a.py")
        directive_line1 = LineIgnoreDirective(
            file_path=file_path,
            target_line=1,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        directive_line2 = LineIgnoreDirective(
            file_path=file_path,
            target_line=2,
            ignore_all=False,
            ignored_rules=frozenset({"rule-b"}),
        )

        # Act
        result = LineIgnoreDirective.merge((directive_line1, directive_line2))

        # Assert
        assert len(result) == 2
        lines = {d.target_line for d in result}
        assert lines == {1, 2}

    def test_merge_正常系_同一行のspecific_rulesでignored_rulesが和集合になること(self):
        # Arrange
        file_path = Path("a.py")
        directive_a = LineIgnoreDirective(
            file_path=file_path,
            target_line=2,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        directive_b = LineIgnoreDirective(
            file_path=file_path,
            target_line=2,
            ignore_all=False,
            ignored_rules=frozenset({"rule-b"}),
        )

        # Act
        result = LineIgnoreDirective.merge((directive_a, directive_b))

        # Assert
        assert len(result) == 1
        assert result[0].file_path == file_path
        assert result[0].target_line == 2
        assert result[0].ignore_all is False
        assert result[0].ignored_rules == frozenset({"rule-a", "rule-b"})

    def test_merge_正常系_同一行で片方がignore_all_Trueの場合マージ後もTrueになること(self):
        # Arrange
        file_path = Path("a.py")
        directive_all = LineIgnoreDirective(
            file_path=file_path,
            target_line=3,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        directive_specific = LineIgnoreDirective(
            file_path=file_path,
            target_line=3,
            ignore_all=False,
            ignored_rules=frozenset({"rule-b"}),
        )

        # Act
        result = LineIgnoreDirective.merge((directive_all, directive_specific))

        # Assert
        assert len(result) == 1
        assert result[0].ignore_all is True

    def test_merge_正常系_異なるファイルの同一行番号が別々に保持されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        directive_a = LineIgnoreDirective(
            file_path=file_a,
            target_line=1,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        directive_b = LineIgnoreDirective(
            file_path=file_b,
            target_line=1,
            ignore_all=False,
            ignored_rules=frozenset({"rule-b"}),
        )

        # Act
        result = LineIgnoreDirective.merge((directive_a, directive_b))

        # Assert
        assert len(result) == 2
        file_paths = {d.file_path for d in result}
        assert file_paths == {file_a, file_b}
