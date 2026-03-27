"""テスト用Fakeクラス（violation fixture）"""

from pathlib import Path


class InMemoryFsReader:
    """インメモリでファイル読み込みをシミュレートするFakeクラス"""

    def __init__(self, content: str = "") -> None:
        self.content = content

    def read(self, file_path: Path) -> str:
        return self.content
