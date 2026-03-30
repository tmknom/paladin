"""__all__ を持たない準拠フィクスチャ"""

import os


def greet() -> str:
    return os.getcwd()
