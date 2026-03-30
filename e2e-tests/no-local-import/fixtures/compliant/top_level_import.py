"""トップレベルインポートを使用する準拠フィクスチャ"""

import json
import os


def greet() -> str:
    return json.dumps({"message": os.getcwd()})
