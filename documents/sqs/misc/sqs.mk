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
	export AWS_PROFILE=${AWS_PROFILE}; python3 publisher/publish_documents.py --region ${AWS_REGION} \
		--file-name documents/sqs/misc/sqs-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: publish_ssm_docs
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --html=documents/sqs/misc/sqs-cucumber-tests-results.html --self-contained-html \
		--keep_test_resources --run_integration_tests -m sqs --aws_profile ${AWS_PROFILE} && \
	deactivate

# Execute only one specified Cucumber test
test_one: test_linter publish_ssm_docs
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests \
		documents/sqs/sop/purge-queue/2021-03-11/Tests/step_defs/test_purge_queue.py -m sqs  --aws_profile ${AWS_PROFILE} && \
	deactivate