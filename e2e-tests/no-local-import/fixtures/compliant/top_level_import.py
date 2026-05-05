"""トップレベルインポートを使用する準拠フィクスチャ"""

import json
import os


def greet() -> str:  # paladin: ignore[no-module-level-function]
    return json.dumps({"message": os.getcwd()})
