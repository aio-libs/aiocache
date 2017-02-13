from setuptools import setup, find_packages

setup(
    name="aiocache",
    version="0.3.1",
    author="Manuel Miranda",
    url="https://github.com/argaen/aiocache",
    author_email="manu.mirandad@gmail.com",
    description="multi backend asyncio cache",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(),
    install_requires=[
        'aioredis',
        'aiomcache'
    ]
)
