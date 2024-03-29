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

clean_canary_artifacts:
	rm -rf documents/docdb/test/database_inaccessible_alarm/2020-09-21/Test/canary/package  && \
	rm -f documents/docdb/test/database_inaccessible_alarm/2020-09-21/Test/canary/*.zip

clean_all: clean clean_test_artifacts clean_canary_artifacts

enable_git_hooks:
	cp -R ./.githooks/* ./.git/hooks/ && \
	chmod +x ./.git/hooks/* && \
	echo "Git hooks were updated from ./.githooks/ into ./.git/hooks/"

install_virtualenv:
	python3.7 -m pip install virtualenv

venv: clean clean_test_artifacts enable_git_hooks install_virtualenv
	python3.7 -m virtualenv venv

pip_install: venv
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate

pip_install_only:
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate

# Check versions updates of requirements
check_pip_updates:
	source venv/bin/activate && \
    pip-check --local --ascii --hide-unchanged --not-required && \
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
unit_test: clean_test_artifacts
	# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test --reruns 5 --timeout=50 --disable-socket && \
	deactivate

# Execute unit tests multiple times randomly which increases the chance to find the error when test cases have dependencies between each other
unit_test_multiple_times: clean_test_artifacts
	# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test --reruns 5 --count=100 -x --timeout=50 --disable-socket && \
	deactivate

# Find lines which are not in master branch and not covered by unit tests. Firstly, coverage tests need to be executed
find_uncovered_new_lines: unit_test
	# If it was executed from the nested Makefiles when workdir was not changed after moving to the parent Makefile
	cd "$(CWD)/" && \
	source venv/bin/activate && \
	python3 -m diff_cover.diff_cover_tool documentation/coverage/coverage.xml --compare-branch=origin/master --fail-under=100 && \
	deactivate

find_unused_fixtures:
	source venv/bin/activate && \
	python3 -m pytest --dead-fixtures&& \
	deactivate

# Execute unit tests only for changed files usually as part of the pre-push git hook. It is useful to save time
unit_test_incrementally:
	source venv/bin/activate && \
	python3 -m pytest -m unit_test --inc --cov-append --suppress-no-test-exit-code --workers auto && \
	deactivate

destroy_all_cfn_resources:
	source venv/bin/activate && \
	PYTHONPATH=. python resource_manager/src/tools/resource_tool.py -c DESTROY_ALL	 && \
	deactivate

list_all_cfn_resources:
	source venv/bin/activate && \
	PYTHONPATH=. python resource_manager/src/tools/resource_tool.py -c LIST && \
	deactivate

generate_artifact_sop:
	source venv/bin/activate && \
	PYTHONPATH=. python artifact_generator/src/generate_artifacts.py -i artifact_generator/input/input-overrides-sop.json && \
	deactivate

generate_artifact_test:
	source venv/bin/activate && \
	PYTHONPATH=. python artifact_generator/src/generate_artifacts.py -i artifact_generator/input/input-overrides-test.json && \
	deactivate

# Find validation errors in SSM Documents
style_validator:
	source venv/bin/activate && \
    python -m pytest -m style_validator --no-cov && \
    deactivate

# Wrapper rule to execute unit tests and linter together easily in the nested Makefiles
linter_and_unit_test: test_linter unit_test

#todo DIG-977 create CW Canary distribution package in database_inaccessible_alarm.feature
build_canary_artifacts: clean_canary_artifacts test_linter
	source venv/bin/activate && \
	cd documents/docdb/canary/database-connection-canary && \
	pip install --target ./package/python -r requirements.txt && \
	cd package && \
	zip -r ../database-connection-canary.zip . && \
	cd  .. && \
	zip -g database-connection-canary.zip python/*

cfn_lint: pip_install_only
	source venv/bin/activate && \
	PYTHONPATH=. cfn-lint -a cfn_lint/rules/assume_role_templates -t documents/**/AutomationAssumeRoleTemplate.yml ; \
	PYTHONPATH=. cfn-lint -a cfn_lint/rules/alarm_templates -o cfn_lint/specs/AlarmHasActionSpec.json -i E3006 E1029 E3012 E0000 E1019 -t documents/**/AlarmTemplate.yml ; \
	PYTHONPATH=. cfn-lint -a cfn_lint/rules/resource_manager_templates -i W1020 -t resource_manager/cloud_formation_templates/*.yml resource_manager/cloud_formation_templates/**/*.yml && \
	deactivate
