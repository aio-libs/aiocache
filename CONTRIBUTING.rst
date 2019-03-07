Contributing
============

#. Clone the repository with ``git clone git@github.com:argaen/aiocache.git``
#. Install dependencies with ``make install-dev``
#. Make a change (means writing code, tests without reducing coverage and docs)
#. Ensure syntax is correct with ``make lint``. If there are errors, you can format the code with ``make format``
#. Ensure all tests pass with ``make test``. For fast iterations, use ``make unit`` which will build just the unit tests. You will need docker and docker-compose to be able to pass acceptance and functional tests.
#. Ensure documentation is OK with ``sphinx-autobuild docs/ docs/_build/html/``
#. Make the PR in Github (you must have a fork of your own)
