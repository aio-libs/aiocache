__version__ = "1.0.0a0"

from .decorators import cached, cached_stampede, multi_cached  # noqa: E402,I202

__all__ = (
    "cached",
    "cached_stampede",
    "multi_cached",
)
