Contributing
============

Workflow is the following:

#. Clone the repository
#. Install dependencies with ``pip install -r requirements-ci.txt && pip install -r requirements-dev.txt``
#. Make a change (means writing code, tests and docs)
#. Ensure all tests pass with ``make test``. You will need docker and docker-compose to be able to pass integration tests.
#. Ensure documentation is OK with ``sphinx-autobuild docs/ docs/_build/html/``
#. Make the PR in Github (you must have a fork of your own)
