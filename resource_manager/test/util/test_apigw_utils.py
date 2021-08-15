import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

import resource_manager.src.util.apigw_utils as apigw_utils
import resource_manager.src.util.boto3_client_factory as client_factory
from documents.util.scripts.test.mock_sleep import MockSleep

REST_API_GW_ID = "0djifyccl6"
REST_API_GW_STAGE_NAME = "DummyStage"
REST_API_GW_DEPLOYMENT_ID_V1 = "j4ujo3"
USAGE_PLAN_ID: str = "jvgy9s"
USAGE_PLAN_THROTTLE_RATE_LIMIT: float = 100.0
USAGE_PLAN_THROTTLE_BURST_LIMIT: int = 100
NEW_THROTTLE_RATE_LIMIT: float = 80.0
NEW_THROTTLE_BURST_LIMIT: int = 80


def get_sample_create_deployment_response(https_status_code):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": https_status_code
        },
        "id": REST_API_GW_DEPLOYMENT_ID_V1
    }
    return response


def get_sample_delete_deployment_response(https_status_code):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": https_status_code
        }
    }
    return response


def get_sample_get_stage_response(https_status_code):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": https_status_code
        },
        "deploymentId": REST_API_GW_DEPLOYMENT_ID_V1,
        "stageName": REST_API_GW_STAGE_NAME
    }
    return response


def get_sample_update_stage_response(https_status_code):
    return get_sample_get_stage_response(https_status_code)


def get_sample_update_usage_plan_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "throttle": {
            "burstLimit": NEW_THROTTLE_BURST_LIMIT,
            "rateLimit": NEW_THROTTLE_RATE_LIMIT
        },
        "apiStages": [
            {
                "apiId": REST_API_GW_ID,
                "stage": REST_API_GW_STAGE_NAME,
                "throttle": {
                    "*/*": {
                        "burstLimit": NEW_THROTTLE_BURST_LIMIT,
                        "rateLimit": NEW_THROTTLE_RATE_LIMIT
                    }
                }
            }
        ]
    }
    return response


def get_sample_get_usage_plan_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "throttle": {
            "burstLimit": USAGE_PLAN_THROTTLE_BURST_LIMIT,
            "rateLimit": USAGE_PLAN_THROTTLE_RATE_LIMIT
        },
        "apiStages": [
            {
                "apiId": REST_API_GW_ID,
                "stage": REST_API_GW_STAGE_NAME,
                "throttle": {
                    "*/*": {
                        "burstLimit": USAGE_PLAN_THROTTLE_BURST_LIMIT,
                        "rateLimit": USAGE_PLAN_THROTTLE_RATE_LIMIT
                    }
                }
            }
        ]
    }
    return response


