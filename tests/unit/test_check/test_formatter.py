"""CheckReportFormatterクラスのテスト"""

import json
from pathlib import Path

from paladin.check.formatter import CheckFormatterFactory, CheckJsonFormatter, CheckReportFormatter
from paladin.check.result import CheckResult
from paladin.check.types import TargetFiles
from paladin.foundation.output import OutputFormat
from paladin.rule import SourceFiles, Violation, Violations


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
        source_files=SourceFiles(files=()),
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
        assert "改善手順:" in report.text
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
        assert (
            "  改善手順: `paladin view require-all-export` を実行して改善手順を確認してください"
            in report.text
        )

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


class TestCheckJsonFormatter:
    """CheckJsonFormatterクラスのテスト"""

    def test_json_format_正常系_違反なしでstatus_okとexit_code_0のJSON文字列を返すこと(self):
        # Arrange
        result = _make_check_result(())

        # Act
        report = CheckJsonFormatter().format(result)

        # Assert
        assert '"status": "ok"' in report.text
        assert '"total_violations": 0' in report.text
        assert report.exit_code == 0

    def test_json_format_正常系_違反ありでstatus_violationsとexit_code_1のJSON文字列を返すこと(
        self,
    ):
        # Arrange
        v = _make_violation()
        result = _make_check_result((v,))

        # Act
        report = CheckJsonFormatter().format(result)

        # Assert
        assert '"status": "violations"' in report.text
        assert report.exit_code == 1

    def test_json_format_正常系_diagnosticsに全違反の詳細が含まれること(self):
        # Arrange
        v = _make_violation()
        result = _make_check_result((v,))

        # Act
        report = CheckJsonFormatter().format(result)

        # Assert
        data = json.loads(report.text)
        diag = data["diagnostics"][0]
        assert "file" in diag
        assert "line" in diag
        assert "column" in diag
        assert "rule_id" in diag
        assert "rule_name" in diag
        assert "message" in diag
        assert "reason" in diag
        assert "suggestion" in diag
        assert "detail" in diag
        assert (
            diag["detail"]
            == "`paladin view require-all-export` を実行して改善手順を確認してください"
        )

    def test_json_format_正常系_summaryにby_ruleとby_fileが含まれること(self):
        # Arrange
        v1 = _make_violation("a/__init__.py", rule_id="rule-a", rule_name="Rule A")
        v2 = _make_violation("b/__init__.py", rule_id="rule-a", rule_name="Rule A")
        v3 = _make_violation("b/__init__.py", rule_id="rule-b", rule_name="Rule B")
        result = _make_check_result((v1, v2, v3))

        # Act
        report = CheckJsonFormatter().format(result)

        # Assert
        data = json.loads(report.text)
        assert data["summary"]["by_rule"]["rule-a"] == 2
        assert data["summary"]["by_rule"]["rule-b"] == 1
        assert data["summary"]["by_file"]["a/__init__.py"] == 1
        assert data["summary"]["by_file"]["b/__init__.py"] == 2

    def test_json_format_正常系_fileフィールドがPath型から文字列に変換されること(self):
        # Arrange
        v = _make_violation(file="src/paladin/__init__.py")
        result = _make_check_result((v,))

        # Act
        report = CheckJsonFormatter().format(result)

        # Assert
        data = json.loads(report.text)
        assert isinstance(data["diagnostics"][0]["file"], str)


class TestCheckFormatterFactory:
    """CheckFormatterFactoryクラスのテスト"""

    def test_factory_format_正常系_TEXT指定でtext形式のCheckReportを返すこと(self):
        # Arrange
        result = _make_check_result(())

        # Act
        report = CheckFormatterFactory().format(result, OutputFormat.TEXT)

        # Assert
        assert "status: ok" in report.text

    def test_factory_format_正常系_JSON指定でJSON形式のCheckReportを返すこと(self):
        # Arrange
        result = _make_check_result(())

        # Act
        report = CheckFormatterFactory().format(result, OutputFormat.JSON)

        # Assert
        data = json.loads(report.text)
        assert "status" in data

    def test_factory_format_正常系_TEXT指定で違反ありのexit_code_1を返すこと(self):
        # Arrange
        v = _make_violation()
        result = _make_check_result((v,))

        # Act
        report = CheckFormatterFactory().format(result, OutputFormat.TEXT)

        # Assert
        assert report.exit_code == 1

    def test_factory_format_正常系_JSON指定で違反ありのexit_code_1を返すこと(self):
        # Arrange
        v = _make_violation()
        result = _make_check_result((v,))

        # Act
        report = CheckFormatterFactory().format(result, OutputFormat.JSON)

        # Assert
        assert report.exit_code == 1
