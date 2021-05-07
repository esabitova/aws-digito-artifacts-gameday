import unittest
import pytest
import json
import io
import resource_manager.src.util.lambda_utils as lambda_utils
import resource_manager.src.util.boto3_client_factory as client_factory
from resource_manager.src.util.enums.lambda_invocation_type import LambdaInvocationType
from unittest.mock import MagicMock
from botocore.response import StreamingBody
from documents.util.scripts.test.test_lambda_util import LAMBDA_ARN, LAMBDA_NAME, LAMBDA_VERSION


def mock_get_function(status_code, memory=0):
    return {
        'ResponseMetadata': {
            'HTTPStatusCode': status_code
        },
        'Configuration': {
            'FunctionArn': LAMBDA_ARN,
            'FunctionName': LAMBDA_NAME,
            'MemorySize': memory
        }
    }


def mock_function_invoke(status_code, payload):
    return {
        'ResponseMetadata': {
            'HTTPStatusCode': status_code
        },
        'Payload': payload
    }


@pytest.mark.unit_test
class TestLambdaUtil(unittest.TestCase):
    def setUp(self):
        self.session_mock = MagicMock()

        self.mock_lambda = MagicMock()
        self.client_side_effect_map = {
            'lambda': self.mock_lambda
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_get_memory_size(self):
        memory_size = 100
        self.mock_lambda.get_function.return_value = mock_get_function(200, memory_size)
        response = lambda_utils.get_memory_size(LAMBDA_ARN, self.session_mock)
        self.mock_lambda.get_function.assert_called_once_with(FunctionName=LAMBDA_ARN)
        self.assertEqual(memory_size, response)

    def test_get_memory_size_exception(self):
        memory_size = 100
        self.mock_lambda.get_function.return_value = mock_get_function(404, memory_size)
        self.assertRaises(Exception, lambda_utils.get_memory_size, LAMBDA_ARN, self.session_mock)
        self.mock_lambda.get_function.assert_called_once_with(FunctionName=LAMBDA_ARN)

    def test_trigger_lambda(self):
        body_encoded = json.dumps({}).encode()
        response_payload = StreamingBody(
            io.BytesIO(body_encoded),
            len(body_encoded)
        )
        self.mock_lambda.invoke.return_value = mock_function_invoke(200, response_payload)
        invocation_type = LambdaInvocationType.Event
        request_payload = '{}'
        response = lambda_utils.trigger_lambda(LAMBDA_ARN, request_payload, invocation_type, self.session_mock)
        self.mock_lambda.invoke.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            InvocationType=invocation_type.name,
            Payload=bytes(request_payload, 'utf-8')
        )
        self.assertEqual(request_payload.encode(), response)

    def test_trigger_lambda_exception(self):
        self.mock_lambda.invoke.return_value = mock_function_invoke(404, {})
        invocation_type = LambdaInvocationType.Event
        request_payload = '{}'
        self.assertRaises(ValueError, lambda_utils.trigger_lambda, LAMBDA_ARN, request_payload, invocation_type,
                          self.session_mock)
        self.mock_lambda.invoke.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            InvocationType=invocation_type.name,
            Payload=bytes(request_payload, 'utf-8')
        )

    def test_get_function_concurrency(self):
        concurrent_executions = 10
        self.mock_lambda.get_function_concurrency.return_value = {'ReservedConcurrentExecutions': concurrent_executions}
        response = lambda_utils.get_function_concurrency(LAMBDA_ARN, self.session_mock)
        self.assertEqual(concurrent_executions, response)
        self.mock_lambda.get_function_concurrency.assert_called_once_with(
            FunctionName=LAMBDA_ARN
        )

    def test_delete_function_concurrency(self):
        lambda_utils.delete_function_concurrency(LAMBDA_ARN, self.session_mock)
        self.mock_lambda.delete_function_concurrency.assert_called_once_with(FunctionName=LAMBDA_ARN)

    def test_get_function_provisioned_concurrency(self):
        provisioned_concurrency = 50
        self.mock_lambda.get_provisioned_concurrency_config.return_value = {
            'AllocatedProvisionedConcurrentExecutions': provisioned_concurrency
        }
        response = lambda_utils.get_function_provisioned_concurrency(LAMBDA_ARN, LAMBDA_VERSION, self.session_mock)
        self.assertEqual(provisioned_concurrency, response)
        self.mock_lambda.get_provisioned_concurrency_config.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            Qualifier=LAMBDA_VERSION
        )

    def test_delete_function_provisioned_concurrency_config(self):
        lambda_utils.delete_function_provisioned_concurrency_config(LAMBDA_ARN, LAMBDA_VERSION, self.session_mock)
        self.mock_lambda.delete_provisioned_concurrency_config.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            Qualifier=LAMBDA_VERSION
        )

    def test_get_lambda_state(self):
        state = 'Active'
        self.mock_lambda.get_function.return_value = {'Configuration': {'State': state}}
        response = lambda_utils.get_lambda_state(LAMBDA_ARN, self.session_mock)
        self.mock_lambda.get_function.assert_called_once_with(
            FunctionName=LAMBDA_ARN
        )
        self.assertEqual(response, state)

    def test_create_alias(self):
        alias_name = 'alias_name'
        lambda_version = '1'
        lambda_utils.create_alias(LAMBDA_ARN, alias_name, lambda_version, self.session_mock)
        self.mock_lambda.create_alias.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            Name=alias_name,
            FunctionVersion=lambda_version
        )

    def test_delete_alias(self):
        alias_name = 'alias_name'
        lambda_utils.delete_alias(LAMBDA_ARN, alias_name, self.session_mock)
        self.mock_lambda.delete_alias.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            Name=alias_name
        )
