from setuptools import setup, find_packages

setup(
    name="aiocache",
    version="0.2.2",
    author="Manuel Miranda",
    url="https://github.com/argaen/aiocache",
    author_email="manu.mirandad@gmail.com",
    description="Asynchronous redis cache",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
    ],
    packages=find_packages(),
    install_requires=[
        'aioredis',
        'aiomcache'
    ]
)
