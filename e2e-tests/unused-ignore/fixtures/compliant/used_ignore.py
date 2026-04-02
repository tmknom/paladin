"""Used ignore fixture."""


def foo():
    import os  # paladin: ignore[no-local-import]
    return os.getcwd()
