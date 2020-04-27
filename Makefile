.DEFAULT_GOAL := all
isort = isort -rc async_redis tests
black = black -S -l 120 --target-version py37 async_redis tests

.PHONY: install
install:
	pip install -U pip setuptools
	pip install -r requirements.txt
	SKIP_CYTHON=1 pip install -e .

.PHONY: generate-stubs
generate-stubs:
	./tools/generate_stubs.py

.PHONY: compile-trace
compile-trace:
	python setup.py build_ext --force --inplace --define CYTHON_TRACE

.PHONY: compile
compile:
	python setup.py build_ext --inplace

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
all: generate-stubs lint mypy testcov

.PHONY: benchmark
benchmark:
	python benchmarks/run.py

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
	rm -rf build
	rm -rf dist
	rm -f async_redis/*.c async_redis/*.so
	rm -f .coverage
	rm -f .coverage.*
	python setup.py clean
