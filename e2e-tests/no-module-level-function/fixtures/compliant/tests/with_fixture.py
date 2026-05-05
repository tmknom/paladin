"""pytest.fixture デコレータ付き関数の準拠フィクスチャ"""


@pytest.fixture  # noqa: F821 - paladin の AST 解析が対象（実行は不要）
def tmp_source() -> str:  # 準拠: @pytest.fixture は許可リストに含まれる
    return "x = 1\n"
