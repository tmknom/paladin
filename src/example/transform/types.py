"""Transform向けドメインモデル定義"""

from dataclasses import dataclass
from datetime import datetime
from typing import NewType

from pydantic import Field

from example.foundation.model import CoreModel

TransformedDatetime = NewType("TransformedDatetime", datetime)
"""テキスト変換日時"""


@dataclass(frozen=True)
class SrcText:
    """変換前の入力テキストを保持する不変オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
    """

    text: str
    """変換対象の生テキスト"""

    def numbered_lines(self) -> list[str]:
        """各行に行番号（1始まり）を付与したリストを返す

        Returns:
            "N: 行内容" 形式の文字列リスト。空テキストの場合は空リストを返す。
        """
        return [f"{i + 1}: {line}" for i, line in enumerate(self.text.splitlines())]

    def length(self) -> int:
        """テキストの行数を返す

        Returns:
            改行で分割した行数。空テキストの場合は0を返す。
        """
        return len(self.text.splitlines())


@dataclass(frozen=True)
class DstText:
    """変換後の出力テキストを保持する不変オブジェクト

    Constraints:
        - インスタンス生成後は変更不可（frozen=True）
    """

    text: str
    """変換済みテキスト"""

    def length(self) -> int:
        """テキストの行数を返す

        Returns:
            改行で分割した行数。空テキストの場合は0を返す。
        """
        return len(self.text.splitlines())

    def __str__(self) -> str:
        """内部テキストを文字列として返す

        Returns:
            保持している変換済みテキスト文字列
        """
        return self.text


class TransformResult(CoreModel):
    """変換前後のテキスト行数を保持する不変な結果オブジェクト"""

    src_length: int = Field(..., description="変換前のテキスト行数")
    dst_length: int = Field(..., description="変換後のテキスト行数")

    def to_json(self) -> str:
        """JSON文字列として返す"""
        return self.model_dump_json()
