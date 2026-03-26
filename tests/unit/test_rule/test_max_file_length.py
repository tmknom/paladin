from pathlib import Path

from paladin.rule.max_file_length import FileLengthCalculator, FileLengthDetector, MaxFileLengthRule
from paladin.rule.types import RuleMeta
from tests.unit.test_rule.helpers import make_source_file, make_test_source_file


def _make_source(num_lines: int) -> str:
    """指定行数のソースを生成する"""
    lines = [f"x_{i} = {i}" for i in range(num_lines)]
    return "\n".join(lines) + "\n"


class TestMaxFileLengthRuleMeta:
    """MaxFileLengthRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = MaxFileLengthRule()

        # Act
        result = rule.meta

        # Assert
        assert isinstance(result, RuleMeta)
        assert result.rule_id == "max-file-length"
        assert result.rule_name == "Max File Length"


class TestMaxFileLengthRuleCheck:
    """MaxFileLengthRule.check のテスト"""

    def test_check_正常系_違反のフィールド値が正しいこと(self):
        # Arrange
        rule = MaxFileLengthRule()
        source = _make_source(301)
        source_file = make_source_file(source, "example.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.rule_id == "max-file-length"

    def test_check_正常系_違反のline番号がファイル末尾の行番号であること(self):
        # Arrange: 301行のファイル
        rule = MaxFileLengthRule()
        source = _make_source(301)
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: 違反の行番号はファイルの行数（末尾）
        assert len(result) == 1
        assert result[0].line == 301

    def test_check_正常系_空ソースで違反なしを返すこと(self) -> None:
        # Arrange
        rule = MaxFileLengthRule()
        source_file = make_source_file("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限500行に対して501行のファイル
        rule = MaxFileLengthRule()
        source = _make_source(501)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルでmax_test_lines以下なら違反なしを返すこと(self):
        # Arrange: テストファイルで500行のファイル
        rule = MaxFileLengthRule()
        source = _make_source(500)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: プロダクション上限300行超えだがテスト上限500行以内の301行
        rule = MaxFileLengthRule()
        source = _make_source(301)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert len(result) == 0

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行のファイル
        rule = MaxFileLengthRule(max_lines=10)
        source = _make_source(11)
        source_file = make_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行のファイル
        rule = MaxFileLengthRule(max_test_lines=20)
        source = _make_source(21)
        source_file = make_test_source_file(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1


class TestFileLengthCalculator:
    """FileLengthCalculator.calc のテスト"""

    def test_改行で終わるソースは行数を正しく返すこと(self):
        source = "a = 1\nb = 2\nc = 3\n"
        assert FileLengthCalculator.calc(source) == 3

    def test_改行なしで終わるソースは行数を正しく返すこと(self):
        source = "a = 1\nb = 2\nc = 3"
        assert FileLengthCalculator.calc(source) == 3

    def test_空文字列は0を返すこと(self):
        assert FileLengthCalculator.calc("") == 0

    def test_改行のみは1を返すこと(self):
        assert FileLengthCalculator.calc("\n") == 1

    def test_1行のソースは1を返すこと(self):
        assert FileLengthCalculator.calc("x = 1\n") == 1


class TestFileLengthDetector:
    """FileLengthDetector.detect のテスト"""

    def test_detect_正常系_超過していればViolationを返すこと(self):
        rule = MaxFileLengthRule(max_lines=5)
        source = _make_source(6)
        source_file = make_source_file(source)
        result = FileLengthDetector.detect(source_file, 6, 5, rule.meta)
        assert result is not None
        assert result.rule_id == "max-file-length"

    def test_detect_正常系_超過していなければNoneを返すこと(self):
        rule = MaxFileLengthRule(max_lines=5)
        source = _make_source(5)
        source_file = make_source_file(source)
        result = FileLengthDetector.detect(source_file, 5, 5, rule.meta)
        assert result is None

    def test_detect_正常系_ちょうど上限はNoneを返すこと(self):
        rule = MaxFileLengthRule(max_lines=5)
        source = _make_source(5)
        source_file = make_source_file(source)
        result = FileLengthDetector.detect(source_file, 5, 5, rule.meta)
        assert result is None
