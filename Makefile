lint:
	flake8

install-dev:
	pip install -e .[dev,redis,memcached]

pylint:
	pylint --disable=C0111 aiocache

unit:
	pytest --cov-report term-missing --cov aiocache -sv tests/ut

acceptance:
	pytest -sv tests/acceptance

doc:
	make -C docs/ html

functional:
	bash examples/run_all.sh

performance:
	pytest -sv tests/performance

test: lint unit acceptance functional

_release:
	scripts/make_release

release: test _release

changelog:
	gitchangelog
