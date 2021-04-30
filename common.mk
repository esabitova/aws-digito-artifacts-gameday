SHELL := /bin/bash
CWD:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

clean:
	rm -rf venv


clean_test_artifacts:
	rm -rf documentation && \
	rm -rf .pytest_cache && \
	rm -rf .coverage* && \
	rm -rf deps.json && \
	rm -rf .pytest-incremental*


enable_git_hooks:
	cp -R ./.githooks/* ./.git/hooks/ && \
	chmod +x ./.git/hooks/*

venv: clean clean_test_artifacts enable_git_hooks
	python3.7 -m virtualenv venv

pip_install: enable_git_hooks
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate

publish_all_ssm_docs:
	# Move to parent working directory
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; export PYTHONPATH=`pwd`; python3 publisher/src/publish_documents.py --region ${AWS_REGION}  --log-level INFO && \
	deactivate

# Execute linter to test code style
test_linter:
# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m flake8 --show-source --config=setup.cfg --count && \
	echo "↑ the number of found errors" && \
	deactivate


# Execute unit tests
unit_test:
	# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test --workers auto && \
	deactivate

# Execute unit tests only for changed files usually as part of the pre-push git hook. It is useful to save time
unit_test_incrementally:
	source venv/bin/activate && \
	python3 -m pytest -m unit_test --inc --cov-append --suppress-no-test-exit-code --workers auto && \
	deactivate

style_validator:
	source venv/bin/activate && \
    python -m pytest -m style_validator --no-cov && \
    deactivate

metadata_validator:
	source venv/bin/activate && \
    python -m pytest -m metadata_validator --no-cov && \
    deactivate

# Wrapper rule to execute unit tests and linter together easily in the nested Makefiles
linter_and_unit_test: test_linter unit_test

