import datetime
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.config import Config
from dateutil.tz import tzlocal

import documents.util.scripts.src.apigw2_utils as apigw2_utils

BOTO3_CONFIG: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})

API_GW_ID: str = "0djifyccl6"
API_GW_STAGE_NAME: str = "DummyStage"
API_GW_DEPLOYMENT_ID_V1: str = "j4ujo3"
API_GW_DEPLOYMENT_ID_V2: str = "m2uen1"
API_GW_ROUTE_KEY: str = "$some route/route"
API_GW_DEPLOYMENT_CREATED_DATE_V1: datetime = datetime.datetime(2021, 4, 21, 18, 8, 10, tzinfo=tzlocal())
API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 7, 10, tzinfo=tzlocal())
API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 9, 10, tzinfo=tzlocal())

QUOTA_SERVICE_CODE: str = 'apigateway'
QUOTA_RATE_LIMIT: float = 10000.0
QUOTA_RATE_LIMIT_CODE: str = 'L-8A5B8E43'
QUOTA_BURST_LIMIT: float = 5000.0
QUOTA_BURST_LIMIT_CODE: str = 'L-CDF5615A'

INITIAL_THROTTLE_RATE_LIMIT: float = 100.0
NEW_THROTTLE_RATE_LIMIT: float = 80.0
LESS_THROTTLE_RATE_LIMIT: float = 49.0
MORE_THROTTLE_RATE_LIMIT: float = 151.0
HUGE_THROTTLE_RATE_LIMIT: float = 11000.0

INITIAL_THROTTLE_BURST_LIMIT: int = 100
NEW_THROTTLE_BURST_LIMIT: int = 80
LESS_THROTTLE_BURST_LIMIT: int = 49
MORE_THROTTLE_BURST_LIMIT: int = 151
HUGE_THROTTLE_BURST_LIMIT: int = 6000


def get_sample_https_status_code_403_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 403
        }
    }
    return response


def get_sample_get_stage_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V1,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {}
    }
    return response


def get_sample_get_stage_default_throttling_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V1,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {
            "ThrottlingBurstLimit": INITIAL_THROTTLE_BURST_LIMIT,
            "ThrottlingRateLimit": INITIAL_THROTTLE_RATE_LIMIT
        },
        "RouteSettings": {}
    }
    return response


def get_sample_get_stage_throttling_response(route_key):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V1,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {
            route_key: {
                "ThrottlingBurstLimit": INITIAL_THROTTLE_BURST_LIMIT,
                "ThrottlingRateLimit": INITIAL_THROTTLE_RATE_LIMIT
            }
        }
    }
    return response


def get_sample_update_stage_response():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V2,
        "StageName": API_GW_STAGE_NAME
    }
    return response


def get_sample_update_stage_default_throttle_response(rate, burst):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V2,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {
            "ThrottlingBurstLimit": rate,
            "ThrottlingRateLimit": burst
        },
        "RouteSettings": {}
    }
    return response


def get_sample_update_stage_throttle_response(route_key, rate, burst):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": API_GW_DEPLOYMENT_ID_V2,
        "StageName": API_GW_STAGE_NAME,
        "DefaultRouteSettings": {},
        "RouteSettings": {
            route_key: {
                "ThrottlingBurstLimit": rate,
                "ThrottlingRateLimit": burst
            }
        }
    }
    return response


def get_sample_get_deployment_response(deployment_id, created_date):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "DeploymentId": deployment_id,
        "CreatedDate": created_date
    }
    return response


def get_sample_get_deployments_response_with_1_deployment():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "Items": [
            {
                'DeploymentId': API_GW_DEPLOYMENT_ID_V1,
                'Description': 'Dummy deployment',
                'CreatedDate': API_GW_DEPLOYMENT_CREATED_DATE_V1
            }
        ]
    }
    return response


