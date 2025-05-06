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
    license="BSD-3-Clause",
    description="multi backend asyncio cache",
    long_description=readme,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.9",
    packages=("aiocache",),
    install_requires=None,
    extras_require={
        "valkey": ["valkey-glide>=1.3.3"],
        "memcached": ["aiomcache>=0.5.2"],
        "msgpack": ["msgpack>=0.5.5"],
    },
    include_package_data=True,
)
