from enum import Enum


class Keys(str, Enum):
    KEY: str = "key"
    KEY_1: str = "random"


KEY_LOCK = Keys.KEY + "-lock"
