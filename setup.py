import re
import os

from setuptools import setup, find_packages

with open(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'aiocache/_version.py')) as fp:
    try:
        version = re.findall(
            r"^__version__ = '([^']+)'\r?$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


setup(
    name='aiocache',
    version=version,
    author='Manuel Miranda',
    url='https://github.com/argaen/aiocache',
    author_email='manu.mirandad@gmail.com',
    description='multi backend asyncio cache',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: AsyncIO',
    ],
    packages=find_packages(),
    install_requires=None,
    extras_require={
        'redis': ['aioredis>=0.3.3,<1'],
        'memcached': ['aiomcache>=0.5.2'],
        'dev': [
            'flake8',
            'pytest',
            'pytest-asyncio',
            'pytest-cov',
            'pytest-mock',
            'codecov',
            'marshmallow',
            'mypy',
            'asynctest==0',
            'ujson',    # this is a bug, need to fix

            'sphinx',
            'sphinx-autobuild',
            'sphinx-rtd-theme',
            'gitchangelog',
            'pystache',
        ]
    },
    dependency_links=[
        'git+https://github.com/MartiusWeb/asynctest.git@async_magic#egg=asynctest-0'
    ]
)
