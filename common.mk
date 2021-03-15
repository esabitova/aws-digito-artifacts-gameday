SHELL := /bin/bash
CWD:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))


clean:
	rm -rf venv

venv: clean
	python3 -m virtualenv venv

pip_install:
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate

# Execute linter to test code style
test_linter:
# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m flake8 && \
	deactivate


# Execute unit tests
unit_test:
	# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test && \
	deactivate

# Wrapper rule to execute unit tests and linter together easily in the nested Makefiles
linter_and_unit_test: test_linter unit_test