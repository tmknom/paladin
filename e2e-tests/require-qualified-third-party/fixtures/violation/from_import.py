"""from インポートを使用する違反フィクスチャ"""

from pydantic import BaseModel


class MyModel(BaseModel):
    """モデルクラス"""

    name: str
