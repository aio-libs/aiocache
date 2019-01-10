import logging

from .serializers import (
    BaseSerializer,
    NullSerializer,
    StringSerializer,
    PickleSerializer,
    JsonSerializer,
)

logger = logging.getLogger(__name__)


try:
    import msgpack
except ImportError:
    logger.debug("msgpack not installed, MsgPackSerializer unavailable")
else:
    from .serializers import MsgPackSerializer

    del msgpack


__all__ = [
    "BaseSerializer",
    "NullSerializer",
    "StringSerializer",
    "PickleSerializer",
    "JsonSerializer",
    "MsgPackSerializer",
]
