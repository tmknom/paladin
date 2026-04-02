"""unused-ignore ルールのテスト"""

from pathlib import Path

import pytest

from paladin.rule.types import RuleMeta, Violation, Violations
from paladin.rule.unused_ignore import (
    IgnoreDirectiveCollector,
    IgnoreDirectiveEntry,
    UnusedIgnoreDetector,
    UnusedIgnoreRule,
)
from tests.unit.test_rule.helper import make_source_file


class TestIgnoreDirectiveCollectorInline:
    """IgnoreDirectiveCollector のインライン Ignore 収集テスト"""

    def test_collect_正常系_直前コメントのインラインIgnoreを収集すること(self):
        # Arrange
        source = "x = 1\n# paladin: ignore[rule-a]\ny = 2\n"
        source_file = make_source_file(source, "example.py")

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].file_path == Path("example.py")
        assert result[0].line == 2
        assert result[0].rule_id == "rule-a"
        assert result[0].is_file_ignore is False

    def test_collect_正常系_行末コメントのインラインIgnoreを収集すること(self):
        # Arrange
        source = "x = 1\ny = 2  # paladin: ignore[rule-a]\nz = 3\n"
        source_file = make_source_file(source, "example.py")

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].line == 2
        assert result[0].rule_id == "rule-a"
        assert result[0].is_file_ignore is False

    def test_collect_正常系_複数ルールIDが指定された場合にルールごとにエントリを生成すること(self):
        # Arrange
        source = "# paladin: ignore[rule-a, rule-b]\nx = 1\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 2
        rule_ids = {e.rule_id for e in result}
        assert rule_ids == {"rule-a", "rule-b"}
        for e in result:
            assert e.line == 1
            assert e.is_file_ignore is False

    def test_collect_エッジケース_ワイルドカードIgnoreを除外すること(self):
        # Arrange
        source = "# paladin: ignore\nx = 1\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 0

    def test_collect_エッジケース_Ignoreコメントがない場合に空タプルを返すこと(self):
        # Arrange
        source = "x = 1\ny = 2\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert result == ()

    def test_collect_正常系_理由コメント付きIgnoreを収集すること(self):
        # Arrange
        source = "# paladin: ignore[rule-a] -- 理由\nx = 1\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "rule-a"
        assert result[0].line == 1


class TestIgnoreDirectiveCollectorFileIgnore:
    """IgnoreDirectiveCollector のファイル単位 Ignore 収集テスト"""

    def test_collect_正常系_ファイル単位Ignoreを収集すること(self):
        # Arrange
        source = "# paladin: ignore-file[rule-a]\nx = 1\n"
        source_file = make_source_file(source, "example.py")

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 1
        assert result[0].file_path == Path("example.py")
        assert result[0].rule_id == "rule-a"
        assert result[0].is_file_ignore is True

    def test_collect_正常系_ファイル単位Ignoreの複数ルールIDを収集すること(self):
        # Arrange
        source = "# paladin: ignore-file[rule-a, rule-b]\nx = 1\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 2
        rule_ids = {e.rule_id for e in result}
        assert rule_ids == {"rule-a", "rule-b"}
        for e in result:
            assert e.is_file_ignore is True

    def test_collect_エッジケース_ファイル単位ワイルドカードIgnoreを除外すること(self):
        # Arrange
        source = "# paladin: ignore-file\nx = 1\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 0

    def test_collect_正常系_インラインとファイル単位Ignoreが混在する場合に両方収集すること(self):
        # Arrange
        source = "# paladin: ignore-file[rule-a]\nx = 1\n# paladin: ignore[rule-b]\ny = 2\n"
        source_file = make_source_file(source)

        # Act
        result = IgnoreDirectiveCollector.collect(source_file)

        # Assert
        assert len(result) == 2
        file_ignore = next(e for e in result if e.is_file_ignore)
        inline_ignore = next(e for e in result if not e.is_file_ignore)
        assert file_ignore.rule_id == "rule-a"
        assert inline_ignore.rule_id == "rule-b"


