syntax:
	flake8

test:
	pytest -sv tests

cov:
	pytest --cov-report term-missing --cov=aiocache -sv tests
