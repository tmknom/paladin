"""テキスト変換の中核処理

行番号付与と日時ヘッダー追加を担当する。
"""

from example.foundation.log import log
from example.transform.types import DstText, SrcText, TransformedDatetime


class TextTransformer:
    """テキストに行番号と日時ヘッダーを付与する

    入力テキストの各行に行番号を付与し、先頭に現在日時を追加する。
    """

    def __init__(self) -> None:
        """TextTransformerを初期化"""

    @log
    def transform(self, text: SrcText, datetime: TransformedDatetime) -> DstText:
        """テキストに行番号と日時ヘッダーを付与

        Args:
            text: 変換対象のテキスト
            datetime: 先頭に付与する日時

        Returns:
            日時ヘッダーと行番号を付与したテキスト
        """
        # 先頭に現在日時を追加し、テキストに行番号を付与
        output_lines = [str(datetime), *text.numbered_lines()]

        # 改行区切りのテキストに戻す
        return DstText("\n".join(output_lines))
