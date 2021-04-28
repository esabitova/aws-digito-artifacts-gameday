import datetime
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from dateutil.tz import tzlocal

import documents.util.scripts.src.apigw_util as apigw_util

USAGE_PLAN_ID: str = "jvgy9s"
USAGE_PLAN_LIMIT = 50000
USAGE_PLAN_PERIOD: str = "WEEK"
NEW_USAGE_PLAN_LIMIT = 50000
NEW_HUGECHANGE_USAGE_PLAN_LIMIT = 5000
NEW_USAGE_PLAN_PERIOD: str = "WEEK"

REST_API_GW_ID: str = "0djifyccl6"
REST_API_GW_STAGE_NAME: str = "DummyStage"
REST_API_GW_DEPLOYMENT_ID_V1: str = "j4ujo3"
REST_API_GW_DEPLOYMENT_ID_V2: str = "m2uen1"
REST_API_GW_DEPLOYMENT_CREATED_DATE_V1: datetime = datetime.datetime(2021, 4, 21, 18, 8, 10, tzinfo=tzlocal())
REST_API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 7, 10, tzinfo=tzlocal())
REST_API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 9, 10, tzinfo=tzlocal())


def get_sample_get_usage_plan_response():
    response = {
        "quota": {
            "limit": USAGE_PLAN_LIMIT,
            "period": USAGE_PLAN_PERIOD
        },
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        }
    }
    return response


def get_sample_https_status_code_403_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 403
        }
    }
    return response


def get_sample_update_usage_plan_response():
    response = {
        "quota": {
            "limit": NEW_USAGE_PLAN_LIMIT,
            "period": NEW_USAGE_PLAN_PERIOD
        },
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        }
    }
    return response


def get_sample_get_stage_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "deploymentId": REST_API_GW_DEPLOYMENT_ID_V1,
        "stageName": REST_API_GW_STAGE_NAME
    }
    return response


def get_sample_update_stage_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "deploymentId": REST_API_GW_DEPLOYMENT_ID_V2,
        "stageName": REST_API_GW_STAGE_NAME
    }
    return response


def get_sample_get_deployment_response(deployment_id, created_date):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "id": deployment_id,
        "createdDate": created_date
    }
    return response


def get_sample_get_deployments_response_with_1_deployment():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "items": [
            {
                'id': REST_API_GW_DEPLOYMENT_ID_V1,
                'description': 'Dummy deployment',
                'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
            }
        ]
    }
    return response


def get_sample_get_deployments_response_with_2_deployments():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "items": [
            {
                'id': REST_API_GW_DEPLOYMENT_ID_V2,
                'description': 'Dummy deployment 2',
                'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1
            },
            {
                'id': REST_API_GW_DEPLOYMENT_ID_V1,
                'description': 'Dummy deployment 1',
                'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
            }
        ]
    }
    return response


