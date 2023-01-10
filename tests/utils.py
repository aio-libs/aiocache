try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class Keys(StrEnum):
    KEY: str = "key"
    KEY_1: str = "random"


KEY_LOCK = Keys.KEY + "-lock"