class TestUnusedIgnoreDetector:
    """UnusedIgnoreDetector のテスト"""

    @pytest.fixture
    def meta(self) -> RuleMeta:
        return UnusedIgnoreRule().meta

    def _make_violation(self, file_path: Path, line: int, rule_id: str) -> Violation:
        return Violation(
            file=file_path,
            line=line,
            column=0,
            rule_id=rule_id,
            rule_name="Fake Rule",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )

    def test_detect_正常系_インラインIgnoreに対応する違反がない場合にViolationを返すこと(
        self, meta: RuleMeta
    ):
        # Arrange: 直前コメント方式 line=2、target_line=3 に違反なし
        source = "x = 1\n# paladin: ignore[rule-a]\ny = 2\n"
        source_file = make_source_file(source, "example.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("example.py"),
                line=2,
                rule_id="rule-a",
                is_file_ignore=False,
                target_line=3,
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 1
        assert result[0].line == 2
        assert result[0].rule_id == "unused-ignore"

    def test_detect_正常系_インラインIgnoreに対応する違反がある場合にViolationを返さないこと(
        self, meta: RuleMeta
    ):
        # Arrange: 直前コメント方式 line=2、target_line=3 に違反あり
        source_file = make_source_file("x = 1\n# paladin: ignore[rule-a]\ny = 2\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"),
                line=2,
                rule_id="rule-a",
                is_file_ignore=False,
                target_line=3,
            ),
        )
        raw_violations = Violations(
            items=(self._make_violation(Path("f.py"), line=3, rule_id="rule-a"),)
        )

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 0

    def test_detect_正常系_ファイル単位Ignoreに対応する違反がない場合にViolationを返すこと(
        self, meta: RuleMeta
    ):
        # Arrange
        source_file = make_source_file("# paladin: ignore-file[rule-a]\nx = 1\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"), line=1, rule_id="rule-a", is_file_ignore=True
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 1
        assert result[0].line == 1

    def test_detect_正常系_ファイル単位Ignoreに対応する違反がある場合にViolationを返さないこと(
        self, meta: RuleMeta
    ):
        # Arrange
        source_file = make_source_file("# paladin: ignore-file[rule-a]\nx = 1\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"), line=1, rule_id="rule-a", is_file_ignore=True
            ),
        )
        raw_violations = Violations(
            items=(self._make_violation(Path("f.py"), line=5, rule_id="rule-a"),)
        )

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 0

    def test_detect_正常系_無効化ルールのIgnoreは未使用とみなさないこと(self, meta: RuleMeta):
        # Arrange: 直前コメント方式 line=1、target_line=2
        source_file = make_source_file("# paladin: ignore[rule-a]\nx = 1\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"),
                line=1,
                rule_id="rule-a",
                is_file_ignore=False,
                target_line=2,
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset({"rule-a"}), source_file, meta
        )

        # Assert
        assert len(result) == 0

    def test_detect_正常系_インラインIgnore未使用のViolationフィールドが正しいこと(
        self, meta: RuleMeta
    ):
        # Arrange: 直前コメント line=2、target_line=3 に違反なし
        source_file = make_source_file("x = 1\n# paladin: ignore[rule-a]\ny = 2\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"),
                line=2,
                rule_id="rule-a",
                is_file_ignore=False,
                target_line=3,
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 1
        v = result[0]
        assert "rule-a" in v.message
        assert "# paladin: ignore" in v.message
        assert "未使用" in v.reason or "不要" in v.reason or "可読性" in v.reason
        assert "rule-a" in v.suggestion

    def test_detect_正常系_ファイル単位Ignore未使用のViolationフィールドが正しいこと(
        self, meta: RuleMeta
    ):
        # Arrange
        source_file = make_source_file("# paladin: ignore-file[rule-a]\nx = 1\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"), line=1, rule_id="rule-a", is_file_ignore=True
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 1
        v = result[0]
        assert "rule-a" in v.message
        assert "ignore-file" in v.message

    def test_detect_エッジケース_エントリが空の場合に空タプルを返すこと(self, meta: RuleMeta):
        # Arrange
        source_file = make_source_file("x = 1\n")
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect((), raw_violations, frozenset(), source_file, meta)

        # Assert
        assert result == ()

    def test_detect_エッジケース_違反リストが空でIgnoreがある場合にViolationを返すこと(
        self, meta: RuleMeta
    ):
        # Arrange: 直前コメント line=1、target_line=2
        source_file = make_source_file("# paladin: ignore[rule-a]\nx = 1\n", "f.py")
        entries = (
            IgnoreDirectiveEntry(
                file_path=Path("f.py"),
                line=1,
                rule_id="rule-a",
                is_file_ignore=False,
                target_line=2,
            ),
        )
        raw_violations = Violations(items=())

        # Act
        result = UnusedIgnoreDetector.detect(
            entries, raw_violations, frozenset(), source_file, meta
        )

        # Assert
        assert len(result) == 1


