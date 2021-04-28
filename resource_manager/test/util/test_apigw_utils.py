import unittest
from unittest.mock import MagicMock

import pytest

import resource_manager.src.util.apigw_utils as apigw_utils
import resource_manager.src.util.boto3_client_factory as client_factory

REST_API_GW_ID = "0djifyccl6"
REST_API_GW_STAGE_NAME = "DummyStage"
REST_API_GW_DEPLOYMENT_ID_V1 = "j4ujo3"


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
