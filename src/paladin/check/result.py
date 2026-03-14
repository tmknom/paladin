"""Check層の結果・レポート型定義

パイプライン実行結果の集約とフォーマット済み出力を保持する値オブジェクトを定義する。
"""

import enum
from dataclasses import dataclass

from paladin.check.types import TargetFiles
from paladin.lint import Violations
from paladin.source.types import ParsedFiles


@dataclass(frozen=True)
class CheckResult:
    """Check処理の実行結果を保持する不変オブジェクト"""

    target_files: TargetFiles
    """列挙された解析対象ファイル群"""

    parsed_files: ParsedFiles
    """AST解析結果群"""

    violations: Violations
    """ルール違反一覧"""


class CheckStatus(enum.Enum):
    """実行結果の状態を表す列挙型"""

    OK = "ok"
    VIOLATIONS = "violations"


@dataclass(frozen=True)
class CheckSummary:
    """Summary情報（status・total・by_rule・by_file）を保持する値オブジェクト"""

    status: CheckStatus
    total: int
    by_rule: dict[str, int]
    by_file: dict[str, int]

    @classmethod
    def from_check_result(cls, result: CheckResult) -> "CheckSummary":
        """CheckResultから集計してCheckSummaryを生成する"""
        violations = list(result.violations)
        total = len(violations)

        by_rule: dict[str, int] = {}
        by_file: dict[str, int] = {}
        for v in violations:
            by_rule[v.rule_id] = by_rule.get(v.rule_id, 0) + 1
            file_key = str(v.file)
            by_file[file_key] = by_file.get(file_key, 0) + 1

        status = CheckStatus.OK if total == 0 else CheckStatus.VIOLATIONS
        return cls(status=status, total=total, by_rule=by_rule, by_file=by_file)


@dataclass(frozen=True)
class CheckReport:
    """フォーマット済みレポート文字列と終了コードを保持する値オブジェクト"""

    text: str
    exit_code: int
