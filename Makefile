syntax:
	flake8

ut:
	pytest -sv tests/ut

integration:
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests/integration
	docker-compose -f docker-compose.yml stop

test:
	docker-compose -f docker-compose.yml up -d
	pytest -sv tests
	docker-compose -f docker-compose.yml stop

cov:
	docker-compose -f docker-compose.yml up -d
	pytest --cov-report term-missing --cov=aiocache -sv tests
	docker-compose -f docker-compose.yml stop

doc:
	make -C docs/ html
