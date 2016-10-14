from setuptools import setup

install_requires = []
tests_require = install_requires + ['pytest']

setup(
    name="aiocache",
    version="0.0.5",
    author="Manuel Miranda",
    url="https://github.com/argaen/aiocache",
    author_email="manu.mirandad@gmail.com",
    description="Asynchronous redis cache",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.5",
    ],
    packages=['aiocache'],
    install_requires=install_requires,
    setup_requires=['pytest-runner'],
    tests_require=tests_require,
)
