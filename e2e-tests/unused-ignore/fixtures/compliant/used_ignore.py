"""Used ignore fixture."""


def foo():  # paladin: ignore[no-module-level-function]
    import os  # paladin: ignore[no-local-import]
    return os.getcwd()
