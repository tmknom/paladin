from pathlib import Path

from paladin.check.result import CheckReport, CheckResult, CheckStatus, CheckSummary
from paladin.check.rule.types import Violation, Violations
from paladin.check.types import ParsedFiles, TargetFiles


class TestCheckResult:
    """CheckResultクラスのテスト"""

    def test_init_正常系_target_filesとparsed_filesとviolationsを保持すること(self):
        # Arrange
        target_files = TargetFiles(files=(Path("a.py"),))
        parsed_files = ParsedFiles(files=())
        violations = Violations(items=())

        # Act
        result = CheckResult(
            target_files=target_files,
            parsed_files=parsed_files,
            violations=violations,
        )

        # Assert
        assert result.target_files == target_files
        assert result.parsed_files == parsed_files
        assert result.violations == violations


class TestCheckStatus:
    """CheckStatusクラスのテスト"""

    def test_check_status_正常系_OK値がokであること(self):
        assert CheckStatus.OK.value == "ok"

    def test_check_status_正常系_VIOLATIONS値がviolationsであること(self):
        assert CheckStatus.VIOLATIONS.value == "violations"


class TestCheckSummary:
    """CheckSummaryクラスのテスト"""

    def _make_violation(
        self,
        file: str = "src/paladin/__init__.py",
        rule_id: str = "require-all-export",
        rule_name: str = "Require __all__ Export",
    ) -> Violation:
        return Violation(
            file=Path(file),
            line=1,
            column=0,
            rule_id=rule_id,
            rule_name=rule_name,
            message="message",
            reason="reason",
            suggestion="suggestion",
        )

    def _make_check_result(self, violations: tuple[Violation, ...]) -> CheckResult:
        return CheckResult(
            target_files=TargetFiles(files=()),
            parsed_files=ParsedFiles(files=()),
            violations=Violations(items=violations),
        )

    def test_check_summary_from_check_result_正常系_違反ありで集計されること(self):
        # Arrange
        v1 = self._make_violation("a/__init__.py", "require-all-export")
        v2 = self._make_violation("b/__init__.py", "require-all-export")
        result = self._make_check_result((v1, v2))

        # Act
        summary = CheckSummary.from_check_result(result)

        # Assert
        assert summary.status == CheckStatus.VIOLATIONS
        assert summary.total == 2
        assert summary.by_rule == {"require-all-export": 2}
        assert summary.by_file == {"a/__init__.py": 1, "b/__init__.py": 1}

    def test_check_summary_from_check_result_正常系_違反なしでOKステータスになること(self):
        # Arrange
        result = self._make_check_result(())

        # Act
        summary = CheckSummary.from_check_result(result)

        # Assert
        assert summary.status == CheckStatus.OK
        assert summary.total == 0
        assert summary.by_rule == {}
        assert summary.by_file == {}

    def test_check_summary_from_check_result_エッジケース_同一ファイル複数違反で件数が合算されること(
        self,
    ):
        # Arrange
        v1 = self._make_violation("a/__init__.py", "rule-a", "Rule A")
        v2 = self._make_violation("a/__init__.py", "rule-b", "Rule B")
        result = self._make_check_result((v1, v2))

        # Act
        summary = CheckSummary.from_check_result(result)

        # Assert
        assert summary.by_file["a/__init__.py"] == 2


class TestCheckReport:
    """CheckReportクラスのテスト"""

    def test_check_report_init_正常系_textとexit_codeを保持すること(self):
        # Arrange & Act
        report = CheckReport(text="summary: ok", exit_code=0)

        # Assert
        assert report.text == "summary: ok"
        assert report.exit_code == 0
