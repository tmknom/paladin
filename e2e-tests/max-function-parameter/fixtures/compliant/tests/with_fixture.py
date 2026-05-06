"""@pytest.fixture デコレータ付き関数の準拠フィクスチャ"""


@pytest.fixture  # noqa: F821 - paladin の AST 解析が対象（実行は不要）
def user_service(db, cache, mailer, logger, audit):  # 準拠: 5引数だが許可リスト
    return None
