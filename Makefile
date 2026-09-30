PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: test coverage postgres-test run check

test:
	pytest -v

coverage:
	pytest --cov=app --cov-report=term-missing

postgres-test:
	pytest -m postgres -v

run:
	$(PYTHON) run.py

check:
	$(PYTHON) -m compileall app tests