def get_sample_get_deployments_response_with_6_deployments():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "items": [
            {'id': 'zpju28', 'description': 'Dummy deployment 6',
             'createdDate': datetime.datetime(2021, 4, 21, 18, 11, 10, tzinfo=tzlocal())},
            {'id': 'zo5n6k', 'description': 'Dummy deployment 5',
             'createdDate': datetime.datetime(2021, 4, 21, 18, 10, 10, tzinfo=tzlocal())},
            {'id': 'zk1f7c', 'description': 'Dummy deployment 4',
             'createdDate': datetime.datetime(2021, 4, 21, 18, 9, 10, tzinfo=tzlocal())},
            {'id': REST_API_GW_DEPLOYMENT_ID_V1, 'description': 'Dummy deployment 3',
             'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_V1},
            {'id': REST_API_GW_DEPLOYMENT_ID_V2, 'description': 'Dummy deployment 2',
             'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1},
            {'id': 'xfjve2', 'description': 'Dummy deployment 1',
             'createdDate': datetime.datetime(2021, 4, 21, 18, 6, 10, tzinfo=tzlocal())}
        ]
    }
    return response


@pytest.mark.unit_test
class TestApigwUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigw = MagicMock()
        self.side_effect_map = {
            'apigateway': self.mock_apigw
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigw.get_usage_plan.return_value = get_sample_get_usage_plan_response()
        self.mock_apigw.update_usage_plan.return_value = get_sample_update_usage_plan_response()
        self.mock_apigw.get_stage.return_value = get_sample_get_stage_response()
        self.mock_apigw.update_stage.return_value = get_sample_update_stage_response()

    def tearDown(self):
        self.patcher.stop()

    def test_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        output = apigw_util.check_limit_and_period(events, None)
        self.assertEqual("ok", output['Result'])

    def test_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        output = apigw_util.set_limit_and_period(events, None)
        self.assertEqual(NEW_USAGE_PLAN_LIMIT, output['Limit'])
        self.assertEqual(NEW_USAGE_PLAN_PERIOD, output['Period'])

    def test_input1_check_limit_and_period(self):
        events = {}
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            apigw_util.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_input2_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            apigw_util.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_input3_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT

        with pytest.raises(KeyError) as exception_info:
            apigw_util.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))

    def test_input1_set_limit_and_period(self):
        events = {}
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            apigw_util.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_input2_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            apigw_util.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_input3_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT

        with pytest.raises(KeyError) as exception_info:
            apigw_util.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))

    def test_get_deployment(self):
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V2, REST_API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1
        )
        output = apigw_util.get_deployment(REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V2)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['id'])

    def test_get_deployments(self):
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()
        output = apigw_util.get_deployments(REST_API_GW_ID)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['items'][0]['id'])

    def test_get_stage(self):
        output = apigw_util.get_stage(REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['deploymentId'])

    def test_find_deployment_id_for_update_with_provided_id(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V2
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V2, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw_util.find_deployment_id_for_update(events, None)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_with_provided_deployment_id_same_as_current(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V1

        with pytest.raises(ValueError) as exception_info:
            apigw_util.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Provided deployment ID and current deployment ID should not be the same'))

    def test_find_deployment_id_for_update_without_provided_id(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_6_deployments()
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V1, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw_util.find_deployment_id_for_update(events, None)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_available_deployments(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()

        with pytest.raises(ValueError) as exception_info:
            apigw_util.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'There are no deployments found to apply in RestApiGateway ID: '
                                             f'{REST_API_GW_ID}, except current deployment ID: '
                                             f'{REST_API_GW_DEPLOYMENT_ID_V1}'))

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_previous_deployments(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_2_deployments()
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V1, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        with pytest.raises(ValueError) as exception_info:
            apigw_util.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'Could not find any existing deployment which has createdDate less than '
                                             f'current deployment ID: {REST_API_GW_DEPLOYMENT_ID_V1}'))

    def test_input1_deployment_id_for_update(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID

        with pytest.raises(KeyError) as exception_info:
            apigw_util.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires RestStageName in events'))

    def test_input2_deployment_id_for_update(self):
        events = {}
        events['RestStageName'] = REST_API_GW_STAGE_NAME

        with pytest.raises(KeyError) as exception_info:
            apigw_util.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_update_deployment(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V2

        output = apigw_util.update_deployment(events, None)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdNewValue'])

    def test_input1_update_deployment(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME

        with pytest.raises(KeyError) as exception_info:
            apigw_util.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestDeploymentId in events'))

    def test_input2_update_deployment(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V1

        with pytest.raises(KeyError) as exception_info:
            apigw_util.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestStageName in events'))

    def test_input3_update_deployment(self):
        events = {}
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V1

        with pytest.raises(KeyError) as exception_info:
            apigw_util.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))


@pytest.mark.unit_test
class TestApigwUtilValueExceptions(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigw = MagicMock()
        self.side_effect_map = {
            'apigateway': self.mock_apigw
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigw.get_usage_plan.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.update_usage_plan.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_deployment.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_deployments.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_stage.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.update_stage.return_value = get_sample_https_status_code_403_response()

    def tearDown(self):
        self.patcher.stop()

    def test_error_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(ValueError) as exception_info:
            apigw_util.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to get usage plan limit and period'))

    def test_error_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(ValueError) as exception_info:
            apigw_util.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to update usage plan limit and period'))

    def test_error_https_status_code_200(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_util.assert_https_status_code_200(get_sample_https_status_code_403_response(), 'Error message')
        self.assertTrue(exception_info.match('Error message'))

    def test_error_get_deployment(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_util.get_deployment(REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V1)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployment with restApiId: {REST_API_GW_ID} '
                                             f'and deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_deployments(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_util.get_deployments(REST_API_GW_ID)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployments with restApiId: {REST_API_GW_ID} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_stage(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_util.get_stage(REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.assertTrue(exception_info.match(f'Failed to perform get_stage with restApiId: {REST_API_GW_ID} '
                                             f'and stageName: {REST_API_GW_STAGE_NAME} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_update_deployment(self):
        events = {}
        events['RestApiGwId'] = REST_API_GW_ID
        events['RestStageName'] = REST_API_GW_STAGE_NAME
        events['RestDeploymentId'] = REST_API_GW_DEPLOYMENT_ID_V1

        with pytest.raises(ValueError) as exception_info:
            apigw_util.update_deployment(events, None)
        self.assertTrue(exception_info.match(f'Failed to perform update_stage with restApiId: {REST_API_GW_ID}, '
                                             f'stageName: {REST_API_GW_STAGE_NAME} and '
                                             f'deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))


@pytest.mark.unit_test
class TestApigwUtilAssertionExceptions(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigw = MagicMock()
        self.side_effect_map = {
            'apigateway': self.mock_apigw
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigw.get_usage_plan.return_value = get_sample_get_usage_plan_response()

    def tearDown(self):
        self.patcher.stop()

    def test_error_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_HUGECHANGE_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(AssertionError) as exception_info:
            apigw_util.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('.*'))
