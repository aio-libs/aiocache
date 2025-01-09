..  _v1_migration:

Migrating from v0.x to v1
======

The v1 release of aiocache is a major release that introduces several breaking changes.

Changes to Cache Instantiation
---------

The abstraction and factories around cache instantiation have been removed in favor of a more direct approach.

* The `aiocache.Cache` class has been removed. Instead, use the specific cache class directly. For example, use `aiocache.backends.redis` instead of `aiocache.Cache("simplememory")`.
