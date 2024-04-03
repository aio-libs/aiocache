from typing import (
    Any,
    Callable,
    Concatenate,
    Mapping,
    ParamSpec,
    Protocol,
    Sequence,
    Type,
    TypeVar,
    overload,
)

from aiocache import BaseCache, Cache
from aiocache.plugins import BasePlugin
from aiocache.serializers import BaseSerializer

Params = ParamSpec("Params")
ReturnType = TypeVar("ReturnType")
DecoratorKWArgs = TypeVar("DecoratorKWArgs")
SerializerType = TypeVar("SerializerType", bound=BaseSerializer)
CacheType = TypeVar("CacheType", bound=BaseCache)
MCReturnType = TypeVar("MCReturnType", bound=Mapping)
MCKey = TypeVar("MCKey")
MCVal = TypeVar("MCVal")

class CachedDecorator(Protocol[Params, ReturnType]):
    def __call__(
        self,
        *args: Params.args,
        cache_read: bool = True,
        cache_write: bool = True,
        aiocache_wait_for_write: bool = True,
        **kwargs: Params.kwargs,
    ) -> ReturnType: ...

class CachedDecorated(CachedDecorator[CacheType, Params, ReturnType]):
    cache: CacheType

class cached:
    ttl: int | None
    key_builder: Callable[Params, str] | None
    skip_cache_func: Callable[[ReturnType], bool] | None
    noself: bool
    alias: str | None
    cache: None

    decorator: CachedDecorator[Params, ReturnType]

    _cache: CacheType
    _serializer: SerializerType
    _namespace: str | None
    _plugins: Sequence[BasePlugin] | None
    _kwargs: dict[str, DecoratorKWArgs]

    @overload
    def __init__(
        self,
        ttl: int | None = None,
        *,
        key_builder: Callable[Params, str] | None = None,
        skip_cache_func: Callable[[ReturnType], bool] | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        noself: bool = False,
        alias: str,
        **kwargs: DecoratorKWArgs,
    ): ...
    @overload
    def __init__(
        self,
        ttl: int | None = None,
        *,
        key_builder: Callable[Params, str] | None = None,
        skip_cache_func: Callable[[ReturnType], bool] | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        noself: bool = False,
        namespace: str | None = None,
        serializer: SerializerType | None = None,
        plugins: Sequence[BasePlugin] | None = None,
        alias: None = None,
        **kwargs: DecoratorKWArgs,
    ): ...
    def __call__(
        self, fn: Callable[Params, ReturnType]
    ) -> CachedDecorated[CacheType, Params, ReturnType]: ...
    def get_cache_key(self, *args: Params.args, **kwargs: Params.kwargs) -> str: ...
    async def get_from_cache(self, key: str) -> ReturnType | None: ...
    async def set_in_cache(self, key: str, value: ReturnType) -> None: ...

class cached_stampede(cached):
    lease: int

    @overload
    def __init__(
        self,
        lease: int = 2,
        ttl: int | None = None,
        *,
        key_builder: Callable[Params, str] | None = None,
        skip_cache_func: Callable[[ReturnType], bool] | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        noself: bool = False,
        alias: str,
        **kwargs: DecoratorKWArgs,
    ) -> CachedDecorated[CacheType, Params, ReturnType]: ...
    @overload
    def __init__(
        self,
        lease: int = 2,
        ttl: int | None = None,
        *,
        key_builder: Callable[Params, str] | None = None,
        skip_cache_func: Callable[[ReturnType], bool] | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        noself: bool = False,
        namespace: str | None = None,
        serializer: SerializerType | None = None,
        plugins: Sequence[BasePlugin] | None = None,
        alias: None = None,
        **kwargs: DecoratorKWArgs,
    ) -> CachedDecorated[CacheType, Params, ReturnType]: ...

class multi_cached:
    keys_from_attr: str
    key_builder: Callable[Concatenate[MCKey, Callable[Params, MCReturnType], Params], str] | None
    skip_cache_func: Callable[[MCKey, MCVal], bool] | None
    ttl: int | None
    alias: str | None
    cache: None

    decorator: CachedDecorator[Params, MCReturnType]

    _cache: CacheType
    _serializer: SerializerType
    _namespace: str | None
    _plugins: Sequence[BasePlugin] | None
    _kwargs: dict[str, DecoratorKWArgs]

    @overload
    def __init__(
        self,
        keys_from_attr: str,
        *,
        key_builder: (
            Callable[Concatenate[MCKey, Callable[Params, ReturnType], Params], str] | None
        ) = None,
        skip_cache_func: Callable[[MCKey, MCVal], bool] | None = None,
        ttl: int | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        alias: str,
        **kwargs: DecoratorKWArgs,
    ): ...
    @overload
    def __init__(
        self,
        keys_from_attr: str,
        *,
        namespace: str | None = None,
        key_builder: (
            Callable[Concatenate[MCKey, Callable[Params, ReturnType], Params], str] | None
        ) = None,
        skip_cache_func: Callable[[MCKey, MCVal], bool] | None = None,
        ttl: int | None = None,
        cache: Type[CacheType] = Cache.MEMORY,
        serializer: SerializerType | None = None,
        plugins: Sequence[BasePlugin] | None = None,
        alias: None = None,
        **kwargs: DecoratorKWArgs,
    ): ...
    def __call__(
        self, fn: Callable[Params, ReturnType]
    ) -> CachedDecorated[CacheType, Params, MCReturnType]: ...
    def get_cache_keys(
        self, f: Callable[Params, ReturnType], *args: Params.args, **kwargs: Params.kwargs
    ) -> str: ...
    async def get_from_cache(self, *keys: MCKey) -> list[MCVal | None]: ...
    async def set_in_cache(
        self,
        result: MCReturnType[MCKey, MCVal],
        fn: Callable[Params, ReturnType],
        fn_args: Params.args,
        fn_kwargs: Params.kwargs,
    ) -> None: ...

def __getattr__(name: str) -> Any: ...
