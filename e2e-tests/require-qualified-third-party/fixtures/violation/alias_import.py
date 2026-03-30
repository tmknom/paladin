"""エイリアスインポートを使用する違反フィクスチャ"""

import pydantic as pyd


class MyModel(pyd.BaseModel):
    """モデルクラス"""

    name: str
