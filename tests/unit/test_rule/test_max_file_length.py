from pathlib import Path

from paladin.rule.max_file_length import FileLengthCalculator, FileLengthDetector, MaxFileLengthRule
from paladin.rule.types import DetectionContext, RuleMeta
from tests.unit.test_rule.helper import SourceFileFactory


class SourceCodeBuilder:
    @staticmethod
    def lines(num_lines: int) -> str:
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
        source = SourceCodeBuilder.lines(401)
        source_file = SourceFileFactory.make(source, "example.py")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1
        violation = result[0]
        assert violation.file == Path("example.py")
        assert violation.rule_id == "max-file-length"

    def test_check_正常系_違反のline番号がファイル末尾の行番号であること(self):
        # Arrange: 401行のファイル
        rule = MaxFileLengthRule()
        source = SourceCodeBuilder.lines(401)
        source_file = SourceFileFactory.make(source)

        # Act
        result = rule.check(source_file)

        # Assert: 違反の行番号はファイルの行数（末尾）
        assert len(result) == 1
        assert result[0].line == 401

    def test_check_正常系_空ソースで違反なしを返すこと(self) -> None:
        # Arrange
        rule = MaxFileLengthRule()
        source_file = SourceFileFactory.make("")

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルはmax_test_linesが適用されること(self):
        # Arrange: テストファイルのデフォルト上限800行に対して801行のファイル
        rule = MaxFileLengthRule()
        source = SourceCodeBuilder.lines(801)
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_テストファイルでmax_test_lines以下なら違反なしを返すこと(self):
        # Arrange: テストファイルで800行のファイル
        rule = MaxFileLengthRule()
        source = SourceCodeBuilder.lines(800)
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 0

    def test_check_正常系_テストファイルでmax_lines超過でも違反なしを返すこと(self):
        # Arrange: 上限400行超えだがテスト上限800行以内の401行
        rule = MaxFileLengthRule()
        source = SourceCodeBuilder.lines(401)
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert: テストファイルなので違反なし
        assert len(result) == 0

    def test_check_正常系_カスタムmax_linesが適用されること(self):
        # Arrange: max_lines=10 で11行のファイル
        rule = MaxFileLengthRule(max_lines=10)
        source = SourceCodeBuilder.lines(11)
        source_file = SourceFileFactory.make(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1

    def test_check_正常系_カスタムmax_test_linesが適用されること(self):
        # Arrange: max_test_lines=20 でテストファイルに21行のファイル
        rule = MaxFileLengthRule(max_test_lines=20)
        source = SourceCodeBuilder.lines(21)
        source_file = SourceFileFactory.make_test(source)

        # Act
        result = rule.check(source_file)

        # Assert
        assert len(result) == 1


class TestFileLengthCalculator:
    """FileLengthCalculator.calc のテスト"""

    def test_calc_正常系_改行で終わるソースは行数を正しく返すこと(self):
        # Arrange
        source = "a = 1\nb = 2\nc = 3\n"
        # Act / Assert
        assert FileLengthCalculator.calc(source) == 3

    def test_calc_正常系_改行なしで終わるソースは行数を正しく返すこと(self):
        # Arrange
        source = "a = 1\nb = 2\nc = 3"
        # Act / Assert
        assert FileLengthCalculator.calc(source) == 3

    def test_calc_エッジケース_空文字列は0を返すこと(self):
        # Act / Assert
        assert FileLengthCalculator.calc("") == 0

    def test_calc_エッジケース_改行のみは1を返すこと(self):
        # Act / Assert
        assert FileLengthCalculator.calc("\n") == 1

    def test_calc_正常系_1行のソースは1を返すこと(self):
        # Act / Assert
        assert FileLengthCalculator.calc("x = 1\n") == 1


class TestFileLengthDetector:
    """FileLengthDetector.detect のテスト"""

    def test_detect_正常系_超過していればViolationを返すこと(self):
        # Arrange
        rule = MaxFileLengthRule(max_lines=5)
        source = SourceCodeBuilder.lines(6)
        source_file = SourceFileFactory.make(source)
        ctx = DetectionContext(meta=rule.meta, source_file=source_file)

        # Act
        result = FileLengthDetector.detect(6, 5, ctx)

        # Assert
        assert result is not None
        assert result.rule_id == "max-file-length"

    def test_detect_正常系_超過していなければNoneを返すこと(self):
        # Arrange
        rule = MaxFileLengthRule(max_lines=5)
        source = SourceCodeBuilder.lines(5)
        source_file = SourceFileFactory.make(source)
        ctx = DetectionContext(meta=rule.meta, source_file=source_file)

        # Act
        result = FileLengthDetector.detect(5, 5, ctx)

        # Assert
        assert result is None

    def test_detect_正常系_ちょうど上限はNoneを返すこと(self):
        # Arrange
        rule = MaxFileLengthRule(max_lines=5)
        source = SourceCodeBuilder.lines(5)
        source_file = SourceFileFactory.make(source)
        ctx = DetectionContext(meta=rule.meta, source_file=source_file)

        # Act
        result = FileLengthDetector.detect(5, 5, ctx)

        # Assert
        assert result is None

    def test_detect_正常系_プロダクションファイルの場合は責務見直しを促すsuggestionを返すこと(self):
        # Arrange
        rule = MaxFileLengthRule(max_lines=5)
        source = SourceCodeBuilder.lines(6)
        source_file = SourceFileFactory.make(source)
        ctx = DetectionContext(meta=rule.meta, source_file=source_file)

        # Act
        result = FileLengthDetector.detect(6, 5, ctx)

        # Assert
        assert result is not None
        assert result.suggestion != ""

    def test_detect_正常系_テストファイルの場合はparametrize活用を促すsuggestionを返すこと(self):
        # Arrange
        rule = MaxFileLengthRule(max_test_lines=5)
        source = SourceCodeBuilder.lines(6)
        source_file = SourceFileFactory.make_test(source)
        ctx = DetectionContext(meta=rule.meta, source_file=source_file)

        # Act
        result = FileLengthDetector.detect(6, 5, ctx)

        # Assert
        assert result is not None
        assert result.suggestion != ""
