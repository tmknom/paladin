"""pydanticベースの共通モデル基底

全ドメインモデルが継承すべき基底クラス。
不変性、厳格性、堅牢性を保証する設定を一元化する。
"""

from pydantic import BaseModel, ConfigDict


class CoreModel(BaseModel):
    """不変かつ厳格なpydanticモデル基底

    Configuration:
        - extra="forbid": 定義外のフィールドを受け入れず、エラーとする
        - populate_by_name=True: aliasと内部名のどちらでもデシリアライズ可能
        - str_strip_whitespace=True: 文字列フィールドの前後空白を自動除去
        - frozen=True: インスタンス生成後の変更を禁止（不変オブジェクト）
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
        frozen=True,
    )
