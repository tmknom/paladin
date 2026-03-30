"""ローカルインポートを使用する違反フィクスチャ"""


def greet() -> str:
    import json
    return json.dumps({"message": "hello"})
