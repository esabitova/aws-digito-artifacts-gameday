import unittest
from unittest.mock import patch, MagicMock, call
import pytest

from documents.util.scripts.src.lambda_util import get_concurrent_execution_quota, check_feasibility, \
    calculate_total_reserved_concurrency, set_reserved_concurrent_executions, backup_reserved_concurrent_executions

CONCURRENT_EXECUTION_QUOTA_CODE = 'L-B99A9384'
LAMBDA_NAME = 'LambdaTemplate-0-LambdaFunction-5UDF2PBK1R'
LAMBDA_ARN = 'arn:aws:lambda:us-east-1:435978235099:function:LambdaTemplate-0-LambdaFunction-5UDF2PBK1R'
LAMBDA_VERSION = 1


def get_concurrent_execution_quota_mock_data(limit):
    return {
        "ServiceCode": "lambda",
        "ServiceName": "AWS Lambda",
        "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-B99A9384",
        "QuotaCode": "L-B99A9384",
        "QuotaName": "Concurrent executions",
        "Value": limit,
        "Unit": "None",
        "Adjustable": True,
        "GlobalQuota": False,
        "UsageMetric": {
            "MetricNamespace": "AWS/Lambda",
            "MetricName": "ConcurrentExecutions",
            "MetricDimensions": {},
            "MetricStatisticRecommendation": "Maximum"
        }
    }


def get_aws_default_service_quota_side_effect(limit):
    return {
        'Quota': get_concurrent_execution_quota_mock_data(limit)
    }


def get_service_quotas_side_effect(limit=None):
    result = {
        "Quotas": [
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-7C0F49F9",
                "QuotaCode": "L-7C0F49F9",
                "QuotaName": "Asynchronous payload",
                "Value": 256,
                "Unit": "Kilobytes",
                "Adjustable": False,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-548AE339",
                "QuotaCode": "L-548AE339",
                "QuotaName": "Burst concurrency",
                "Value": 3000,
                "Unit": "None",
                "Adjustable": False,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-8E39F3F1",
                "QuotaCode": "L-8E39F3F1",
                "QuotaName": "Deployment package size (console editor)",
                "Value": 3,
                "Unit": "Megabytes",
                "Adjustable": False,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-75F48B05",
                "QuotaCode": "L-75F48B05",
                "QuotaName": "Deployment package size (direct upload)",
                "Value": 50,
                "Unit": "Megabytes",
                "Adjustable": False,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-E49FF7B8",
                "QuotaCode": "L-E49FF7B8",
                "QuotaName": "Deployment package size (unzipped)",
                "Value": 250,
                "Unit": "Megabytes",
                "Adjustable": False,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-9FEE3D26",
                "QuotaCode": "L-9FEE3D26",
                "QuotaName": "Elastic network interfaces per VPC",
                "Value": 250,
                "Unit": "None",
                "Adjustable": True,
                "GlobalQuota": False
            },
            {
                "ServiceCode": "lambda",
                "ServiceName": "AWS Lambda",
                "QuotaArn": "arn:aws:servicequotas:us-east-1::lambda/L-6581F036",
                "QuotaCode": "L-6581F036",
                "QuotaName": "Environment variable size",
                "Value": 4,
                "Unit": "Kilobytes",
                "Adjustable": False,
                "GlobalQuota": False
            }
        ]
    }
    # if limit is not None:
    if limit:
        result['Quotas'].append(get_concurrent_execution_quota_mock_data(limit))
    return [result]


def list_functions_paginated_side_effect(number_of_another_functions=0):
    functions = [{
        'FunctionName': LAMBDA_NAME,
        'FunctionArn': LAMBDA_ARN,
    }]
    for i in range(0, number_of_another_functions):
        functions.append({
            'FunctionName': LAMBDA_NAME + str(i),
            'FunctionArn': LAMBDA_ARN + str(i),
        })
    return [{
        'Functions': functions
    }]


def get_function_concurrency_side_effect(concurrency=0):
    return {
        'ReservedConcurrentExecutions': concurrency
    }


def get_paginate_side_effect(function, number_of_functions):
    class PaginateMock(MagicMock):
        def paginate(self, **kwargs):
            return function(number_of_functions)

    return PaginateMock


