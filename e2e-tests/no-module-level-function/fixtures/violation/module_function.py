"""モジュールレベル関数の違反フィクスチャ"""


def calc_file_length(source: str) -> int:  # 違反: モジュールレベルに関数が定義されている
    if not source:
        return 0
    return len(source.splitlines())
