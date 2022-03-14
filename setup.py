import re
import os

from setuptools import setup, find_packages

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "aiocache/_version.py")) as fp:
    try:
        version = re.findall(r"^__version__ = \"([^']+)\"\r?$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


with open("README.rst", encoding="utf8") as f:
    readme = f.read()


setup(
    name="aiocache",
    version=version,
    author="Manuel Miranda",
    url="https://github.com/aio-libs/aiocache",
    author_email="manu.mirandad@gmail.com",
    description="multi backend asyncio cache",
    long_description=readme,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: AsyncIO",
    ],
    packages=find_packages(),
    install_requires=None,
    extras_require={
        # todo: adapt code for aioredis 2.0
        'redis:python_version<"3.8"': ["aioredis>=1.0.0,<2.0"],
        'redis:python_version>="3.8"': ["aioredis>=1.3.0,<2.0"],
        "memcached": ["aiomcache>=0.5.2"],
        "msgpack": ["msgpack>=0.5.5"],
    },
    include_package_data=True,
)
