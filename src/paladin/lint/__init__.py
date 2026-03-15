"""ルールドメインパッケージの公開API

公開APIは `paladin.lint` から import すること(`__all__` のみ互換性対象)。
"""

from paladin.lint.protocol import MultiFileRule, Rule
from paladin.lint.rule_set import RuleSet
from paladin.lint.types import RuleMeta, SourceFile, SourceFiles, Violation, Violations

__all__ = [
    "MultiFileRule",
    "Rule",
    "RuleMeta",
    "RuleSet",
    "SourceFile",
    "SourceFiles",
    "Violation",
    "Violations",
]
