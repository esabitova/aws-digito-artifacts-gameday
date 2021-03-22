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
	export AWS_PROFILE=${AWS_PROFILE}; python3 publisher/src/publish_documents.py --region ${AWS_REGION} \
		--file-name documents/docdb/misc/docdb-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: publish_ssm_docs
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --html=documents/docdb/misc/docdb-cucumber-tests-results.html --self-contained-html \
		--keep_test_resources --run_integration_tests -m docdb --aws_profile ut && \
	deactivate