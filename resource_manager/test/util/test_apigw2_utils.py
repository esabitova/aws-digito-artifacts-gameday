import unittest
from unittest.mock import MagicMock

import pytest

import resource_manager.src.util.apigw2_utils as apigw2_utils
import resource_manager.src.util.boto3_client_factory as client_factory
from documents.util.scripts.test.test_apigw2_utils import get_sample_get_service_quota_response_side_effect, \
    QUOTA_RATE_LIMIT, QUOTA_BURST_LIMIT

API_GW_ID = "0djifyccl6"
API_GW_STAGE_NAME = "DummyStage"
API_GW_DEPLOYMENT_ID = "j4ujo3"
API_GW_ROUTE_KEY = "$some route/key"
INITIAL_THROTTLE_RATE_LIMIT: float = 100.0
INITIAL_THROTTLE_BURST_LIMIT: int = 100
NEW_THROTTLE_RATE_LIMIT: float = 80.0
NEW_THROTTLE_BURST_LIMIT: int = 80


def get_sample_create_deployment_response(https_status_code):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": https_status_code
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID
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
        "DeploymentId": API_GW_DEPLOYMENT_ID,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {}
    }
    return response


def get_sample_get_stage_default_initital_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {
            'ThrottlingRateLimit': INITIAL_THROTTLE_RATE_LIMIT,
            'ThrottlingBurstLimit': INITIAL_THROTTLE_BURST_LIMIT
        },
        "RouteSettings": {}
    }
    return response


def get_sample_get_stage_route_initital_response(route_key):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {
            route_key: {
                'ThrottlingRateLimit': INITIAL_THROTTLE_RATE_LIMIT,
                'ThrottlingBurstLimit': INITIAL_THROTTLE_BURST_LIMIT
            }
        }
    }
    return response


def get_sample_update_stage_response(https_status_code):
    return get_sample_get_stage_response(https_status_code)


def get_sample_update_stage_default_throttling(rate, burst):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {
            'ThrottlingRateLimit': rate,
            'ThrottlingBurstLimit': burst
        },
        "RouteSettings": {}
    }
    return response


def get_sample_update_stage_route_throttling(route_key, rate, burst):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {
            route_key: {
                'ThrottlingRateLimit': rate,
                'ThrottlingBurstLimit': burst
            }
        }
    }
    return response


