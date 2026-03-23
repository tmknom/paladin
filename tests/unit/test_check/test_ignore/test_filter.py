"""ViolationFilter のテスト"""

from pathlib import Path

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.check.ignore.filter import ViolationFilter
from paladin.rule import Violation, Violations


def _make_violation(
    file: Path,
    rule_id: str = "rule-a",
    line: int = 1,
) -> Violation:
    return Violation(
        file=file,
        line=line,
        column=0,
        rule_id=rule_id,
        rule_name="Rule A",
        message="violation",
        reason="reason",
        suggestion="suggestion",
    )


class TestViolationFilter:
    """ViolationFilter クラスのテスト"""

    def test_filter_正常系_ignore_allで該当ファイルの全違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_特定ルールignoreで該当ルールの違反のみ除外されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a")
        v_b = _make_violation(file_path, "rule-b")
        violations = Violations(items=(v_a, v_b))
        directive = FileIgnoreDirective(
            file_path=file_path,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).rule_id == "rule-b"

    def test_filter_正常系_ignore対象外のファイルの違反は保持されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a = _make_violation(file_a, "rule-a")
        v_b = _make_violation(file_b, "rule-a")
        violations = Violations(items=(v_a, v_b))
        directive = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).file == file_b

    def test_filter_エッジケース_空のViolationsで空のViolationsを返すこと(self):
        # Arrange
        violations = Violations(items=())
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, ())

        # Assert
        assert len(result) == 0

    def test_filter_エッジケース_空のディレクティブで全違反を保持すること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, ())

        # Assert
        assert len(result) == 1

    def test_filter_正常系_複数ファイルで各ファイルのディレクティブが正しく適用されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a1 = _make_violation(file_a, "rule-a")
        v_a2 = _make_violation(file_a, "rule-b")
        v_b1 = _make_violation(file_b, "rule-a")
        v_b2 = _make_violation(file_b, "rule-b")
        violations = Violations(items=(v_a1, v_a2, v_b1, v_b2))
        directive_a = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        directive_b = FileIgnoreDirective(
            file_path=file_b, ignore_all=False, ignored_rules=frozenset({"rule-a"})
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (directive_a, directive_b))

        # Assert
        assert len(result) == 1
        remaining = next(iter(result))
        assert remaining.file == file_b
        assert remaining.rule_id == "rule-b"


class TestViolationFilterLineIgnore:
    """ViolationFilter の行単位 Ignore テスト"""

    def test_filter_正常系_行単位ignore_allで該当行の全違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a", line=5)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_行単位特定ルールignoreで該当ルールの違反のみ除外されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a", line=5)
        v_b = _make_violation(file_path, "rule-b", line=5)
        violations = Violations(items=(v_a, v_b))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=False,
            ignored_rules=frozenset({"rule-a"}),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).rule_id == "rule-b"

    def test_filter_正常系_行単位ignoreが異なる行の違反に影響しないこと(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a", line=3)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_path,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1

    def test_filter_正常系_ファイル単位と行単位のignoreが同時に適用されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a = _make_violation(file_a, "rule-a", line=1)
        v_b_line3 = _make_violation(file_b, "rule-a", line=3)
        v_b_line5 = _make_violation(file_b, "rule-a", line=5)
        violations = Violations(items=(v_a, v_b_line3, v_b_line5))
        file_directive = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        line_directive = LineIgnoreDirective(
            file_path=file_b,
            target_line=3,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (file_directive,), (line_directive,))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).file == file_b
        assert next(iter(result)).line == 5

    def test_filter_エッジケース_空のline_directivesで既存動作が維持されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        file_directive = FileIgnoreDirective(
            file_path=file_path, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (file_directive,), ())

        # Assert
        assert len(result) == 0

    def test_filter_正常系_行単位ignoreが異なるファイルの違反に影響しないこと(self):
        # Arrange: 違反は a.py、ディレクティブは b.py を対象とするケース
        file_a = Path("a.py")
        file_b = Path("b.py")
        violation = _make_violation(file_a, "rule-a", line=5)
        violations = Violations(items=(violation,))
        line_directive = LineIgnoreDirective(
            file_path=file_b,
            target_line=5,
            ignore_all=True,
            ignored_rules=frozenset(),
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), (line_directive,))

        # Assert
        assert len(result) == 1


class TestViolationFilterIgnoreRules:
    """ViolationFilter の ignore_rules パラメータのテスト"""

    def test_filter_正常系_ignore_rulesで指定ルールの全ファイル違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), ignore_rules=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_ignore_rulesで複数ルールの違反が除外されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a")
        v_b = _make_violation(file_path, "rule-b")
        violations = Violations(items=(v_a, v_b))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), ignore_rules=frozenset({"rule-a", "rule-b"}))

        # Assert
        assert len(result) == 0

    def test_filter_正常系_ignore_rulesに含まれないルールの違反は保持されること(self):
        # Arrange
        file_path = Path("example.py")
        v_a = _make_violation(file_path, "rule-a")
        v_b = _make_violation(file_path, "rule-b")
        violations = Violations(items=(v_a, v_b))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), ignore_rules=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 1
        assert next(iter(result)).rule_id == "rule-b"

    def test_filter_正常系_ignore_rulesとfile_directivesが同時に適用されること(self):
        # Arrange
        file_a = Path("a.py")
        file_b = Path("b.py")
        v_a = _make_violation(file_a, "rule-a")
        v_b = _make_violation(file_b, "rule-b")
        violations = Violations(items=(v_a, v_b))
        file_directive = FileIgnoreDirective(
            file_path=file_a, ignore_all=True, ignored_rules=frozenset()
        )
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (file_directive,), ignore_rules=frozenset({"rule-b"}))

        # Assert
        assert len(result) == 0

    def test_filter_エッジケース_空のignore_rulesで既存動作が維持されること(self):
        # Arrange
        file_path = Path("example.py")
        violation = _make_violation(file_path, "rule-a")
        violations = Violations(items=(violation,))
        vf = ViolationFilter()

        # Act
        result = vf.filter(violations, (), ignore_rules=frozenset())

        # Assert
        assert len(result) == 1
