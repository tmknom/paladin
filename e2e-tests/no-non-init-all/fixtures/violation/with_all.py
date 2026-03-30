"""非 __init__.py で __all__ を定義する違反フィクスチャ"""

import os

__all__ = ["greet"]


def greet() -> str:
    return os.getcwd()
