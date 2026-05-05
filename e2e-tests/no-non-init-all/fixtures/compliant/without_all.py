"""__all__ を持たない準拠フィクスチャ"""

import os


def greet() -> str:  # paladin: ignore[no-module-level-function]
    return os.getcwd()
