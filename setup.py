import re
import os

from setuptools import setup, find_packages
from distutils.util import strtobool

with open(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'aiocache/_version.py')) as fp:
    try:
        version = re.findall(
            r"^__version__ = '([^']+)'\r?$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


aioredis = "aioredis==0.3.1"
aiomcache = "aiomcache==0.5.2"

install_requires = set((aioredis, aiomcache))

setup_kwargs = {
    'name': "aiocache",
    'version': version,
    'author': "Manuel Miranda",
    'url': "https://github.com/argaen/aiocache",
    'author_email': "manu.mirandad@gmail.com",
    'description': "multi backend asyncio cache",
    'classifiers': [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Framework :: AsyncIO",
    ],
    'packages': find_packages(),
}


if not strtobool(os.environ.get("AIOCACHE_REDIS", "yes")):
    print("Installing without aioredis")
    install_requires.remove(aioredis)

if not strtobool(os.environ.get("AIOCACHE_MEMCACHED", "yes")):
    print("Installing without aiomcache")
    install_requires.remove(aiomcache)


setup_kwargs['install_requires'] = install_requires
setup(**setup_kwargs)