@pytest.mark.unit_test
class TestApiGwUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_apigw = MagicMock()
        self.client_side_effect_map = {
            'apigateway': self.mock_apigw
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.mock_apigw.update_usage_plan.return_value = get_sample_update_usage_plan_response()
        self.mock_apigw.get_usage_plan.return_value = get_sample_get_usage_plan_response()

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_create_deployment(self):
        self.mock_apigw.create_deployment.return_value = get_sample_create_deployment_response(201)
        result = apigw_utils.create_deployment(self.session_mock, REST_API_GW_ID, 'Dummy deployment')
        self.mock_apigw.create_deployment.assert_called_once_with(
            restApiId=REST_API_GW_ID, description='Dummy deployment'
        )
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, result['id'])

    def test_create_deployment_error(self):
        self.mock_apigw.create_deployment.return_value = get_sample_create_deployment_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.create_deployment(self.session_mock, REST_API_GW_ID, 'Dummy deployment')
        self.assertTrue(exception_info.match('Failed to create deployment: Dummy deployment, '
                                             f'restApiId: {REST_API_GW_ID} '
                                             f'Response is: {get_sample_create_deployment_response(403)}'))

    def test_delete_deployment(self):
        self.mock_apigw.delete_deployment.return_value = get_sample_create_deployment_response(202)
        result = apigw_utils.delete_deployment(self.session_mock, REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V1)
        self.mock_apigw.delete_deployment.assert_called_once_with(
            restApiId=REST_API_GW_ID, deploymentId=REST_API_GW_DEPLOYMENT_ID_V1
        )
        self.assertEqual(True, result)

    def test_delete_deployment_error(self):
        self.mock_apigw.delete_deployment.return_value = get_sample_create_deployment_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.delete_deployment(self.session_mock, REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V1)
        self.assertTrue(exception_info.match(f'Failed to delete deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1}, '
                                             f'restApiId: {REST_API_GW_ID} '
                                             f'Response is: {get_sample_create_deployment_response(403)}'))

    def test_get_stage(self):
        self.mock_apigw.get_stage.return_value = get_sample_get_stage_response(200)
        result = apigw_utils.get_stage(self.session_mock, REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.mock_apigw.get_stage.assert_called_once_with(restApiId=REST_API_GW_ID, stageName=REST_API_GW_STAGE_NAME)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, result['deploymentId'])

    def test_get_stage_error(self):
        self.mock_apigw.get_stage.return_value = get_sample_get_stage_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.get_stage(self.session_mock, REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.assertTrue(exception_info.match(f'Failed to perform get_stage with restApiId: {REST_API_GW_ID} '
                                             f'and stageName: {REST_API_GW_STAGE_NAME} '
                                             f'Response is: {get_sample_get_stage_response(403)}'))

    def test_update_stage_deployment(self):
        self.mock_apigw.update_stage.return_value = get_sample_update_stage_response(200)
        result = apigw_utils.update_stage_deployment(
            self.session_mock, REST_API_GW_ID, REST_API_GW_STAGE_NAME, REST_API_GW_DEPLOYMENT_ID_V1
        )
        self.mock_apigw.update_stage.assert_called_once_with(
            restApiId=REST_API_GW_ID,
            stageName=REST_API_GW_STAGE_NAME,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/deploymentId',
                    'value': REST_API_GW_DEPLOYMENT_ID_V1,
                },
            ]
        )
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, result['deploymentId'])

    def test_update_stage_deployment_error(self):
        self.mock_apigw.update_stage.return_value = get_sample_update_stage_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.update_stage_deployment(
                self.session_mock, REST_API_GW_ID, REST_API_GW_STAGE_NAME, REST_API_GW_DEPLOYMENT_ID_V1
            )
        self.assertTrue(exception_info.match(f'Failed to perform update_stage with restApiId: {REST_API_GW_ID}, '
                                             f'stageName: {REST_API_GW_STAGE_NAME} '
                                             f'and deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_get_stage_response(403)}'))

    def test_update_usage_plan(self):
        output = apigw_utils.update_usage_plan(self.session_mock, USAGE_PLAN_ID, [])
        self.mock_apigw.update_usage_plan.assert_called_with(
            usagePlanId=USAGE_PLAN_ID,
            patchOperations=[]
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['throttle']['rateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['throttle']['burstLimit'])

    @patch('time.sleep')
    def test_update_usage_plan_with_too_many_requests_exception_and_normal_execution(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.mock_apigw.update_usage_plan.side_effect = [
            ClientError(
                error_response={"Error": {"Code": "TooManyRequestsException"}},
                operation_name='UpdateUsagePlan'
            ),
            get_sample_update_usage_plan_response()
        ]
        output = apigw_utils.update_usage_plan(self.session_mock, USAGE_PLAN_ID, [])
        self.mock_apigw.update_usage_plan.assert_called_with(
            usagePlanId=USAGE_PLAN_ID,
            patchOperations=[]
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['throttle']['rateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['throttle']['burstLimit'])

    @patch('time.sleep')
    def test_update_usage_plan_with_too_many_requests_exception_and_failed_execution(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        self.mock_apigw.update_usage_plan.side_effect = ClientError(
            error_response={"Error": {"Code": "TooManyRequestsException"}},
            operation_name='UpdateUsagePlan'
        )
        with pytest.raises(Exception) as exception_info:
            apigw_utils.update_usage_plan(self.session_mock, USAGE_PLAN_ID, [], 5)
        self.assertTrue(exception_info.match('Could not perform update_usage_plan successfully for 5 times'))

    def test_update_usage_plan_with_unknown_exception(self):
        self.mock_apigw.update_usage_plan.side_effect = ClientError(
            error_response={"Error": {"Code": "UnknownException"}},
            operation_name='UpdateUsagePlan'
        )
        with self.assertRaises(Exception) as e:
            apigw_utils.update_usage_plan(self.session_mock, USAGE_PLAN_ID, [])

        self.assertEqual(e.exception.response['Error']['Code'], 'UnknownException')

    def test_set_throttling_settings_with_provided_stage_name(self):
        output = apigw_utils.set_throttling_settings(
            self.session_mock,
            USAGE_PLAN_ID,
            NEW_THROTTLE_RATE_LIMIT,
            NEW_THROTTLE_BURST_LIMIT,
            REST_API_GW_ID,
            REST_API_GW_STAGE_NAME
        )
        self.mock_apigw.update_usage_plan.assert_called_with(
            usagePlanId=USAGE_PLAN_ID,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': f'/apiStages/{REST_API_GW_ID}:{REST_API_GW_STAGE_NAME}/throttle/*/*/rateLimit',
                    'value': str(NEW_THROTTLE_RATE_LIMIT)
                },
                {
                    'op': 'replace',
                    'path': f'/apiStages/{REST_API_GW_ID}:{REST_API_GW_STAGE_NAME}/throttle/*/*/burstLimit',
                    'value': str(NEW_THROTTLE_BURST_LIMIT)
                }
            ]
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_set_throttling_settings_without_provided_stage_name(self):
        output = apigw_utils.set_throttling_settings(
            self.session_mock,
            USAGE_PLAN_ID,
            NEW_THROTTLE_RATE_LIMIT,
            NEW_THROTTLE_BURST_LIMIT
        )
        self.mock_apigw.update_usage_plan.assert_called_with(
            usagePlanId=USAGE_PLAN_ID,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/throttle/rateLimit',
                    'value': str(NEW_THROTTLE_RATE_LIMIT)
                },
                {
                    'op': 'replace',
                    'path': '/throttle/burstLimit',
                    'value': str(NEW_THROTTLE_BURST_LIMIT)
                }
            ]
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_get_usage_plan_with_provided_stage_name(self):
        output = apigw_utils.get_usage_plan(
            self.session_mock,
            USAGE_PLAN_ID,
            REST_API_GW_ID,
            REST_API_GW_STAGE_NAME
        )
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_get_usage_plan_without_provided_stage_name(self):
        output = apigw_utils.get_usage_plan(
            self.session_mock,
            USAGE_PLAN_ID
        )
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['BurstLimit'])
