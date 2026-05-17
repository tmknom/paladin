"""5引数メソッドを含む違反フィクスチャ"""


class UserService:
    def create_user(
        self,
        name: str,
        email: str,
        age: int,
        role: str,
        phone: str,
    ) -> None:  # 違反: self を除いて 5 引数で上限 4 を超過
        pass
