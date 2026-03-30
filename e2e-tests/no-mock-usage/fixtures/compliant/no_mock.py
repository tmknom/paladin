"""Mock を使用しない準拠フィクスチャ"""

import os


def get_cwd() -> str:
    return os.getcwd()
