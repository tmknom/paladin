from pathlib import Path

from paladin.lint.types import RuleMeta, Violation, Violations


class TestViolation:
    """Violationクラスのテスト"""

    def test_violation_init_正常系_全フィールドを保持すること(self):
        # Arrange & Act
        result = Violation(
            file=Path("src/paladin/__init__.py"),
            line=1,
            column=0,
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            message="__init__.py に __all__ が定義されていない",
            reason="__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある",
            suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
        )

        # Assert
        assert result.file == Path("src/paladin/__init__.py")
        assert result.line == 1
        assert result.column == 0
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.message == "__init__.py に __all__ が定義されていない"
        assert (
            result.reason
            == "__all__ が未定義の場合、パッケージの公開インタフェースが不明確になり、意図しないシンボルが外部に露出するリスクがある"
        )
        assert result.suggestion == "__all__ リストを定義し、公開するシンボルを明示的に列挙する"


class TestViolations:
    """Violationsクラスのテスト"""

    def _make_violation(self, file: str = "src/paladin/__init__.py") -> Violation:
        return Violation(
            file=Path(file),
            line=1,
            column=0,
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            message="__init__.py に __all__ が定義されていない",
            reason="reason",
            suggestion="suggestion",
        )

    def test_violations_len_正常系_件数を返すこと(self):
        # Arrange
        v1 = self._make_violation("a/__init__.py")
        v2 = self._make_violation("b/__init__.py")
        violations = Violations(items=(v1, v2))

        # Act
        result = len(violations)

        # Assert
        assert result == 2

    def test_violations_iter_正常系_Violationをイテレーションできること(self):
        # Arrange
        v1 = self._make_violation("a/__init__.py")
        v2 = self._make_violation("b/__init__.py")
        violations = Violations(items=(v1, v2))

        # Act
        result = list(violations)

        # Assert
        assert result == [v1, v2]

    def test_violations_len_エッジケース_空で0を返すこと(self):
        # Arrange
        violations = Violations(items=())

        # Act
        result = len(violations)

        # Assert
        assert result == 0


class TestRuleMeta:
    """RuleMetaクラスのテスト"""

    def test_rule_meta_init_正常系_全フィールドを保持すること(self):
        # Arrange & Act
        result = RuleMeta(
            rule_id="require-all-export",
            rule_name="Require __all__ Export",
            summary="__init__.py に __all__ の定義を要求する",
            intent="パッケージの公開インターフェースを明示し、意図しないシンボルの露出を防ぐ",
            guidance="__init__.py に __all__ が定義されているかを確認する",
            suggestion="__all__ リストを定義し、公開するシンボルを明示的に列挙する",
        )

        # Assert
        assert result.rule_id == "require-all-export"
        assert result.rule_name == "Require __all__ Export"
        assert result.summary == "__init__.py に __all__ の定義を要求する"
        assert (
            result.intent
            == "パッケージの公開インターフェースを明示し、意図しないシンボルの露出を防ぐ"
        )
        assert result.guidance == "__init__.py に __all__ が定義されているかを確認する"
        assert result.suggestion == "__all__ リストを定義し、公開するシンボルを明示的に列挙する"
