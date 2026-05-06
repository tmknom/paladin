"""3引数以内のメソッドのみの準拠フィクスチャ"""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserProfile:
    """ユーザープロフィールのバリューオブジェクト"""

    name: str
    email: str
    age: int


class UserService:
    """ユーザー管理サービス"""

    def create_user(self, profile: UserProfile) -> None:  # 準拠: 1引数
        pass
