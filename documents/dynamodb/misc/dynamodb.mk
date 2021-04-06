# The Makefile to execute commands by convenient way

SHELL := /bin/bash

# Include the file with private configuration properties to avoid collisions between teammates. See private.env.sample as the example
include ../../../private.env
export $(shell sed 's/=.*//' ../../../private.env)

include ../../../common.mk

# Upload local SSM Documents to AWS SSM Documents service by specifying them in the manifest file
publish_ssm_docs:
	# Move to parent working directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; export PYTHONPATH=`pwd`; python3 publisher/src/publish_documents.py --region ${AWS_REGION} \
		--file-name documents/dynamodb/misc/dynamodb-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: linter_and_unit_test
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest --keep_test_resources --run_integration_tests -m dynamodb --aws_profile ${AWS_PROFILE} && \
	deactivate

# Execute only one specified Cucumber test
test_one: test_linter
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests \
		documents/dynamodb/sop/update_provisioned_capacity/2020-04-01/Tests/step_defs/test_update_provisioned_capacity.py -m dynamodb  --aws_profile ${AWS_PROFILE} && \
	deactivate

service_unit_test:
	cd ../../../ && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test documents/util/scripts/test/test_dynamodb_util.py && \
	deactivate