Changelog
=========


Unreleased
----------
- Added CHANGELOG and release process. [argaen]
- Improvement in getting attrs with fallbacks. [argaen]

  Created a new helper to decide wether to use original value, config
  or default from the class. This will help when the refactor of the
  settings module is done.
- Added pool_min_size pool_max_size to redisbackend `#167
  <https://github.com/argaen/issues/#167>`_ [Manuel Miranda]
- Timeout per function. Propagate it correctly with defaults. `#166
  <https://github.com/argaen/issues/#166>`_ [Manuel Miranda]

  Also solved a bug where memcached multi_set wasn't waiting for
  keys to be inserted.

  Closes #163 and #162
- Added disclaimer regarding the defaults module. [argaen]
- Fixed framework examples. [argaen]
- Update pytest-mock from 1.5.0 to 1.6.0 `#160
  <https://github.com/argaen/issues/#160>`_ [pyup.io bot]
- Removed async-timeout as a dependency. [argaen]
- Updated README. [argaen]
- Added noself arg to cached decorator `#137
  <https://github.com/argaen/issues/#137>`_ [Manuel Miranda]
- 0.3.2 version bump. [argaen]
- Cache instance in decorators is built in every call `#135
  <https://github.com/argaen/issues/#135>`_ [Manuel Miranda]
- Pin tornado to latest version 4.4.2 `#133
  <https://github.com/argaen/issues/#133>`_ [pyup.io bot]

  * Added framework examples

  * Pin tornado to latest version 4.4.2
- Pin aiohttp to latest version 1.3.1 `#132
  <https://github.com/argaen/issues/#132>`_ [pyup.io bot]

  * Added framework examples

  * Pin aiohttp to latest version 1.3.1
- Pin sanic to latest version 0.3.1 `#131
  <https://github.com/argaen/issues/#131>`_ [pyup.io bot]

  * Added framework examples

  * Pin sanic to latest version 0.3.1
- Added framework examples. [argaen]
- Don't use wait_for when no timeout is provided. [argaen]


0.3.1 (2017-02-13)
------------------
- Don't use  when no timeout is provided. [argaen]
- Changed add redis to use set with not existing flag `#119
  <https://github.com/argaen/issues/#119>`_ [Manuel Miranda]
- Fixed typo in docs image. [argaen]
- Increased iterations in examples plugin to avoid test failing.
  [argaen]
- Memcached multi_set with ensure_future `#114
  <https://github.com/argaen/issues/#114>`_ [Manuel Miranda]
- Fixed tests for ujson compatibility execution. [argaen]
- Added back acceptance tests to travis. [argaen]
- Moved cached, multi_cached to new decorators.py module. [argaen]


0.3.0 (2017-01-12)
------------------
- Changed setup.py description. [argaen]
- 0.3.0 version bump. [argaen]
- Fixed asynctest issues for timeout tests `#109
  <https://github.com/argaen/issues/#109>`_ [Manuel Miranda]
- 0.2.3 version bump. [argaen]
- Created new API class `#108 <https://github.com/argaen/issues/#108>`_
  [Manuel Miranda]

  This class is in charge of registering which methods are used as commands,
  disabling the command in case the AIOCACHE_DISABLED variable is set, executing the plugin
  pipeline and the timeout. This is all done with classmethods that can be used
  as decorators.

  * Increased coverage for plugins

  * Added branch coverage in pipeline
- Enhancement #94/increase unit test coverage `#106
  <https://github.com/argaen/issues/#106>`_ [Manuel Miranda]

  * Renamed integration to acceptance

  * Increased coverage of memcached backend
- Fix test failing randomly. [argaen]
- Enhancement #94/increase unit test coverage `#102
  <https://github.com/argaen/issues/#102>`_ [Manuel Miranda]

  Added unit test coverage for redis backend module
- Enhancement #94/increase unit test coverage `#101
  <https://github.com/argaen/issues/#101>`_ [Manuel Miranda]

  * Improved cache.py testing

  * Improved unit tests for memory backend
- Update README. [argaen]
- Set multicached keys only when non existing `#98
  <https://github.com/argaen/issues/#98>`_ [Manuel Miranda]

  * Set multicached keys only when non existing

  * If ttl is 0 for expire, cancel it
- Added expire command `#97 <https://github.com/argaen/issues/#97>`_
  [Manuel Miranda]
- 0.2.2 version bump. [argaen]
- All backend kwargs pull default attributes. [argaen]

  Before only plugins, serializer and namespace attributes were pulling
  the from the default settings in case they were missing when initializing.
  Now attributes like endpoint, db, port, etc. are being pulled too.
- Removed integrtion from coverage. [argaen]

  Integration tests were added to coverage because in the
  beginning there wasn't much logic and everything was tested
  with integration tests only.
