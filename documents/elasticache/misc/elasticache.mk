# The Makefile to execute commands by convenient way

SHELL := /bin/bash

# Include the file with private configuration properties to avoid collisions between teammates. See private.env.sample and exec-vars.env.sample as the examples
include ../../../private.env
export $(shell sed 's/=.*//' ../../../private.env)
include exec-vars.env
export $(shell sed 's/=.*//' exec-vars.env)

include ../../../common.mk

# Upload local SSM Documents to AWS SSM Documents service by specifying them in the manifest file
publish_ssm_docs:
	# Move to parent working directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; export PYTHONPATH=`pwd`; python3 publisher/src/publish_documents.py --region ${AWS_REGION} \
		--file-name documents/${SERVICE}/misc/${SERVICE}-manifest --log-level INFO && \
	deactivate

# Execute Cucumber test(-s)
test: test_linter
	# Move to parent working directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest --count=${TEST_COUNT} --workers ${TEST_WORKERS} --pool_size ${TEST_POOL_SIZE} \
		${TEST_TARGETS} --keep_test_resources --tb=long -rfEs --release_failed_resources --run_integration_tests -m ${SERVICE} --aws_profile ${AWS_PROFILE} && \
	deactivate


service_unit_test:
	cd ../../../ && \
	source venv/bin/activate && \
	python3 -m pytest -m unit_test documents/util/scripts/test/test_${SERVICE}_util.py && \
	deactivate
