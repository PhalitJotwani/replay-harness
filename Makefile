.PHONY: install lint typecheck test docker-test

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests

typecheck:
	mypy src

test:
	pytest tests/ -v

docker-test:
	docker build -t replay-harness-test . && docker run --rm replay-harness-test