@pytest.mark.unit_test
class TestApiGwUtil(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.mock_apigwv2 = MagicMock()
        self.mock_service_quotas = MagicMock()
        self.client_side_effect_map = {
            'apigatewayv2': self.mock_apigwv2,
            'service-quotas': self.mock_service_quotas
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    def test_create_deployment(self):
        self.mock_apigwv2.create_deployment.return_value = get_sample_create_deployment_response(201)
        result = apigw2_utils.create_deployment(self.session_mock, API_GW_ID, 'Dummy deployment')
        self.mock_apigwv2.create_deployment.assert_called_once_with(
            ApiId=API_GW_ID, Description='Dummy deployment'
        )
        self.assertEqual(API_GW_DEPLOYMENT_ID, result['DeploymentId'])

    def test_create_deployment_error(self):
        self.mock_apigwv2.create_deployment.return_value = get_sample_create_deployment_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw2_utils.create_deployment(self.session_mock, API_GW_ID, 'Dummy deployment')
        self.assertTrue(exception_info.match('Failed to create deployment: Dummy deployment, '
                                             f'ApiId: {API_GW_ID} '
                                             f'Response is: {get_sample_create_deployment_response(403)}'))

    def test_delete_deployment(self):
        self.mock_apigwv2.delete_deployment.return_value = get_sample_create_deployment_response(202)
        result = apigw2_utils.delete_deployment(self.session_mock, API_GW_ID, API_GW_DEPLOYMENT_ID)
        self.mock_apigwv2.delete_deployment.assert_called_once_with(
            ApiId=API_GW_ID, DeploymentId=API_GW_DEPLOYMENT_ID
        )
        self.assertEqual(True, result)

    def test_delete_deployment_error(self):
        self.mock_apigwv2.delete_deployment.return_value = get_sample_create_deployment_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw2_utils.delete_deployment(self.session_mock, API_GW_ID, API_GW_DEPLOYMENT_ID)
        self.assertTrue(exception_info.match(f'Failed to delete DeploymentId: {API_GW_DEPLOYMENT_ID}, '
                                             f'ApiId: {API_GW_ID} '
                                             f'Response is: {get_sample_create_deployment_response(403)}'))

    def test_get_stage(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(200)
        result = apigw2_utils.get_stage(self.session_mock, API_GW_ID, API_GW_STAGE_NAME)
        self.mock_apigwv2.get_stage.assert_called_once_with(ApiId=API_GW_ID, StageName=API_GW_STAGE_NAME)
        self.assertEqual(API_GW_DEPLOYMENT_ID, result['DeploymentId'])

    def test_get_stage_error(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw2_utils.get_stage(self.session_mock, API_GW_ID, API_GW_STAGE_NAME)
        self.assertTrue(exception_info.match(f'Failed to perform get_stage with ApiId: {API_GW_ID} '
                                             f'and StageName: {API_GW_STAGE_NAME} '
                                             f'Response is: {get_sample_get_stage_response(403)}'))

    def test_update_stage_deployment(self):
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_response(200)
        result = apigw2_utils.update_stage_deployment(
            self.session_mock, API_GW_ID, API_GW_STAGE_NAME, API_GW_DEPLOYMENT_ID
        )
        self.mock_apigwv2.update_stage.assert_called_once_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME,
            DeploymentId=API_GW_DEPLOYMENT_ID
        )
        self.assertEqual(API_GW_DEPLOYMENT_ID, result['DeploymentId'])

    def test_update_stage_deployment_error(self):
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_response(403)

        with pytest.raises(AssertionError) as exception_info:
            apigw2_utils.update_stage_deployment(
                self.session_mock, API_GW_ID, API_GW_STAGE_NAME, API_GW_DEPLOYMENT_ID
            )
        self.assertTrue(exception_info.match(f'Failed to perform update_stage with ApiId: {API_GW_ID}, '
                                             f'StageName: {API_GW_STAGE_NAME} '
                                             f'and DeploymentId: {API_GW_DEPLOYMENT_ID} '
                                             f'Response is: {get_sample_get_stage_response(403)}'))

    def test_get_default_throttling_settings(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_initital_response()
        result = apigw2_utils.get_default_throttling_settings(self.session_mock, API_GW_ID, API_GW_STAGE_NAME)
        self.assertEqual(INITIAL_THROTTLE_RATE_LIMIT, result['ThrottlingRateLimit'])
        self.assertEqual(INITIAL_THROTTLE_BURST_LIMIT, result['ThrottlingBurstLimit'])

    def test_get_default_throttling_settings_no_initial(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(200)
        result = apigw2_utils.get_default_throttling_settings(self.session_mock, API_GW_ID, API_GW_STAGE_NAME)
        self.assertEqual(QUOTA_RATE_LIMIT, result['ThrottlingRateLimit'])
        self.assertEqual(QUOTA_BURST_LIMIT, result['ThrottlingBurstLimit'])

    def test_get_route_throttling_settings(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_route_initital_response(API_GW_ROUTE_KEY)
        result = apigw2_utils.get_route_throttling_settings(
            self.session_mock, API_GW_ID, API_GW_STAGE_NAME, API_GW_ROUTE_KEY
        )
        self.assertEqual(INITIAL_THROTTLE_RATE_LIMIT, result['ThrottlingRateLimit'])
        self.assertEqual(INITIAL_THROTTLE_BURST_LIMIT, result['ThrottlingBurstLimit'])

    def test_get_route_throttling_settings_no_initial(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(200)
        result = apigw2_utils.get_route_throttling_settings(
            self.session_mock, API_GW_ID, API_GW_STAGE_NAME, API_GW_ROUTE_KEY
        )
        self.assertEqual(False, result['ThrottlingRateLimit'])
        self.assertEqual(False, result['ThrottlingBurstLimit'])

    def test_update_default_throttling_settings(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(200)
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_default_throttling(
            NEW_THROTTLE_RATE_LIMIT, NEW_THROTTLE_BURST_LIMIT
        )
        result = apigw2_utils.update_default_throttling_settings(
            self.session_mock, API_GW_ID, API_GW_STAGE_NAME, str(NEW_THROTTLE_RATE_LIMIT), str(NEW_THROTTLE_BURST_LIMIT)
        )
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, result['DefaultRouteSettings']['ThrottlingRateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, result['DefaultRouteSettings']['ThrottlingBurstLimit'])

    def test_update_route_throttling_settings(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response(200)
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_route_throttling(
            API_GW_ROUTE_KEY, NEW_THROTTLE_RATE_LIMIT, NEW_THROTTLE_BURST_LIMIT
        )
        result = apigw2_utils.update_route_throttling_settings(
            self.session_mock, API_GW_ID, API_GW_STAGE_NAME, API_GW_ROUTE_KEY,
            int(NEW_THROTTLE_RATE_LIMIT), NEW_THROTTLE_BURST_LIMIT
        )
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, result['RouteSettings'][API_GW_ROUTE_KEY]['ThrottlingRateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, result['RouteSettings'][API_GW_ROUTE_KEY]['ThrottlingBurstLimit'])
