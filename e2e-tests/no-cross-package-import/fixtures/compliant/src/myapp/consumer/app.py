__all__: list[str] = ["App"]

from myapp.rule import RuleMeta  # 準拠: rule は allow-dirs に含まれる


class App:
    def __init__(self, meta: RuleMeta) -> None:
        self._meta = meta
