def process(items: list[int]) -> list[int]:
    results = []
    for item in items:              # depth 1
        if item > 0:                # depth 2
            for sub in range(item): # depth 3 -- 違反
                results.append(sub)
    return results
