.DEFAULT_GOAL := all
isort = isort -rc async_redis tests
black = black -S -l 120 --target-version py37 async_redis tests

.PHONY: install
install:
	pip install -U pip setuptools
	pip install -r requirements.txt
	#pip install -e .

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: lint
lint:
	flake8 async_redis tests
	$(isort) --check-only -df
	$(black) --check

.PHONY: test
test:
	pytest --cov=async_redis

.PHONY: testcov
testcov: test
	@echo "building coverage html"
	@coverage html

.PHONY: mypy
mypy:
	mypy async_redis

.PHONY: all
all: lint mypy testcov

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	make -C docs clean
	python setup.py clean
