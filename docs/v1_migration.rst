..  _v1_migration:

Migrating from v0.x to v1
======

The v1 release of aiocache is a major release that introduces several breaking changes.

Changes to Cache Instantiation
---------

The abstraction and factories around cache instantiation have been removed in favor of a more direct approach.

* The `aiocache.Cache` class has been removed. Instead, use the specific cache class directly. For example, use `aiocache.RedisCache` instead of `aiocache.Cache.REDIS`.
* Caches should be fully instantiated when passed to decorators, rather than being instantiated with a factory function:
* Cache aliases have been removed. Create an instance of the cache class directly instead.