@pytest.mark.unit_test
class TestLambdaUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_lambda = MagicMock()
        self.mock_service_quotas = MagicMock()

        # self.list_functions_mock = MagicMock()
        side_effect_map = {
            'lambda': self.mock_lambda,
            'service-quotas': self.mock_service_quotas,
            # 'list_functions': self.list_functions_mock
        }
        self.client.side_effect = lambda service_name, config: side_effect_map.get(service_name)
        # self.client.get_paginator.side_effect = lambda action_name: side_effect_map.get(action_name)

    def tearDown(self):
        self.patcher.stop()

    # Test get_concurrent_execution_quota
    def test_get_concurrent_execution_quota_account_limit_5000(self):
        events = {}
        limit = 2000
        self.mock_service_quotas.get_paginator = get_paginate_side_effect(get_service_quotas_side_effect, limit)
        response = get_concurrent_execution_quota(events, None)
        self.assertEqual(response, {'ConcurrentExecutionsQuota': limit})

    def test_get_concurrent_execution_quota_default_service_code(self):
        events = {}
        limit = 1000
        self.mock_service_quotas.list_service_quotas.return_value = get_service_quotas_side_effect()
        self.mock_service_quotas.get_aws_default_service_quota.return_value = \
            get_aws_default_service_quota_side_effect(limit)
        response = get_concurrent_execution_quota(events, None)
        self.assertEqual(response, {'ConcurrentExecutionsQuota': limit})
        self.mock_service_quotas.get_aws_default_service_quota.assert_called_once_with(
            ServiceCode='lambda',
            QuotaCode=CONCURRENT_EXECUTION_QUOTA_CODE
        )

    def test_get_concurrent_execution_quota_exception(self):
        self.mock_service_quotas.get_aws_default_service_quota.return_value = {}
        self.assertRaises(Exception, get_concurrent_execution_quota, {}, None)

    # Test calculate_total_reserved_concurrency
    def test_calculate_total_reserved_concurrency_one_function(self):
        events = {
            'LambdaARN': LAMBDA_ARN
        }
        number_of_functions = 0
        self.mock_lambda.get_paginator = get_paginate_side_effect(
            list_functions_paginated_side_effect,
            number_of_functions
        )
        response = calculate_total_reserved_concurrency(events, None)
        self.assertEqual(response, {'TotalReservedConcurrency': 0})
        self.mock_lambda.get_function_concurrency.assert_not_called()

    def test_calculate_total_reserved_concurrency_two_functions(self):
        events = {
            'LambdaARN': LAMBDA_ARN
        }
        number_of_functions = 1
        self.mock_lambda.get_paginator = get_paginate_side_effect(
            list_functions_paginated_side_effect,
            number_of_functions
        )
        self.mock_lambda.get_function_concurrency.assert_not_called()
        concurrency = 20
        self.mock_lambda.get_function_concurrency.return_value = get_function_concurrency_side_effect(concurrency)
        response = calculate_total_reserved_concurrency(events, None)
        self.mock_lambda.get_function_concurrency.assert_called_once_with(
            FunctionName=LAMBDA_NAME + '0'
        )
        self.assertEqual({'TotalReservedConcurrency': concurrency}, response)

    def test_calculate_total_reserved_concurrency_five_functions(self):
        events = {
            'LambdaARN': LAMBDA_ARN
        }
        number_of_functions = 4
        self.mock_lambda.get_paginator = get_paginate_side_effect(
            list_functions_paginated_side_effect,
            number_of_functions
        )
        self.mock_lambda.get_function_concurrency.assert_not_called()
        concurrency = 100
        self.mock_lambda.get_function_concurrency.return_value = get_function_concurrency_side_effect(concurrency)
        response = calculate_total_reserved_concurrency(events, None)
        calls = [
            call(FunctionName=LAMBDA_NAME + '0'),
            call(FunctionName=LAMBDA_NAME + '1'),
            call(FunctionName=LAMBDA_NAME + '2'),
            call(FunctionName=LAMBDA_NAME + '3')
        ]
        self.mock_lambda.get_function_concurrency.assert_has_calls(calls)
        self.assertEqual({'TotalReservedConcurrency': concurrency * 4}, response)

    def test_calculate_total_reserved_concurrency_exception(self):
        self.mock_lambda.get_paginator.return_value = []
        self.assertRaises(Exception, calculate_total_reserved_concurrency, {}, None)

    # Test check_feasibility
    def test_check_feasibility_value_within_quota(self):
        events = {
            'ConcurrentExecutionsQuota': 1000,
            'TotalReservedConcurrency': 0,
            'NewReservedConcurrentExecutions': 10
        }
        response = check_feasibility(events, None)
        self.assertEqual(response, {
            'CanSetReservedConcurrency': True,
            'MaximumPossibleReservedConcurrency': 890
        })

    def test_check_feasibility_value_outside_quota(self):
        events = {
            'ConcurrentExecutionsQuota': 1000,
            'TotalReservedConcurrency': 900,
            'NewReservedConcurrentExecutions': 10
        }
        self.assertRaises(Exception, check_feasibility, events, None)

    def test_check_feasibility_empty_events(self):
        self.assertRaises(Exception, check_feasibility, {}, None)

    # Test set_reserved_concurrent_executions
    def test_set_reserved_concurrent_executions(self):
        concurrent_executions = 10
        events = {
            'NewReservedConcurrentExecutions': concurrent_executions,
            'LambdaARN': LAMBDA_ARN,
            'MaximumPossibleReservedConcurrency': 510
        }
        response = set_reserved_concurrent_executions(events, None)
        self.mock_lambda.put_function_concurrency.assert_called_once_with(
            FunctionName=LAMBDA_ARN,
            ReservedConcurrentExecutions=concurrent_executions
        )
        self.assertEqual(response, {
            'ReservedConcurrencyLeft': 500,
            'NewReservedConcurrencyValue': concurrent_executions
        })

    def test_set_reserved_concurrent_executions_empty_events(self):
        self.assertRaises(Exception, set_reserved_concurrent_executions, {}, None)

    def test_backup_reserved_concurrent_executions_empty_events(self):
        events = {}
        self.assertRaises(KeyError, backup_reserved_concurrent_executions, events, None)

    def test_backup_reserved_concurrent_executions_empty_response(self):
        events = {
            'LambdaARN': LAMBDA_ARN,
        }
        self.mock_lambda.get_function_concurrency.return_value = None
        response = backup_reserved_concurrent_executions(events, None)
        self.assertEqual(response, {
            "ReservedConcurrentExecutionsConfigured": False,
            "BackupReservedConcurrentExecutionsValue": 0
        })

    def test_backup_reserved_concurrent_executions_concurrency_configured(self):
        events = {
            'LambdaARN': LAMBDA_ARN,
        }
        reserved_concurrency = 10
        self.mock_lambda.get_function_concurrency.return_value = {
            'ReservedConcurrentExecutions': reserved_concurrency
        }
        response = backup_reserved_concurrent_executions(events, None)
        self.assertEqual(response, {
            "ReservedConcurrentExecutionsConfigured": True,
            "BackupReservedConcurrentExecutionsValue": reserved_concurrency
        })
