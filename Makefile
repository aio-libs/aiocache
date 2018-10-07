cov-report = true


lint:
	pipenv run flake8
	pipenv run black -l 100 --check tests/ aiocache/

format:
	pipenv run black -l 100 tests/ aiocache/

install-dev:
	pipenv install --skip-lock -d

pylint:
	pipenv run pylint --disable=C0111 aiocache

unit:
	pipenv run coverage run -m pytest tests/ut
	@if [ $(cov-report) = true ]; then\
    pipenv run coverage combine;\
    pipenv run coverage report;\
	fi

acceptance:
	pipenv run pytest -sv tests/acceptance

doc:
	pipenv run make -C docs/ html

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
