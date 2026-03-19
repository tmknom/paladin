"""pydantic-settingsベースの環境変数設定基底

環境変数から設定値を読み込むモデルが継承すべき基底クラス。
大小文字の正規化、未知キーの拒否を共通設定として一元化する。
"""

import pydantic_settings

SettingsConfigDict = pydantic_settings.SettingsConfigDict


class CoreSettings(pydantic_settings.BaseSettings):
    """環境変数設定の共通基底クラス

    Configuration:
        - case_sensitive=False: 環境変数名の大小文字を区別しない
        - extra="forbid": 定義外の環境変数キーを受け入れず、エラーとする
    """

    model_config = pydantic_settings.SettingsConfigDict(
        case_sensitive=False,
        extra="forbid",
    )
