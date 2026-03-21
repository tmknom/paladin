__all__: list[str] = ["Handler"]

from myapp.check.context import CheckContext  # 違反: check は allow-dirs に含まれない


class Handler:
    def __init__(self, context: CheckContext) -> None:
        self._context = context
