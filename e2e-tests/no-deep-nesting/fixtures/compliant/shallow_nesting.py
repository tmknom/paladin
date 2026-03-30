"""浅いネストの準拠フィクスチャ"""


def process(items: list[int]) -> list[int]:
    results = []
    for item in items:       # depth 1
        if item > 0:         # depth 2
            results.append(item)
    return results
