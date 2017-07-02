dockerup:
	docker-compose -f docker-compose.yml up -d

dockerdown:
	docker-compose -f docker-compose.yml stop

syntax:
	flake8

pylint:
	pylint --disable=C0111 aiocache

types:
	mypy aiocache --disallow-untyped-defs

ut:
	pytest --cov-report term-missing --cov=aiocache -sv tests/ut

_acceptance:
	pytest -sv tests/acceptance

acceptance: dockerup _acceptance dockerdown

doc:
	make -C docs/ html

_functional:
	bash examples/run_all.sh

functional: dockerup _functional dockerdown

_performance:
	pytest -sv tests/performance

performance: dockerup _performance dockerdown

test: syntax ut dockerup _acceptance _functional _performance dockerdown

_release:
	scripts/make_release

release: test _release

changelog:
	gitchangelog