def get_sample_get_deployments_response_with_2_deployments():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "Items": [
            {
                'DeploymentId': API_GW_DEPLOYMENT_ID_V2,
                'Description': 'Dummy deployment 2',
                'CreatedDate': API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1
            },
            {
                'DeploymentId': API_GW_DEPLOYMENT_ID_V1,
                'Description': 'Dummy deployment 1',
                'CreatedDate': API_GW_DEPLOYMENT_CREATED_DATE_V1
            }
        ]
    }
    return response


def get_sample_get_deployments_response_with_6_deployments():
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "Items": [
            {'DeploymentId': 'zpju28', 'Description': 'Dummy deployment 6',
             'CreatedDate': datetime.datetime(2021, 4, 21, 18, 11, 10, tzinfo=tzlocal())},
            {'DeploymentId': 'zo5n6k', 'Description': 'Dummy deployment 5',
             'CreatedDate': datetime.datetime(2021, 4, 21, 18, 10, 10, tzinfo=tzlocal())},
            {'DeploymentId': 'zk1f7c', 'Description': 'Dummy deployment 4',
             'CreatedDate': datetime.datetime(2021, 4, 21, 18, 9, 10, tzinfo=tzlocal())},
            {'DeploymentId': API_GW_DEPLOYMENT_ID_V1, 'Description': 'Dummy deployment 3',
             'CreatedDate': API_GW_DEPLOYMENT_CREATED_DATE_V1},
            {'DeploymentId': API_GW_DEPLOYMENT_ID_V2, 'Description': 'Dummy deployment 2',
             'CreatedDate': API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1},
            {'DeploymentId': 'xfjve2', 'Description': 'Dummy deployment 1',
             'CreatedDate': datetime.datetime(2021, 4, 21, 18, 6, 10, tzinfo=tzlocal())}
        ]
    }
    return response


def get_sample_get_service_quota_response(quota_code: str, limit: float):
    response = {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        'Quota': {
            'ServiceCode': QUOTA_SERVICE_CODE,
            'QuotaCode': quota_code,
            'Value': limit
        }
    }
    return response


def get_sample_get_service_quota_response_side_effect():
    response = [
        get_sample_get_service_quota_response(QUOTA_RATE_LIMIT_CODE, QUOTA_RATE_LIMIT),
        get_sample_get_service_quota_response(QUOTA_BURST_LIMIT_CODE, QUOTA_BURST_LIMIT)
    ]
    return response


