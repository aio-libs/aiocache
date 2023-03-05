import re
from pathlib import Path

from setuptools import setup

p = Path(__file__).with_name("aiocache") / "__init__.py"
try:
    version = re.findall(r"^__version__ = \"([^']+)\"\r?$", p.read_text(), re.M)[0]
except IndexError:
    raise RuntimeError("Unable to determine version.")

readme = Path(__file__).with_name("README.rst").read_text()


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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: AsyncIO",
    ],
    packages=("aiocache",),
    install_requires=None,
    extras_require={
        "redis": ["redis>=4.2.0"],
        "memcached": ["aiomcache>=0.5.2"],
        "msgpack": ["msgpack>=0.5.5"],
    },
    include_package_data=True,
)
