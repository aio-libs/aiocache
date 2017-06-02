# Changelog


## 0.5.2 (2017-05-15)
* Reuse connection context manager [#225](https://github.com/argaen/aiocache/issues/225) [argaen]
* Add performance footprint tests [#228](https://github.com/argaen/aiocache/issues/228) [argaen]
* Timeout=0 takes precedence over self.timeout [#227](https://github.com/argaen/aiocache/issues/227) [argaen]
* Lock when acquiring redis connection [#224](https://github.com/argaen/aiocache/issues/224) [argaen]
* Added performance concurrency tests [#216](https://github.com/argaen/aiocache/issues/216) [argaen]


## 0.5.1

* Deprecate settings module [#215](https://github.com/argaen/aiocache/issues/215) [argaen]
* Decorators support introspection [#213](https://github.com/argaen/aiocache/issues/213) [argaen]


## 0.5.0 (2017-04-29)

* Removed pool reusage for redis. A new one
  is created for each instance [argaen]
* Soft dependencies for redis and memcached [#197](https://github.com/argaen/aiocache/issues/197) [argaen]
* Added incr CMD [#188](https://github.com/argaen/aiocache/issues/188>) [Manuel
  Miranda]
* Create factory accepts cache args [#209](https://github.com/argaen/aiocache/issues/209) [argaen]
* Cached and multi_cached can use alias caches (creates new instance per call) [#205](https://github.com/argaen/aiocache/issues/205) [argaen]
* Method ``create`` to create new instances from alias [#204](https://github.com/argaen/aiocache/issues/204) [argaen]
* Remove unnecessary warning [#200](https://github.com/argaen/aiocache/issues/200) [Petr Timofeev]
* Add asyncio trove classifier [#199](https://github.com/argaen/aiocache/issues/199) [Thanos Lefteris]
* Pass pool_size to the underlayed aiomcache [#189](https://github.com/argaen/aiocache/issues/189) [Aurélien Busi]
* Added marshmallow example [#181](https://github.com/argaen/aiocache/issues/181) [argaen]
* Added example for compression serializer [#179](https://github.com/argaen/aiocache/issues/179) [argaen]
* Added BasePlugin.add_hook helper [#173](https://github.com/argaen/aiocache/issues/173) [argaen]

### Breaking

* Refactored how settings and defaults work. Now
  aliases are the only way. [#193](https://github.com/argaen/aiocache/issues/193) [argaen]
* Consistency between backends and serializers. With
  SimpleMemoryCache, some data will change on how its stored
  when using DefaultSerializer [#191](https://github.com/argaen/aiocache/issues/191) [argaen]


# 0.3.3 (2017-04-06)

* Added CHANGELOG and release process [#172](https://github.com/argaen/aiocache/issues/172) [argaen]
* Added pool_min_size pool_max_size to redisbackend [#167](https://github.com/argaen/aiocache/issues/167) [argaen]
* Timeout per function. Propagate it correctly with defaults. [#166](https://github.com/argaen/aiocache/issues/166) [argaen]
* Added noself arg to cached decorator [#137](https://github.com/argaen/aiocache/issues/137) [argaen]
* Cache instance in decorators is built in every call [#135](https://github.com/argaen/aiocache/issues/135) [argaen]


# 0.3.1 (2017-02-13)

* Changed add redis to use set with not existing flag [#119](https://github.com/argaen/aiocache/issues/119) [argaen]
* Memcached multi_set with ensure_future [#114](https://github.com/argaen/aiocache/issues/114) [argaen]


# 0.3.0 (2017-01-12)

* Fixed asynctest issues for timeout tests [#109](https://github.com/argaen/aiocache/issues/109) [argaen]
* Created new API class [#108](https://github.com/argaen/aiocache/issues/108)
  [argaen]
* Set multicached keys only when non existing [#98](https://github.com/argaen/aiocache/issues/98) [argaen]
* Added expire command [#97](https://github.com/argaen/aiocache/issues/97) [argaen]
* Ttl tasks are cancelled for memory backend if key is deleted [#92](https://github.com/argaen/aiocache/issues/92) [argaen]
* Ignore caching if AIOCACHE_DISABLED is set to 1 [#90](https://github.com/argaen/aiocache/issues/90) [argaen]
