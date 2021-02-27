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

try:
    import dill
except ImportError:
    logger.debug("dill not installed, DillSerializer unavailable")
else:
    from .serializers import DillSerializer

    del dill

__all__ = [
    "BaseSerializer",
    "NullSerializer",
    "StringSerializer",
    "PickleSerializer",
    "JsonSerializer",
    "MsgPackSerializer",
    "DillSerializer",
]
