cov-report = true


lint:
	flake8

install-dev:
	pipenv install --dev

pylint:
	pylint --disable=C0111 aiocache

unit:
	pipenv run coverage run -m pytest tests/ut
	@if [ $(cov-report) = true ]; then\
    coverage combine;\
    coverage report;\
	fi

acceptance:
	pipenv run pytest -sv tests/acceptance

doc:
	make -C docs/ html

functional:
	pipenv run bash examples/run_all.sh

performance:
	pipenv run pytest -sv tests/performance

test: lint unit acceptance functional

_release:
	scripts/make_release

release: test _release

changelog:
	gitchangelog
