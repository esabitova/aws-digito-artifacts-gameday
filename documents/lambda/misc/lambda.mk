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
	export AWS_PROFILE=${AWS_PROFILE}; python3 publisher/publish_documents.py --region ${AWS_REGION} \
		--file-name documents/lambda/misc/lambda-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: publish_ssm_docs
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --html=documents/lambda/misc/lambda-cucumber-tests-results.html --self-contained-html \
		--keep_test_resources --run_integration_tests -m lambda --aws_profile ${AWS_PROFILE} && \
	deactivate

# Execute only one specified Cucumber test
test_one: publish_ssm_docs
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests \
		documents/lambda/test/change_memory_size/2020-10-26/tests/step_defs/test_change_memory_size.py -m lambda  --aws_profile ${AWS_PROFILE} && \
	deactivate
