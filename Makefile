SHELL := /bin/bash
include private.env
export $(shell sed 's/=.*//' private.env)


clean:
	rm -rf venv

venv: clean
	python3 -m virtualenv venv

pip_install:
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate

publish_lambda_ssm_docs:
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 publisher/publish_documents.py --region ${AWS_REGION} --file-name manifests/lambda-manifest --log-level INFO && \
	deactivate

test_lambda:
	source venv/bin/activate && \
	export AWS_PROFILE=${AWS_PROFILE}; python3 -m pytest  --html=./test-results/lambda-cucumber-tests-results.html --self-contained-html --keep_test_resources --run_integration_tests -m lambda --aws_profile ut && \
	deactivate