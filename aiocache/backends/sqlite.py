import asyncio
import aiosqlite
from time import time

from aiocache.base import BaseCache
from aiocache.serializers import JsonSerializer


class SQLiteBackend:
    def __init__(self, filename=":memory:", cache_expire_interval=0, **kwargs):
        self._db = None
        self.__db_lock = None
        self._filename = filename
        self._next_expire_at = None
        self._cache_expire_interval = cache_expire_interval
        super().__init__(**kwargs)
        # print("Namespace=", self.namespace)

    def _register_expire(self, when):
        if when is not None:
            if self._next_expire_at is None or self._next_expire_at > when:
                self._next_expire_at = when
                # print("Next cleanup in", when - time())
    @property
    def _db_lock(self):
        if self.__db_lock is None:
            self.__db_lock = asyncio.Lock()
        return self.__db_lock

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def open(self):
        async with self._db_lock:
            await self._ensure_connected()

    async def close(self):
        async with self._db_lock:
            if self._db is not None:
                await self._db.close()
                self._db = None

    async def clear_expired(self):
        async with self._db_lock:
            await self._ensure_connected()
            return await self._remove_expired(force=True)

    async def _clear_expired(self, force=False):
        now = time()
        if not force:
            if self._next_expire_at is None or self._next_expire_at >= now + self._cache_expire_interval:
                # It is too soon to expired data yet
                return 0

        # Delete expired entries
        async with self._db.execute("DELETE FROM aiocache WHERE expires_at < ?", (now, )) as cursor:
            num_deleted = cursor.rowcount

        # Get time of next expiration (So that we don't clear expired entries too soon)
        async with self._db.execute('SELECT MIN(expires_at) FROM aiocache WHERE expires_at IS NOT NULL') as cursor:
            result = await cursor.fetchone()
            self._next_expire_at = result[0] if result else None

        await self._db.commit()

        # print("Expired", num_deleted, "records -- Next cleanup in", "---" if self._next_expire_at is None else self._next_expire_at - now)
        return num_deleted

    async def _ensure_connected(self):
        if self._db is None:
            self._db = await aiosqlite.connect(self._filename)
            await self._db.execute("""
                    CREATE TABLE IF NOT EXISTS aiocache (
                        key TEXT NOT NULL PRIMARY KEY,
                        value BLOB NOT NULL,
                        expires_at REAL
                    );
            """)
            await self._db.execute("""
                    CREATE INDEX IF NOT EXISTS cache_expires_at_idx ON aiocache(expires_at);
            """)
            await self._clear_expired(force=True)
        else:
            # Already connected
            await self._clear_expired()  # Good opportunity to invalidate old data



    async def _get(self, key, encoding="utf-8", _conn=None):
        return (await self._multi_get([key], encoding=encoding, _conn=_conn))[0]

    async def _gets(self, key, encoding="utf-8", _conn=None):
        return await self._get(key, encoding=encoding, _conn=_conn)

    async def _multi_get(self, keys, encoding="utf-8", _conn=None):
        async with self._db_lock:
            await self._ensure_connected()

            now = time()
            sql = 'SELECT key, value FROM aiocache WHERE key IN (' + ','.join(['?'] * len(keys)) + ') AND ((expires_at IS NULL) OR (expires_at >= ?))'
            sql_params = tuple(keys) + (now,)
            async with self._db.execute(sql, sql_params) as cursor:
                result = {}
                async for row in cursor:
                    key, value = row
                    if encoding is not None and isinstance(value, bytes):
                        value = value.decode(encoding)
                    result[key] = value
                # print("get:", result)
                return [
                    result.get(key, None)
                    for key in keys
                ]

    async def _multi_set_impl(self, pairs, ttl, encoding="utf-8", replace=True):
        # print("set:", repr(dict(pairs)), "ttl=", ttl)
        async with self._db_lock:
            await self._ensure_connected()

            expires_at = None if ttl is None else time() + ttl
            try:
                for key, value in pairs:
                    if encoding is not None and isinstance(encoding, str):
                        value = value.encode(encoding)

                    try:
                        await self._db.execute(
                            ('INSERT OR REPLACE' if replace else 'INSERT') +
                            ' INTO aiocache(key, value, expires_at) VALUES (?, ?, ?)',
                            (key, value, expires_at,))
                    except aiosqlite.IntegrityError:
                        raise ValueError("Key {} already exists, use .set to update the value".format(key))
                await self._db.commit()
                self._register_expire(expires_at)
                return True
            except:
                await self._db.rollback()
                raise

    async def _set(self, key, value, ttl=None, _cas_token=None, _conn=None):
        return await self._multi_set_impl([(key, value)], ttl=ttl, replace=True)

    async def _multi_set(self, pairs, ttl=None, _conn=None):
        return await self._multi_set_impl(pairs, ttl=ttl, replace=True)

    async def _add(self, key, value, ttl=None, _conn=None):
        return await self._multi_set_impl([(key, value)], ttl=ttl, replace=False)

    async def _exists(self, key, _conn=None):
        async with self._db_lock:
            await self._ensure_connected()

            now = time()
            async with self._db.execute('SELECT NULL FROM aiocache WHERE key = ? AND ((expires_at IS NULL) OR (expires_at >= ?))', (key, now,)) as cursor:
                row = await cursor.fetchone()
                # print("exist:", key, "is", row is not None)
                return row is not None

    async def _increment(self, key, delta, _conn=None):
        async with self._db_lock:
            await self._ensure_connected()

            now = time()
            async with self._db.execute('SELECT VALUE FROM aiocache WHERE key = ? AND ((expires_at IS NULL) OR (expires_at >= ?))', (keys, now,)) as cursor:
                row = await cursor.fetchone()
                if row is not None:
                    try:
                        old_value = int(row[0])
                    except ValueError:
                        raise TypeError("Value is not an integer") from None
                else:
                    old_value = 0

            new_value = old_value + delta
            # print("increment:", key, "=>", new_value)
            expires_at = None  # Disable expiration
            try:
                await self._db.execute(
                        'INSERT OR REPLACE INTO aiocache(key, value, expires_at) VALUES (?, ?, ?)',
                        (key, new_value, expires_at,))
                await self._db.commit()
                return new_value
            except:
                await self._db.rollback()
                raise

    async def _expire(self, key, ttl, _conn=None):
        if ttl == 0:
            ttl = None

        # print("expire:", key)
        async with self._db_lock:
            await self._ensure_connected()

            expires_at = None if ttl is None else time() + ttl
            try:
                async with self._db.execute('UPDATE aiocache SET expires_at = ? WHERE key = ?', (expires_at, key)) as cursor:
                    ret = cursor.rowcount != 0
                await self._db.commit()
                self._register_expire(expires_at)
                return ret
            except:
                await self._db.rollback()
                raise


    async def _delete(self, key, _conn=None):
        # print("delete:", key)
        async with self._db_lock:
            await self._ensure_connected()

            try:
                async with self._db.execute('DELETE FROM aiocache WHERE key = ?', (key,)) as cursor:
                    ret = cursor.rowcount
                await self._db.commit()
                return ret
            except:
                await self._db.rollback()
                raise

    async def _clear(self, namespace=None, _conn=None):
        # print("clear:", namespace)
        prefix = self._build_key(namespace, '')
        escaped_prefix = re.sub(r"([%_@])", r"@\1", prefix)

        async with self._db_lock:
            await self._ensure_connected()

            try:
                await self._db.execute('DELETE FROM aiocache WHERE key LIKE ? ESCAPE "@"', (escaped_prefix,))
                await self._db.commit()
                return True
            except:
                await self._db.rollback()
                raise

    async def _raw(self, command, *args, encoding="utf-8", _conn=None, **kwargs):
        # print("raw:", command)
        async with self._db_lock:
            await self._ensure_connected()

            async with self._db.execute(command, *args, **kwargs) as  cursor:
                ret = await cursor.fetchall()

            await self._db.commit()
            return ret

    def _build_key(self, key, namespace=None):
        ns = namespace if namespace is not None else self.namespace
        prefix = repr(ns) if ns is not None else ""
        return prefix + ":" + key



class SQLiteCache(SQLiteBackend, BaseCache):
    """
    Memory cache implementation with the following components as defaults:
        - serializer: :class:`aiocache.serializers.JsonSerializer`
        - plugins: None

    Config options are:

    :param serializer: obj derived from :class:`aiocache.serializers.BaseSerializer`.
    :param plugins: list of :class:`aiocache.plugins.BasePlugin` derived classes.
    :param namespace: string to use as default prefix for the key used in all operations of
        the backend. Default is None.
    :param timeout: int or float in seconds specifying maximum timeout for the operations to last.
        By default its 5.
    """

    NAME = "sqlite"

    def __init__(self, serializer=None, **kwargs):
        super().__init__(**kwargs)
        self.serializer = serializer or JsonSerializer()

    @classmethod
    def parse_uri_path(cls, path):
        return {"filename": path}
