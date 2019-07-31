# CHANGELOG


## 0.11.1 (2019-07-31)

* Don't hardcode import redis and memcached in factory [#461](https://github.com/argaen/aiocache/issues/461) - Manuel Miranda


## 0.11.0 (2019-07-31)

* Support str for timeout and ttl [#454](https://github.com/argaen/aiocache/issues/454) - Manuel Miranda

* Add aiocache_wait_for_write decorator param [#448](https://github.com/argaen/aiocache/issues/448) - Manuel Miranda

* Extend and improve usage of Cache class [#446](https://github.com/argaen/aiocache/issues/446) - Manuel Miranda

* Add caches.add functionality [#440](https://github.com/argaen/aiocache/issues/440) - Manuel Miranda

* Use raw msgpack attribute for loads [#439](https://github.com/argaen/aiocache/issues/439) - Manuel Miranda

* Add docs regarding plugin timeouts and multicached [#438](https://github.com/argaen/aiocache/issues/438) - Manuel Miranda

* Fix typehints in lock.py [#434](https://github.com/argaen/aiocache/issues/434) - Aviv

* Use pytest_configure instead of pytest_namespace [#436](https://github.com/argaen/aiocache/issues/436) - Manuel Miranda

* Add Cache class factory [#430](https://github.com/argaen/aiocache/issues/430) - Manuel Miranda


## 0.10.1 (2018-11-15)

* Cancel the previous ttl timer if exists when setting a new value in the in-memory cache [#424](https://github.com/argaen/aiocache/issues/424) - Minh Tu Le

* Add python 3.7 to CI, now its supported! [#420](https://github.com/argaen/aiocache/issues/420) - Manuel Miranda

* Add function as parameter for key_builder [#417](https://github.com/argaen/aiocache/issues/417) - Manuel Miranda

* Always use __name__ when getting logger [#412](https://github.com/argaen/aiocache/issues/412) - Mansur Mamkin

* Format code with black [#410](https://github.com/argaen/aiocache/issues/410) - Manuel Miranda


## 0.10.0 (2018-06-17)

* Cache can be disabled in decorated functions using `cache_read` and `cache_write` [#404](https://github.com/argaen/aiocache/issues/404) - Josep Cugat

* Cache constructor can receive now default ttl [#405](https://github.com/argaen/aiocache/issues/405) - Josep Cugat
## 0.9.1 (2018-04-27)

* Single deploy step [#395](https://github.com/argaen/aiocache/issues/395) - Manuel Miranda

* Catch ImportError when importing optional msgpack [#398](https://github.com/argaen/aiocache/issues/398) - Paweł Kowalski

* Lazy load redis asyncio.Lock [#397](https://github.com/argaen/aiocache/issues/397) - Jordi Soucheiron


## 0.9.0 (2018-04-24)

* Bug #389/propagate redlock exceptions [#394](https://github.com/argaen/aiocache/issues/394) - Manuel Miranda
  ___aexit__ was returning whether asyncio Event was removed or not. In
some cases this was avoiding the context manager to propagate
exceptions happening inside. Now its not returning anything and will
raise always any exception raised from inside_

* Fix sphinx build [#392](https://github.com/argaen/aiocache/issues/392) - Manuel Miranda
  _Also add extra step in build pipeline to avoid future errors._

* Update alias config when config already exists [#383](https://github.com/argaen/aiocache/issues/383) - Josep Cugat

* Ensure serializers are instances [#379](https://github.com/argaen/aiocache/issues/379) - Manuel Miranda

* Add MsgPackSerializer [#370](https://github.com/argaen/aiocache/issues/370) - Adam Hopkins

* Add create_connection_timeout for redis>=1.0.0 when creating connections [#368](https://github.com/argaen/aiocache/issues/368) - tmarques82

* Fixed spelling error in serializers.py [#371](https://github.com/argaen/aiocache/issues/371) - Jared Shields


## 0.8.0 (2017-11-08)

* Add pypy support in build pipeline [#359](https://github.com/argaen/aiocache/issues/359) - Manuel Miranda

* Fix multicached bug when using keys as an arg rather than kwarg [#356](https://github.com/argaen/aiocache/issues/356) - Manuel Miranda

* Reuse cache when using decorators with alias [#355](https://github.com/argaen/aiocache/issues/355) - Manuel Miranda

* Cache available from function.cache object for decorated functions [#354](https://github.com/argaen/aiocache/issues/354) - Manuel Miranda

* aioredis and aiomcache are now optional dependencies [#337](https://github.com/argaen/aiocache/issues/337) - Jair Henrique

* Generate wheel package on release [#338](https://github.com/argaen/aiocache/issues/338) - Jair Henrique

* Add key_builder param to caches to customize keys [#315](https://github.com/argaen/aiocache/issues/315) - Manuel Miranda


## 0.7.2 (2017-07-23)

#### Other

* Add key_builder param to caches to customize keys [#310](https://github.com/argaen/aiocache/issues/310) - Manuel Miranda

* Propagate correct message on memcached connector error [#309](https://github.com/argaen/aiocache/issues/309) - Manuel Miranda



## 0.7.1 (2017-07-15)


* Remove explicit loop usages [#305](https://github.com/argaen/aiocache/issues/305) - Manuel Miranda

* Remove bad logging configuration [#304](https://github.com/argaen/aiocache/issues/304) - Manuel Miranda


## 0.7.0 (2017-07-01)

* Upgrade to aioredis 0.3.3. - Manuel Miranda

* Get CMD now returns values that evaluate to False correctly [#282](https://github.com/argaen/aiocache/issues/282) - Manuel Miranda

* New locks public API exposed [#279](https://github.com/argaen/aiocache/issues/279) - Manuel Miranda
  _Users can now use aiocache.lock.RedLock and
aiocache.lock.OptimisticLock_

* Memory now uses new NullSerializer [#273](https://github.com/argaen/aiocache/issues/273) - Manuel Miranda
  _Memory is a special case and doesn't need a serializer  because
anything can be stored in memory. Created a new  NullSerializer that
does nothing which is the default  that SimpleMemoryCache will use
now._

* Multi_cached can use args for key_from_attr [#271](https://github.com/argaen/aiocache/issues/271) - Manuel Miranda
  _before only params defined in kwargs where working due to the
behavior defined in _get_args_dict function. This has now been  fixed
and it behaves as expected._

* Removed cached key_from_attr [#274](https://github.com/argaen/aiocache/issues/274) - Manuel Miranda
  _To reproduce the same behavior, use the new `key_builder` attr_

* Removed settings module. - Manuel Miranda

## 0.6.1 (2017-06-12)

#### Other

* Removed connection reusage for decorators [#267](https://github.com/argaen/aiocache/issues/267)- Manuel Miranda (thanks @dmzkrsk)
  _when decorated function is costly connections where being kept while
being iddle. This is a bad scenario and this reverts back to using a
connection from the cache pool for every cache operation_

* Key_builder for cached [#265](https://github.com/argaen/aiocache/issues/265) - Manuel Miranda
  _Also fixed a bug with multi_cached where key_builder wasn't  applied
when saving the keys_

* Updated aioredis (0.3.1) and aiomcache (0.5.2) versions - Manuel Miranda



## 0.6.0 (2017-06-05)

#### New

* Cached supports stampede locking [#249](https://github.com/argaen/aiocache/issues/249) - Manuel Miranda

* Memory redlock implementation [#241](https://github.com/argaen/aiocache/issues/241) - Manuel Miranda

* Memcached redlock implementation [#240](https://github.com/argaen/aiocache/issues/240) - Manuel Miranda

* Redis redlock implementation [#235](https://github.com/argaen/aiocache/issues/235) - Manuel Miranda

* Add close function to clean up resources [#236](https://github.com/argaen/aiocache/issues/236) - Quinn Perfetto

  _Call `await cache.close()` to close a pool and its connections_

* `caches.create` works without alias [#253](https://github.com/argaen/aiocache/issues/253) - Manuel Miranda


#### Changes

* Decorators use JsonSerializer by default now [#258](https://github.com/argaen/aiocache/issues/258) - Manuel Miranda

  _Also renamed DefaultSerializer to StringSerializer_

* Decorators use single connection [#257](https://github.com/argaen/aiocache/issues/257) - Manuel Miranda

  _Decorators (except cached_stampede) now use a single connection for
each function call. This means connection doesn't go back to the pool
after each cache call. Since the cache instance is the same for a
decorated function, this means that the pool size must be high if
there is big expected concurrency for that given function_

* Change close to clear for redis [#239](https://github.com/argaen/aiocache/issues/239) - Manuel Miranda

  _clear will free connections but will allow the user to still use the
cache if needed (same behavior for  aiomcache and ofc memory)_


## 0.5.2

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

#### Breaking

* Refactored how settings and defaults work. Now
  aliases are the only way. [#193](https://github.com/argaen/aiocache/issues/193) [argaen]
* Consistency between backends and serializers. With
  SimpleMemoryCache, some data will change on how its stored
  when using DefaultSerializer [#191](https://github.com/argaen/aiocache/issues/191) [argaen]


## 0.3.3 (2017-04-06)

* Added CHANGELOG and release process [#172](https://github.com/argaen/aiocache/issues/172) [argaen]
* Added pool_min_size pool_max_size to redisbackend [#167](https://github.com/argaen/aiocache/issues/167) [argaen]
* Timeout per function. Propagate it correctly with defaults. [#166](https://github.com/argaen/aiocache/issues/166) [argaen]
* Added noself arg to cached decorator [#137](https://github.com/argaen/aiocache/issues/137) [argaen]
* Cache instance in decorators is built in every call [#135](https://github.com/argaen/aiocache/issues/135) [argaen]


## 0.3.1 (2017-02-13)

* Changed add redis to use set with not existing flag [#119](https://github.com/argaen/aiocache/issues/119) [argaen]
* Memcached multi_set with ensure_future [#114](https://github.com/argaen/aiocache/issues/114) [argaen]


## 0.3.0 (2017-01-12)

* Fixed asynctest issues for timeout tests [#109](https://github.com/argaen/aiocache/issues/109) [argaen]
* Created new API class [#108](https://github.com/argaen/aiocache/issues/108)
  [argaen]
* Set multicached keys only when non existing [#98](https://github.com/argaen/aiocache/issues/98) [argaen]
* Added expire command [#97](https://github.com/argaen/aiocache/issues/97) [argaen]
* Ttl tasks are cancelled for memory backend if key is deleted [#92](https://github.com/argaen/aiocache/issues/92) [argaen]
* Ignore caching if AIOCACHE_DISABLED is set to 1 [#90](https://github.com/argaen/aiocache/issues/90) [argaen]
