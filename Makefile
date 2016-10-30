syntax:
	flake8

pylint:
	pylint --disable=C0111 aiocache

ut:
	pytest -sv tests/ut

integration:
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests/integration
	docker-compose -f docker-compose.yml stop

test:
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests
	pytest -sv examples
	docker-compose -f docker-compose.yml stop

cov:
	docker-compose -f docker-compose.yml up -d
	pytest --cov-report term-missing --cov=aiocache -sv tests
	docker-compose -f docker-compose.yml stop

doc:
	make -C docs/ html

example:
	docker-compose -f docker-compose.yml up -d
	bash examples/run_all.sh
	docker-compose -f docker-compose.yml stop
