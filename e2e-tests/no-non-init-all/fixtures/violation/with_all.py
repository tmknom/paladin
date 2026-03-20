import os

__all__ = ["greet"]


def greet() -> str:
    return os.getcwd()
