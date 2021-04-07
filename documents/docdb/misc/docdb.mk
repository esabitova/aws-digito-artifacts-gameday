# The Makefile to execute commands by convenient way

SHELL := /bin/bash

# Include the file with private configuration properties to avoid collisions between teammates. See private.env.sample as the example
include ../../../private.env
export $(shell sed 's/=.*//' ../../../private.env)

# Upload local SSM Documents to AWS SSM Documents service by specifying them in the manifest file
publish_ssm_docs:
    # Move to parent working directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; export PYTHONPATH=`pwd`; python3 publisher/src/publish_documents.py --region ${AWS_REGION} \
        --file-name documents/docdb/misc/docdb-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: linter_and_unit_test
    # Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest --keep_test_resources --run_integration_tests -m docdb --aws_profile ut && \
	deactivate

test_one: test_linter
    # Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests \
        documents/docdb/sop/create_new_instance/2020-09-21/Tests/step_defs/test_create_new_instance.py -m docdb --aws_profile ${AWS_PROFILE} && \
	deactivate

test_linter:
	cd ../../../ && \
	source venv/bin/activate && \
	python3 -m flake8 --show-source --config=setup.cfg --count && \
	echo "↑ the number of found errors" && \
	deactivate

unit_test:
	cd ../../../ && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test documents/util/scripts/test/test_docdb_util.py && \
	deactivate

linter_and_unit_test: test_linter unit_test