- Ttl tasks are cancelled for memory backend if key is deleted `#92
  <https://github.com/argaen/issues/#92>`_ [Manuel Miranda]
- Added extra example in README. [argaen]
- Merge branch 'master' of https://github.com/argaen/aiocache. [argaen]
- Ignore caching if AIOCACHE_DISABLED is set to 1 `#90
  <https://github.com/argaen/issues/#90>`_ [Manuel Miranda]
- 0.2.1 version bump. [argaen]
- Merge branch 'master' of github.com:argaen/aiocache. [argaen]
- Added some docs to plugins. [argaen]


0.2.0 (2016-12-14)
------------------
- 0.2.0 version bump. [argaen]
- Added python version badge. [argaen]
- LRU plugin example. [Manuel Miranda]
- Feature #57/policy to generic hooks `#83
  <https://github.com/argaen/issues/#83>`_ [Manuel Miranda]

  * Replaced policies by plugins

  Policies are replaced by a more generic component called plugins.
  These components allow to introduce new behavior to the class like
  monitoring execution time, hit/miss ratios and more. It still also
  possible to interact directly with the client in case cache
  policies are needed to be implemented

  * Added HitMissRatioPlugin

  * Added TimingPlugin
- Update pytest-mock from 1.4.0 to 1.5.0 `#81
  <https://github.com/argaen/issues/#81>`_ [pyup.io bot]
- Added new test. [argaen]

  check exception propagation for cached and multicached decorators
- Reuse redis pools `#77 <https://github.com/argaen/issues/#77>`_
  [Manuel Miranda]

  * RedisBackend reuses pools

  If a pool is called with the same args as a previous one,
  it will be reused
- Accept str or class types in set_defaults `#75
  <https://github.com/argaen/issues/#75>`_ [Manuel Miranda]
- Increased coverage. [argaen]
- Improved multiple inheritance `#73
  <https://github.com/argaen/issues/#73>`_ [Manuel Miranda]
- Merged backend and cache with multiple inheritance `#72
  <https://github.com/argaen/issues/#72>`_ [Manuel Miranda]
- Added structured settings `#69
  <https://github.com/argaen/issues/#69>`_ [Manuel Miranda]
- Enhancement #45/add sense to cache instantiation `#68
  <https://github.com/argaen/issues/#68>`_ [Manuel Miranda]

  Both serializers and policies are passed to cached instantiated

  Also, Policy doesn't depend on the client anymore on instantation time. The methods have the dependency instead (it is injected when the cache is calling them)
- Update flake8 to 3.2.0 `#67 <https://github.com/argaen/issues/#67>`_
  [pyup.io bot]

  * Update flake8 from 3.1.0 to 3.2.0

  * Fixed syntax errors
- Fixed examples. [argaen]
- Updated docs to add clear. [argaen]
- Added db and password redis options. [argaen]

  Closes #62
- Added clear cmd `#64 <https://github.com/argaen/issues/#64>`_ [Manuel
  Miranda]
- Fixed issue with redis key builder. [argaen]
- Created new settings module. [argaen]

  Closes #58
- Optional namespace in commands. [argaen]

  Closes #56
- Set_defaults only works with strings now. [argaen]
- Fix documentation. [argaen]
- 0.1.13 version bump. [argaen]
- Added timeout option for the cache instances. [argaen]

  Now any command with the cache can raise an asyncio.Timeout if it lasts
  more than the specified timeout.

  Closes #55
- Catch all exceptions in decorators. [argaen]

  Now only cache operations are covered by try/catch. In case of exception,
  we always call the original function (logging the exception).

  Closes #54
- 0.1.12 version bump. [argaen]
- Enhancement #34/add logs `#53 <https://github.com/argaen/issues/#53>`_
  [Manuel Miranda]

  * Added time in log calls
- Minor style changes. [argaen]
- Decorators call function if backend not running `#52
  <https://github.com/argaen/issues/#52>`_ [Manuel Miranda]

  If a ConnectionRefused is raised from the backend,
  the decorated function is called anyway
- Added logs in cache class `#51
  <https://github.com/argaen/issues/#51>`_ [Manuel Miranda]
- New version to fix pypi broken ones. [argaen]
- Added default cache, set_defaults cache param now is optional.
  [argaen]
- Fixed setup.py. [argaen]
- Fixed default namespace. [argaen]
- Renamed args in decorators. [argaen]

  Closes #48
- Update pytest-mock from 1.3.0 to 1.4.0 `#49
  <https://github.com/argaen/issues/#49>`_ [pyup.io bot]
- 0.1.7 version bump. [argaen]
- Removed pytest.ini for running examples. [argaen]
- Fixed incorrect documentation link. [argaen]
- Improved how default configuration works. [argaen]
- Get_args_dict supports default values now. [argaen]

  Fixes #44
