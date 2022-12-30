cov-report = true


lint:
	flake8 tests/ aiocache/

install-dev:
	pip install -e .[redis,memcached,msgpack,dev]

pylint:
	pylint --disable=C0111 aiocache

unit:
	coverage run -m pytest tests/ut
	@if [ $(cov-report) = true ]; then\
    coverage combine;\
    coverage report;\
	fi

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
