"""ファイル単位・行単位の Ignore 機能の公開 API。

公開 API は `paladin.check.ignore` から import すること。

Docs:
    - docs/design/ignore.md
"""

from paladin.check.ignore.directive import FileIgnoreDirective, LineIgnoreDirective
from paladin.check.ignore.filter import ViolationFilter
from paladin.check.ignore.parser import FileIgnoreParser, LineIgnoreParser
from paladin.check.ignore.resolver import ConfigIgnoreResolver

__all__ = [
    "ConfigIgnoreResolver",
    "FileIgnoreDirective",
    "FileIgnoreParser",
    "LineIgnoreDirective",
    "LineIgnoreParser",
    "ViolationFilter",
]
