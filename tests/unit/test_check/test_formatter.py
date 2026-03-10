"""CheckReportFormatterクラスのテスト"""

from pathlib import Path

from paladin.check.formatter import CheckReportFormatter
from paladin.check.types import (
    CheckResult,
    ParsedFiles,
    TargetFiles,
    Violation,
    Violations,
)


def _make_violation(
    file: str = "src/paladin/__init__.py",
    line: int = 1,
    column: int = 0,
    rule_id: str = "require-all-export",
    rule_name: str = "Require __all__ Export",
    message: str = "__init__.py に __all__ が定義されていない",
    reason: str = "__all__ が未定義の場合、パッケージの公開インタフェースが不明確になる",
    suggestion: str = "__all__ リストを定義し、公開するシンボルを明示的に列挙する",
) -> Violation:
    return Violation(
        file=Path(file),
        line=line,
        column=column,
        rule_id=rule_id,
        rule_name=rule_name,
        message=message,
        reason=reason,
        suggestion=suggestion,
    )


def _make_check_result(violations: tuple[Violation, ...]) -> CheckResult:
    return CheckResult(
        target_files=TargetFiles(files=()),
        parsed_files=ParsedFiles(files=()),
        violations=Violations(items=violations),
    )


class TestCheckReportFormatter:
    """CheckReportFormatterクラスのテスト"""

    def test_format_正常系_違反なしでOKサマリーとexit_code_0を返すこと(self):
        # Arrange
        result = _make_check_result(())

        # Act
        report = CheckReportFormatter().format(result)

        # Assert
        assert report.exit_code == 0
        assert "status: ok" in report.text
        assert "total: 0" in report.text

    def test_format_正常系_違反ありで診断ブロックとサマリーとexit_code_1を返すこと(self):
        # Arrange
        v = _make_violation()
        result = _make_check_result((v,))

        # Act
        report = CheckReportFormatter().format(result)

        # Assert
        assert report.exit_code == 1
        assert "require-all-export" in report.text
        assert "概要:" in report.text
        assert "理由:" in report.text
        assert "修正方向:" in report.text
        assert "status: violations" in report.text

    def test_format_正常系_複数違反で全違反の診断ブロックが出力されること(self):
        # Arrange
        v1 = _make_violation("a/__init__.py", rule_id="rule-a", rule_name="Rule A")
        v2 = _make_violation("b/__init__.py", rule_id="rule-b", rule_name="Rule B")
        result = _make_check_result((v1, v2))

        # Act
        report = CheckReportFormatter().format(result)

        # Assert
        assert "a/__init__.py" in report.text
        assert "b/__init__.py" in report.text
        assert "rule-a" in report.text
        assert "rule-b" in report.text

    def test_format_正常系_違反ブロックのフォーマットが仕様どおりであること(self):
        # Arrange
        v = _make_violation(
            file="src/paladin/__init__.py",
            line=1,
            column=0,
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            message="__init__.py に __all__ が定義されていない",
            reason="理由テキスト",
            suggestion="修正方向テキスト",
        )
        result = _make_check_result((v,))

        # Act
        report = CheckReportFormatter().format(result)

        # Assert
        expected_header = "src/paladin/__init__.py:1:0 require-all-export Require __all__ Export"
        assert expected_header in report.text
        assert "  概要: __init__.py に __all__ が定義されていない" in report.text
        assert "  理由: 理由テキスト" in report.text
        assert "  修正方向: 修正方向テキスト" in report.text

    def test_format_正常系_サマリーのby_ruleとby_fileが正しくフォーマットされること(self):
        # Arrange
        v1 = _make_violation("a/__init__.py", rule_id="rule-a", rule_name="Rule A")
        v2 = _make_violation("b/__init__.py", rule_id="rule-a", rule_name="Rule A")
        v3 = _make_violation("b/__init__.py", rule_id="rule-b", rule_name="Rule B")
        result = _make_check_result((v1, v2, v3))

        # Act
        report = CheckReportFormatter().format(result)

        # Assert
        assert "by_rule: rule-a=2, rule-b=1" in report.text
        assert "by_file: a/__init__.py=1, b/__init__.py=2" in report.text
