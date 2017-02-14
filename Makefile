syntax:
	flake8

pylint:
	pylint --disable=C0111 aiocache

ut:
	pytest -sv tests/ut

acceptance:
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests/acceptance
	docker-compose -f docker-compose.yml stop

test: syntax
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests/ut
	pytest -sv tests/acceptance
	bash examples/run_all.sh
	docker-compose -f docker-compose.yml stop

cov:
	docker-compose -f docker-compose.yml up -d
	pytest --cov-report term-missing --cov=aiocache -sv tests/ut
	docker-compose -f docker-compose.yml stop

doc:
	make -C docs/ html

functional:
	docker-compose -f docker-compose.yml up -d
	bash examples/run_all.sh
	docker-compose -f docker-compose.yml stop
