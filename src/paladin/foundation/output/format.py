"""出力フォーマットの列挙型"""

from enum import Enum


class OutputFormat(Enum):
    """チェック結果の出力フォーマット"""

    TEXT = "text"
    JSON = "json"
