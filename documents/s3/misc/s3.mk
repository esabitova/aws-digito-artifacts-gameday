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
		--file-name documents/s3/misc/s3-manifest --log-level INFO && \
	deactivate

# Execute Cucumber tests
test: linter_and_unit_test
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests -m s3 --count=2 --aws_profile ${AWS_PROFILE} && \
	deactivate

# Execute only one specified Cucumber test
test_one: linter_and_unit_test
	# Move to parent directory
	cd ../../../ && \
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --keep_test_resources --run_integration_tests \
		documents/s3/sop/restore_from_backup/2020-09-21/Tests/step_defs/test_restore_from_backup.py -m s3 --count=2  --aws_profile ${AWS_PROFILE} && \
	deactivate