- Added callable to decorators to build key `#46
  <https://github.com/argaen/issues/#46>`_ [Manuel Miranda]

  Also made multi_set to support ttl
- Added functionality to decorators to support both args and kwargs for
  keys. [argaen]
- Cleaned up code. [argaen]
- Removed unused arg. [argaen]
- Added architecture image. [argaen]
- 0.1.4 version bump. [argaen]
- Examples as acceptance tests. [argaen]
- Refactor to split cache and backend logic `#42
  <https://github.com/argaen/issues/#42>`_ [Manuel Miranda]

  Backends now are second level class while the new Cache classes
  are the ones the user interacts with. The api is still similar.
- Update pytest-mock from 1.2 to 1.3.0 `#40
  <https://github.com/argaen/issues/#40>`_ [pyup.io bot]
- Fixed multi_cached behavior. `#38
  <https://github.com/argaen/issues/#38>`_ [Manuel Miranda]

  Now it always requires the positional argument to specify which keys_attribute has to be used
  (no implicit behavior allowed).
- Updated exmples and docs. [argaen]
- Updated docs. [argaen]
- Added key attribute for cached decorator. [argaen]
- Changed dq to deque. [argaen]
- Initial Update `#30 <https://github.com/argaen/issues/#30>`_ [pyup.io
  bot]

  * Update sphinx from 1.4.6 to 1.4.8

  * Update aioredis from 0.2.8 to 0.2.9

  * Update pytest-cov from 2.3.1 to 2.4.0

  * Update marshmallow from 2.10.2 to 2.10.3
- Support breaking change of aioredis with exists. [argaen]
- Added missing references to raw. [argaen]
- 0.1.1 version bump. [argaen]
- Added raw functionality `#28 <https://github.com/argaen/issues/#28>`_
  [Manuel Miranda]

  * Added Memcached backend to unit tests battery

  * Added raw functionality

  This allows to proxy commands not support by the default
  interface to the underlying client used by each backend. Developer
  is on his free will there and is responsible to send the needed
  data
- Added step to build examples. [argaen]
- Added simple testing example. [argaen]


0.1.0 (2016-10-24)
------------------
- 0.1.0 version bump. [argaen]
- Some code cleanup. [argaen]

  Also modified the logic around encoding a bit.
- Changed the way to deal with default_cache. [argaen]
- Some code cleaning. [argaen]
- Updated README. [argaen]
- Updated documentation. [argaen]
- Fixed RTD environment. [argaen]
- Added key_attribute for decorators. [argaen]
- Working MemcachedCache implementation `#20
  <https://github.com/argaen/issues/#20>`_ [Manuel Miranda]
- Working version of multi_cached decorator `#19
  <https://github.com/argaen/issues/#19>`_ [Manuel Miranda]

  multi_cached decorator allows to decorate functions that return dict-like objects in order to cache those key/values easily.

  If the decorated function doesn't receive a `keys` argument, all values will be queried to the original source (meaning that the cache won't be used). If the `keys` argument is received, only the non existing keys from the cache will be queried while the existing ones will be retrieved from the cache.
- Integration tests run with docker now. [argaen]
- Added docs on how to contribute. [argaen]
- Version 0.0.3 bump. [argaen]
- Feature/add strategies `#17 <https://github.com/argaen/issues/#17>`_
  [Manuel Miranda]

  * First approach on how to implement cache strategies

  * Added unit tests for checking calls

  * Integrated with default policy for POC

  * POC demonstrating LRUCache plus tests

  * Added policy support in mget and mset
- Moved test files to integration folder. [argaen]
- Moved common backend __ini__ logic to BaseCache. [argaen]
- Added testing for cached decorator and fixed bug. [argaen]
- Added add for all backends. [argaen]
- Unified tests for different backends to ensure minimum interface.
  [argaen]
- Updated README. [argaen]
- Fixed examples. [argaen]
- Changed serializer functions. [argaen]
- Changed LICENSE. [argaen]
- Version 0.0.2 bump. [argaen]
- Fixed autodocs. [argaen]
- Added docs. [argaen]
- Merge branch 'master' of github.com:argaen/aiocache. [argaen]
- RedisCache backend now is correctly closed in tests fixture.
  [manuelmiranda]
- Fixed multi_set tests. [argaen]
- Fixed memory_cache fixture. [argaen]
- Added license file. [argaen]
- Added multi_set and multi_get implementations. [argaen]
- Added fallbacks logic for get_default_cache. [argaen]
- Removed incr from interface. [argaen]
- Added first version of async decorator. [argaen]
- Using loop for RedisService. [argaen]
- Minor modifications. [argaen]
- Added SimpleCacheMemory implementation. [argaen]
- Added examples folder. [argaen]
- Added badges and some more info. [argaen]
- RedisBackend implementation with couple of serializers. [argaen]
- Added first specification for BaseCache. [manuelmiranda]


