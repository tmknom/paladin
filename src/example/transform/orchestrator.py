"""Transform層の中核

変換パイプライン全体を制御し、入力・変換・出力の流れを調整する。
"""

from example.foundation.log import log
from example.transform.context import TransformContext
from example.transform.reader import TextReader
from example.transform.transformer import TextTransformer
from example.transform.types import TransformedDatetime, TransformResult
from example.transform.writer import TextWriter


class TransformOrchestrator:
    """テキストファイルを読み込み、行番号を付与して出力する

    Flow:
        1. TextReaderでファイル読み込み
        2. TextTransformerでテキストを変換
        3. TextWriterで書き込み
        4. 実行結果を返す

    Returns:
        TransformResult: 変換前後のテキスト行数を含む実行結果
    """

    def __init__(
        self,
        reader: TextReader,
        transformer: TextTransformer,
        writer: TextWriter,
    ):
        """TransformOrchestratorを初期化

        Args:
            reader: テキストファイル読み込み
            transformer: テキストファイル変換
            writer: テキストファイル書き込み
        """
        self.reader = reader
        self.transformer = transformer
        self.writer = writer

    @log
    def orchestrate(self, context: TransformContext) -> TransformResult:
        """テキストファイルに行番号を付与して出力

        Args:
            context: Transform処理の実行時コンテキスト

        Returns:
            Transform処理の実行結果
        """
        # テキストファイルを読み込み
        src_text = self.reader.read(context.target_file)

        # テキストファイルを変換
        datetime = TransformedDatetime(context.current_datetime)
        dst_text = self.transformer.transform(text=src_text, datetime=datetime)

        # テキストファイルに書き込み
        dst_path = context.tmp_dir / context.target_file.name
        self.writer.write(dst_text, dst_path)

        # 実行結果を返す
        return TransformResult(src_length=src_text.length(), dst_length=dst_text.length())