class TestUnusedIgnoreRuleMeta:
    """UnusedIgnoreRule.meta のテスト"""

    def test_meta_正常系_ルールメタ情報を返すこと(self):
        # Arrange
        rule = UnusedIgnoreRule()

        # Act / Assert
        assert isinstance(rule.meta, RuleMeta)
        assert rule.meta.rule_id == "unused-ignore"


class TestUnusedIgnoreRuleCheck:
    """UnusedIgnoreRule.check のテスト"""

    @pytest.fixture
    def rule(self) -> UnusedIgnoreRule:
        return UnusedIgnoreRule()

    def _make_violation(self, file_path: Path, line: int, rule_id: str) -> Violation:
        return Violation(
            file=file_path,
            line=line,
            column=0,
            rule_id=rule_id,
            rule_name="Fake",
            message="violation",
            reason="reason",
            suggestion="suggestion",
        )

    def test_check_正常系_未使用インラインIgnoreを検出すること(self, rule: UnusedIgnoreRule):
        # Arrange: 直前コメント、対象行に違反なし
        source = "# paladin: ignore[rule-a]\nx = 1\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert len(result) == 1
        assert result[0].rule_id == "unused-ignore"
        assert result[0].line == 1

    def test_check_正常系_使用中のインラインIgnoreは検出しないこと(self, rule: UnusedIgnoreRule):
        # Arrange: 直前コメント、対象行（次行）に違反あり
        source = "x = 1\n# paladin: ignore[rule-a]\ny = 2\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(
            items=(self._make_violation(Path("f.py"), line=3, rule_id="rule-a"),)
        )

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert len(result) == 0

    def test_check_正常系_未使用ファイル単位Ignoreを検出すること(self, rule: UnusedIgnoreRule):
        # Arrange
        source = "# paladin: ignore-file[rule-a]\nx = 1\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert len(result) == 1
        assert result[0].line == 1

    def test_check_正常系_使用中のファイル単位Ignoreは検出しないこと(self, rule: UnusedIgnoreRule):
        # Arrange
        source = "# paladin: ignore-file[rule-a]\nx = 1\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(
            items=(self._make_violation(Path("f.py"), line=5, rule_id="rule-a"),)
        )

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert len(result) == 0

    def test_check_正常系_無効化ルールのIgnoreは検出しないこと(self, rule: UnusedIgnoreRule):
        # Arrange
        source = "# paladin: ignore[rule-a]\nx = 1\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations, disabled_rule_ids=frozenset({"rule-a"}))

        # Assert
        assert len(result) == 0

    def test_check_エッジケース_Ignoreコメントがないファイルで空タプルを返すこと(
        self, rule: UnusedIgnoreRule
    ):
        # Arrange
        source = "x = 1\ny = 2\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert result == ()

    def test_check_エッジケース_ワイルドカードIgnoreは検出対象外であること(
        self, rule: UnusedIgnoreRule
    ):
        # Arrange
        source = "# paladin: ignore\nx = 1\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert result == ()

    def test_check_正常系_行末コメントの未使用Ignoreを検出すること(self, rule: UnusedIgnoreRule):
        # Arrange: 行末コメント、その行に該当ルールの違反なし
        source = "x = 1  # paladin: ignore[rule-a]\ny = 2\n"
        source_file = make_source_file(source, "f.py")
        raw_violations = Violations(items=())

        # Act
        result = rule.check(source_file, raw_violations)

        # Assert
        assert len(result) == 1
        assert result[0].line == 1
