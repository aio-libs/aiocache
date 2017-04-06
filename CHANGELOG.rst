Changelog
=========


Unreleased
----------
- Added CHANGELOG and release process. [argaen]
- Improvement in getting attrs with fallbacks. [argaen]
- Added pool_min_size pool_max_size to redisbackend `#167
  <https://github.com/argaen/issues/#167>`_ [Manuel Miranda]
- Timeout per function. Propagate it correctly with defaults. `#166
  <https://github.com/argaen/issues/#166>`_ [Manuel Miranda]
- Added disclaimer regarding the defaults module. [argaen]
- Fixed framework examples. [argaen]
- Removed async-timeout as a dependency. [argaen]
- Added noself arg to cached decorator `#137
  <https://github.com/argaen/issues/#137>`_ [Manuel Miranda]
- Cache instance in decorators is built in every call `#135
  <https://github.com/argaen/issues/#135>`_ [Manuel Miranda]
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
- Fixed asynctest issues for timeout tests `#109
  <https://github.com/argaen/issues/#109>`_ [Manuel Miranda]
- Created new API class `#108 <https://github.com/argaen/issues/#108>`_
  [Manuel Miranda]
- Enhancement #94/increase unit test coverage `#106
  <https://github.com/argaen/issues/#106>`_ [Manuel Miranda]
- Fix test failing randomly. [argaen]
- Enhancement #94/increase unit test coverage `#102
  <https://github.com/argaen/issues/#102>`_ [Manuel Miranda]
- Enhancement #94/increase unit test coverage `#101
  <https://github.com/argaen/issues/#101>`_ [Manuel Miranda]
- Set multicached keys only when non existing `#98
  <https://github.com/argaen/issues/#98>`_ [Manuel Miranda]
- Added expire command `#97 <https://github.com/argaen/issues/#97>`_
  [Manuel Miranda]
- All backend kwargs pull default attributes. [argaen]
- Removed integrtion from coverage. [argaen]
- Ttl tasks are cancelled for memory backend if key is deleted `#92
  <https://github.com/argaen/issues/#92>`_ [Manuel Miranda]
- Merge branch 'master' of https://github.com/argaen/aiocache. [argaen]
- Ignore caching if AIOCACHE_DISABLED is set to 1 `#90
  <https://github.com/argaen/issues/#90>`_ [Manuel Miranda]
- Merge branch 'master' of github.com:argaen/aiocache. [argaen]
- Added some docs to plugins. [argaen]


0.2.0 (2016-12-14)
------------------
- Added python version badge. [argaen]
- LRU plugin example. [Manuel Miranda]
- Feature #57/policy to generic hooks `#83
  <https://github.com/argaen/issues/#83>`_ [Manuel Miranda]
- Added new test. [argaen]
- Reuse redis pools `#77 <https://github.com/argaen/issues/#77>`_
  [Manuel Miranda]
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
- Update flake8 to 3.2.0 `#67 <https://github.com/argaen/issues/#67>`_
  [pyup.io bot]
- Fixed examples. [argaen]
- Updated docs to add clear. [argaen]
- Added db and password redis options. [argaen]
- Added clear cmd `#64 <https://github.com/argaen/issues/#64>`_ [Manuel
  Miranda]
- Fixed issue with redis key builder. [argaen]
- Created new settings module. [argaen]
- Optional namespace in commands. [argaen]
- Set_defaults only works with strings now. [argaen]
- Fix documentation. [argaen]
- Added timeout option for the cache instances. [argaen]
- Catch all exceptions in decorators. [argaen]
- Enhancement #34/add logs `#53 <https://github.com/argaen/issues/#53>`_
  [Manuel Miranda]
- Minor style changes. [argaen]
- Decorators call function if backend not running `#52
  <https://github.com/argaen/issues/#52>`_ [Manuel Miranda]
- Added logs in cache class `#51
  <https://github.com/argaen/issues/#51>`_ [Manuel Miranda]
- New version to fix pypi broken ones. [argaen]
- Added default cache, set_defaults cache param now is optional.
  [argaen]
- Fixed setup.py. [argaen]
- Fixed default namespace. [argaen]
- Renamed args in decorators. [argaen]
- Removed pytest.ini for running examples. [argaen]
- Fixed incorrect documentation link. [argaen]
- Improved how default configuration works. [argaen]
- Get_args_dict supports default values now. [argaen]
- Added callable to decorators to build key `#46
  <https://github.com/argaen/issues/#46>`_ [Manuel Miranda]
- Added functionality to decorators to support both args and kwargs for
  keys. [argaen]
- Cleaned up code. [argaen]
- Removed unused arg. [argaen]
- Added architecture image. [argaen]
- Examples as acceptance tests. [argaen]
- Refactor to split cache and backend logic `#42
  <https://github.com/argaen/issues/#42>`_ [Manuel Miranda]
- Fixed multi_cached behavior. `#38
  <https://github.com/argaen/issues/#38>`_ [Manuel Miranda]
- Updated exmples and docs. [argaen]
- Updated docs. [argaen]
- Added key attribute for cached decorator. [argaen]
- Changed dq to deque. [argaen]
- Initial Update `#30 <https://github.com/argaen/issues/#30>`_ [pyup.io
  bot]
- Support breaking change of aioredis with exists. [argaen]
- Added missing references to raw. [argaen]
- Added raw functionality `#28 <https://github.com/argaen/issues/#28>`_
  [Manuel Miranda]
- Added step to build examples. [argaen]
- Added simple testing example. [argaen]


0.1.0 (2016-10-24)
------------------
- Some code cleanup. [argaen]
- Changed the way to deal with default_cache. [argaen]
- Some code cleaning. [argaen]
- Updated documentation. [argaen]
- Fixed RTD environment. [argaen]
- Added key_attribute for decorators. [argaen]
- Working MemcachedCache implementation `#20
  <https://github.com/argaen/issues/#20>`_ [Manuel Miranda]
- Working version of multi_cached decorator `#19
  <https://github.com/argaen/issues/#19>`_ [Manuel Miranda]
- Integration tests run with docker now. [argaen]
- Added docs on how to contribute. [argaen]
- Version 0.0.3 bump. [argaen]
- Feature/add strategies `#17 <https://github.com/argaen/issues/#17>`_
  [Manuel Miranda]
- Moved test files to integration folder. [argaen]
- Moved common backend __ini__ logic to BaseCache. [argaen]
- Added testing for cached decorator and fixed bug. [argaen]
- Added add for all backends. [argaen]
- Unified tests for different backends to ensure minimum interface.
  [argaen]
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


