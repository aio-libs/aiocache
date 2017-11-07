dockerup:
	docker-compose -f docker-compose.yml up -d

dockerdown:
	docker-compose -f docker-compose.yml stop

syntax:
	flake8

install-dev:
	pip install -e .[dev,redis,memcached] --process-dependency-links

pylint:
	pylint --disable=C0111 aiocache

ut:
	pytest --cov-report term-missing --cov aiocache -sv tests/ut

acceptance:
	pytest -sv tests/acceptance

doc:
	make -C docs/ html

functional:
	bash examples/run_all.sh

performance:
	pytest -sv tests/performance

test: syntax ut acceptance functional performance

_release:
	scripts/make_release

release: test _release

changelog:
	gitchangelog
