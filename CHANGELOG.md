# Changelog


## 0.5.2 (2017-05-15)
* Reuse connection context manager [#225](https://github.com/Manuel Miranda/aiocache/issues/225) [Manuel Miranda]
* Add performance footprint tests [#228](https://github.com/Manuel Miranda/aiocache/issues/228) [Manuel Miranda]
* Timeout=0 takes precedence over self.timeout [#227](https://github.com/Manuel Miranda/aiocache/issues/227) [Manuel Miranda]
* Lock when acquiring redis connection [#224](https://github.com/Manuel Miranda/aiocache/issues/224) [Manuel Miranda]
* Added performance concurrency tests [#216](https://github.com/Manuel Miranda/aiocache/issues/216) [Manuel Miranda]


## 0.5.1

* Deprecate settings module [#215](https://github.com/Manuel Miranda/aiocache/issues/215) [Manuel Miranda]
* Decorators support introspection [#213](https://github.com/Manuel Miranda/aiocache/issues/213) [Manuel Miranda]


## 0.5.0 (2017-04-29)

* Removed pool reusage for redis. A new one
  is created for each instance [Manuel Miranda]
* Soft dependencies for redis and memcached [#197](https://github.com/Manuel Miranda/aiocache/issues/197) [Manuel Miranda]
* Added incr CMD [#188](https://github.com/Manuel Miranda/aiocache/issues/188>) [Manuel
  Miranda]
* Create factory accepts cache args [#209](https://github.com/Manuel Miranda/aiocache/issues/209) [Manuel Miranda]
* Cached and multi_cached can use alias caches (creates new instance per call) [#205](https://github.com/Manuel Miranda/aiocache/issues/205) [Manuel Miranda]
* Method ``create`` to create new instances from alias [#204](https://github.com/Manuel Miranda/aiocache/issues/204) [Manuel Miranda]
* Remove unnecessary warning [#200](https://github.com/Manuel Miranda/aiocache/issues/200) [Petr Timofeev]
* Add asyncio trove classifier [#199](https://github.com/Manuel Miranda/aiocache/issues/199) [Thanos Lefteris]
* Pass pool_size to the underlayed aiomcache [#189](https://github.com/Manuel Miranda/aiocache/issues/189) [Aurélien Busi]
* Added marshmallow example [#181](https://github.com/Manuel Miranda/aiocache/issues/181) [Manuel Miranda]
* Added example for compression serializer [#179](https://github.com/Manuel Miranda/aiocache/issues/179) [Manuel Miranda]
* Added BasePlugin.add_hook helper [#173](https://github.com/Manuel Miranda/aiocache/issues/173) [Manuel Miranda]

### Breaking

* Refactored how settings and defaults work. Now
  aliases are the only way. [#193](https://github.com/Manuel Miranda/aiocache/issues/193) [Manuel Miranda]
* Consistency between backends and serializers. With
  SimpleMemoryCache, some data will change on how its stored
  when using DefaultSerializer [#191](https://github.com/Manuel Miranda/aiocache/issues/191) [Manuel Miranda]


# 0.3.3 (2017-04-06)

* Added CHANGELOG and release process [#172](https://github.com/Manuel Miranda/aiocache/issues/172) [Manuel Miranda]
* Added pool_min_size pool_max_size to redisbackend [#167](https://github.com/Manuel Miranda/aiocache/issues/167) [Manuel Miranda]
* Timeout per function. Propagate it correctly with defaults. [#166](https://github.com/Manuel Miranda/aiocache/issues/166) [Manuel Miranda]
* Added noself arg to cached decorator [#137](https://github.com/Manuel Miranda/aiocache/issues/137) [Manuel Miranda]
* Cache instance in decorators is built in every call [#135](https://github.com/Manuel Miranda/aiocache/issues/135) [Manuel Miranda]


# 0.3.1 (2017-02-13)

* Changed add redis to use set with not existing flag [#119](https://github.com/Manuel Miranda/aiocache/issues/119) [Manuel Miranda]
* Memcached multi_set with ensure_future [#114](https://github.com/Manuel Miranda/aiocache/issues/114) [Manuel Miranda]


# 0.3.0 (2017-01-12)

* Fixed asynctest issues for timeout tests [#109](https://github.com/Manuel Miranda/aiocache/issues/109) [Manuel Miranda]
* Created new API class [#108](https://github.com/Manuel Miranda/aiocache/issues/108)
  [Manuel Miranda]
* Enhancement #94/increase unit test coverage [#106](https://github.com/Manuel Miranda/aiocache/issues/106) [Manuel Miranda]
* Enhancement #94/increase unit test coverage [#102](https://github.com/Manuel Miranda/aiocache/issues/102) [Manuel Miranda]
* Enhancement #94/increase unit test coverage [#101](https://github.com/Manuel Miranda/aiocache/issues/101) [Manuel Miranda]
* Set multicached keys only when non existing [#98](https://github.com/Manuel Miranda/aiocache/issues/98) [Manuel Miranda]
* Added expire command [#97](https://github.com/Manuel Miranda/aiocache/issues/97) [Manuel Miranda]
* Ttl tasks are cancelled for memory backend if key is deleted [#92](https://github.com/Manuel Miranda/aiocache/issues/92) [Manuel Miranda]
* Ignore caching if AIOCACHE_DISABLED is set to 1 [#90](https://github.com/Manuel Miranda/aiocache/issues/90) [Manuel Miranda]