@pytest.mark.unit_test
class TestApigwv2Util(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigwv2 = MagicMock()
        self.mock_service_quotas = MagicMock()
        self.side_effect_map = {
            'apigatewayv2': self.mock_apigwv2,
            'service-quotas': self.mock_service_quotas
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response()
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_deployment(self):
        self.mock_apigwv2.get_deployment.return_value = get_sample_get_deployment_response(
            API_GW_DEPLOYMENT_ID_V2, API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1
        )
        output = apigw2_utils.get_deployment(API_GW_ID, API_GW_DEPLOYMENT_ID_V2)
        self.mock_apigwv2.get_deployment.assert_called_with(
            ApiId=API_GW_ID,
            DeploymentId=API_GW_DEPLOYMENT_ID_V2
        )
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V2, output['DeploymentId'])

    def test_get_deployments(self):
        self.mock_apigwv2.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()
        output = apigw2_utils.get_deployments(API_GW_ID)
        self.mock_apigwv2.get_deployments.assert_called_with(
            ApiId=API_GW_ID,
            MaxResults="25"
        )
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V1, output['Items'][0]['DeploymentId'])

    def test_get_stage(self):
        output = apigw2_utils.get_stage(API_GW_ID, API_GW_STAGE_NAME)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V1, output['DeploymentId'])

    def test_find_deployment_id_for_update_with_provided_id(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V2
        }
        self.mock_apigwv2.get_deployment.return_value = get_sample_get_deployment_response(
            API_GW_DEPLOYMENT_ID_V2, API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_with_provided_deployment_id_same_as_current(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Provided deployment ID and current deployment ID should not be the same'))

    def test_find_deployment_id_for_update_without_provided_id(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        self.mock_apigwv2.get_deployments.return_value = get_sample_get_deployments_response_with_6_deployments()
        self.mock_apigwv2.get_deployment.return_value = get_sample_get_deployment_response(
            API_GW_DEPLOYMENT_ID_V1, API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_available_deployments(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        self.mock_apigwv2.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()

        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'There are no deployments found to apply in ApiGateway ID: '
                                             f'{API_GW_ID}, except current deployment ID: '
                                             f'{API_GW_DEPLOYMENT_ID_V1}'))

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_previous_deployments(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        self.mock_apigwv2.get_deployments.return_value = get_sample_get_deployments_response_with_2_deployments()
        self.mock_apigwv2.get_deployment.return_value = get_sample_get_deployment_response(
            API_GW_DEPLOYMENT_ID_V1, API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'Could not find any existing deployment which has createdDate less than '
                                             f'current deployment ID: {API_GW_DEPLOYMENT_ID_V1}'))

    def test_update_deployment(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V2
        }
        output = apigw2_utils.update_deployment(events, None)
        self.mock_apigwv2.update_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME,
            DeploymentId=API_GW_DEPLOYMENT_ID_V2
        )
        self.assertIsNotNone(output)
        self.assertEqual(API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdNewValue'])

    def test_get_service_quota(self):
        self.mock_service_quotas.get_service_quota.return_value = get_sample_get_service_quota_response(
            QUOTA_RATE_LIMIT_CODE,
            QUOTA_RATE_LIMIT
        )
        output = apigw2_utils.get_service_quota(BOTO3_CONFIG, QUOTA_SERVICE_CODE, QUOTA_RATE_LIMIT_CODE)
        self.mock_service_quotas.get_service_quota.assert_called_with(
            ServiceCode=QUOTA_SERVICE_CODE,
            QuotaCode=QUOTA_RATE_LIMIT_CODE
        )
        self.assertIsNotNone(output)
        self.assertEqual(QUOTA_RATE_LIMIT, output['Quota']['Value'])

    def test_validate_auto_deploy(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        output = apigw2_utils.validate_auto_deploy(events, None)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertEqual(True, output)

    def test_validate_auto_deploy_enabled(self):
        self.mock_apigwv2.get_stage.return_value = {
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            },
            "DeploymentId": API_GW_DEPLOYMENT_ID_V1,
            "StageName": API_GW_STAGE_NAME,
            "AutoDeploy": True
        }
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.validate_auto_deploy(events, None)
        self.assertTrue(exception_info.match('AutoDeploy must be turned off to update deployment manually'))
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )

    def test_validate_throttling_config_without_route_key(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_throttling_response()
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        output = apigw2_utils.validate_throttling_config(events, None)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(INITIAL_THROTTLE_RATE_LIMIT, output['OriginalRateLimit'])
        self.assertEqual(INITIAL_THROTTLE_BURST_LIMIT, output['OriginalBurstLimit'])

    def test_validate_throttling_config_with_route_key(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_throttling_response(API_GW_ROUTE_KEY)
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsRouteKey': API_GW_ROUTE_KEY
        }
        output = apigw2_utils.validate_throttling_config(events, None)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(INITIAL_THROTTLE_RATE_LIMIT, output['OriginalRateLimit'])
        self.assertEqual(INITIAL_THROTTLE_BURST_LIMIT, output['OriginalBurstLimit'])

    def test_validate_throttling_config_with_new_rate_limit_increased_more_than_50_percent(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_throttling_response()
        events = {
            'HttpWsThrottlingRate': MORE_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_rate_limit_decreased_more_than_50_percent(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_throttling_response()
        events = {
            'HttpWsThrottlingRate': LESS_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_burst_limit_increased_more_than_50_percent(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_throttling_response()
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': MORE_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Burst rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_burst_limit_decreased_more_than_50_percent(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_default_throttling_response()
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': LESS_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Burst rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_burst_limit_decreased_more_than_50p_no_initial(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response()
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': LESS_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID
        }
        output = apigw2_utils.validate_throttling_config(events, None)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(0, output['OriginalRateLimit'])
        self.assertEqual(0, output['OriginalBurstLimit'])

    def test_validate_throttling_config_with_new_burst_limit_decreased_more_than_50p_no_initial_with_route_key(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_response()
        events = {
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': LESS_THROTTLE_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsRouteKey': API_GW_ROUTE_KEY
        }
        output = apigw2_utils.validate_throttling_config(events, None)
        self.mock_apigwv2.get_stage.assert_called_with(
            ApiId=API_GW_ID,
            StageName=API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(0, output['OriginalRateLimit'])
        self.assertEqual(0, output['OriginalBurstLimit'])

    def test_set_throttling_config_with_route_key(self):
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_throttle_response(
            API_GW_ROUTE_KEY, NEW_THROTTLE_RATE_LIMIT, NEW_THROTTLE_BURST_LIMIT
        )
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsRouteKey': API_GW_ROUTE_KEY
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        output = apigw2_utils.set_throttling_config(events, None)
        self.mock_apigwv2.update_stage.assert_called_with(
            ApiId=API_GW_ID, StageName=API_GW_STAGE_NAME, RouteSettings={
                API_GW_ROUTE_KEY: {
                    'ThrottlingRateLimit': NEW_THROTTLE_RATE_LIMIT,
                    'ThrottlingBurstLimit': NEW_THROTTLE_BURST_LIMIT
                }
            }
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_set_throttling_config_with_route_key_initial(self):
        self.mock_apigwv2.get_stage.return_value = get_sample_get_stage_throttling_response(API_GW_ROUTE_KEY)
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_throttle_response(
            API_GW_ROUTE_KEY, NEW_THROTTLE_RATE_LIMIT, NEW_THROTTLE_BURST_LIMIT
        )
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'HttpWsRouteKey': API_GW_ROUTE_KEY
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        output = apigw2_utils.set_throttling_config(events, None)
        self.mock_apigwv2.update_stage.assert_called_with(
            ApiId=API_GW_ID, StageName=API_GW_STAGE_NAME, RouteSettings={
                API_GW_ROUTE_KEY: {
                    'ThrottlingRateLimit': NEW_THROTTLE_RATE_LIMIT,
                    'ThrottlingBurstLimit': NEW_THROTTLE_BURST_LIMIT
                }
            }
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_set_throttling_config_without_route_key(self):
        self.mock_apigwv2.update_stage.return_value = get_sample_update_stage_default_throttle_response(
            NEW_THROTTLE_RATE_LIMIT, NEW_THROTTLE_BURST_LIMIT
        )
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        output = apigw2_utils.set_throttling_config(events, None)
        self.mock_apigwv2.update_stage.assert_called_with(
            ApiId=API_GW_ID, StageName=API_GW_STAGE_NAME, DefaultRouteSettings={
                'ThrottlingRateLimit': NEW_THROTTLE_RATE_LIMIT,
                'ThrottlingBurstLimit': NEW_THROTTLE_BURST_LIMIT
            }
        )
        self.assertIsNotNone(output)
        self.assertEqual(NEW_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(NEW_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_set_throttling_config_with_rate_above_account_limit(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsThrottlingRate': HUGE_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match(f'Given value of HttpWsThrottlingRate: {HUGE_THROTTLE_RATE_LIMIT}, '
                                             f'can not be more than service quota Throttle rate: {QUOTA_RATE_LIMIT}'))

    def test_set_throttling_config_with_burst_above_account_limit(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'HttpWsThrottlingBurst': HUGE_THROTTLE_BURST_LIMIT,
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match(f'Given value of HttpWsThrottlingBurst: {HUGE_THROTTLE_BURST_LIMIT}, '
                                             f'can not be more than service quota Throttle burst rate: '
                                             f'{QUOTA_BURST_LIMIT}'))


@pytest.mark.unit_test
class TestApigwUtilValueExceptions(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigwv2 = MagicMock()
        self.mock_service_quotas = MagicMock()
        self.side_effect_map = {
            'apigatewayv2': self.mock_apigwv2,
            'service-quotas': self.mock_service_quotas
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigwv2.get_deployment.return_value = get_sample_https_status_code_403_response()
        self.mock_apigwv2.get_deployments.return_value = get_sample_https_status_code_403_response()
        self.mock_apigwv2.get_stage.return_value = get_sample_https_status_code_403_response()
        self.mock_apigwv2.update_stage.return_value = get_sample_https_status_code_403_response()
        self.mock_service_quotas.get_service_quota.return_value = get_sample_https_status_code_403_response()

    def tearDown(self):
        self.patcher.stop()

    def test_error_https_status_code_200(self):
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.assert_https_status_code_200(get_sample_https_status_code_403_response(), 'Error message')
        self.assertTrue(exception_info.match('Error message'))

    def test_error_get_deployment(self):
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.get_deployment(API_GW_ID, API_GW_DEPLOYMENT_ID_V1)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployment with ApiId: {API_GW_ID} '
                                             f'and DeploymentId: {API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_deployments(self):
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.get_deployments(API_GW_ID)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployments with ApiId: {API_GW_ID} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_stage(self):
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.get_stage(API_GW_ID, API_GW_STAGE_NAME)
        self.assertTrue(exception_info.match(f'Failed to perform get_stage with ApiId: {API_GW_ID} '
                                             f'and StageName: {API_GW_STAGE_NAME} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_update_deployment(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match(f'Failed to perform update_stage with ApiId: {API_GW_ID}, '
                                             f'StageName: {API_GW_STAGE_NAME} and '
                                             f'DeploymentId: {API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_service_quota(self):
        with pytest.raises(ValueError) as exception_info:
            apigw2_utils.get_service_quota(BOTO3_CONFIG, QUOTA_SERVICE_CODE, QUOTA_RATE_LIMIT_CODE)
        self.assertTrue(exception_info.match(f'Failed to perform get_service_quota with '
                                             f'ServiceCode: {QUOTA_SERVICE_CODE} and '
                                             f'QuotaCode: {QUOTA_RATE_LIMIT_CODE}'))


@pytest.mark.unit_test
class TestApigwv2UtilKeyExceptions(unittest.TestCase):
    def test_find_deployment_id_for_update_error_input_1(self):
        events = {'HttpWsApiGwId': API_GW_ID}

        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsStageName in events'))

    def test_find_deployment_id_for_update_error_input_2(self):
        events = {'HttpWsStageName': API_GW_STAGE_NAME}

        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsApiGwId in events'))

    def test_update_deployment_error_input_1(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsDeploymentId in events'))

    def test_update_deployment_error_input_2(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsStageName in events'))

    def test_update_deployment_error_input_3(self):
        events = {
            'HttpWsStageName': API_GW_STAGE_NAME,
            'HttpWsDeploymentId': API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsApiGwId in events'))

    def test_validate_auto_deploy_error_input_1(self):
        events = {
            'HttpWsStageName': API_GW_STAGE_NAME,
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_auto_deploy(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsApiGwId in events'))

    def test_validate_auto_deploy_error_input_2(self):
        events = {
            'HttpWsApiGwId': API_GW_ID,
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_auto_deploy(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsStageName in events'))

    def test_set_throttling_config_error_input_1(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsApiGwId in events'))

    def test_set_throttling_config_error_input_2(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsThrottlingBurst in events'))

    def test_set_throttling_config_error_input_3(self):
        events = {
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsThrottlingRate in events'))

    def test_set_throttling_config_error_input_4(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsStageName in events'))

    def test_validate_throttling_config_error_input_1(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsApiGwId in events'))

    def test_validate_throttling_config_error_input_2(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsThrottlingBurst in events'))

    def test_validate_throttling_config_error_input_3(self):
        events = {
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsApiGwId': API_GW_ID,
            'HttpWsStageName': API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsThrottlingRate in events'))

    def test_validate_throttling_config_error_input_4(self):
        events = {
            'HttpWsThrottlingRate': QUOTA_RATE_LIMIT,
            'HttpWsThrottlingBurst': QUOTA_BURST_LIMIT,
            'HttpWsApiGwId': API_GW_ID
        }
        with pytest.raises(KeyError) as exception_info:
            apigw2_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires HttpWsStageName in events'))
