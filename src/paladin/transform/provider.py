"""TransformパッケージのComposition Root

具象クラスへの依存を隠蔽し、Transformパッケージの生成ロジックを一元化する。
"""

from paladin.foundation.fs import TextFileSystemReader, TextFileSystemWriter
from paladin.foundation.log import log
from paladin.transform.orchestrator import TransformOrchestrator
from paladin.transform.reader import TextReader
from paladin.transform.transformer import TextTransformer
from paladin.transform.writer import TextWriter


class TransformOrchestratorProvider:
    """TransformOrchestratorとその依存を生成するファクトリー

    具象クラスの選択と依存注入を一箇所に集約する。
    """

    def __init__(self) -> None:
        """Providerを初期化"""
        pass

    @log
    def provide(self) -> TransformOrchestrator:
        """TransformOrchestratorを構築

        Returns:
            設定済みのTransformOrchestrator
        """
        reader = TextReader(TextFileSystemReader())
        writer = TextWriter(TextFileSystemWriter())

        return TransformOrchestrator(
            reader=reader,
            transformer=TextTransformer(),
            writer=writer,
        )
