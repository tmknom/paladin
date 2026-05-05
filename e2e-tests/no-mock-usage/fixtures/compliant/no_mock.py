"""Mock を使用しない準拠フィクスチャ"""

import os


def get_cwd() -> str:  # paladin: ignore[no-module-level-function]
    return os.getcwd()
