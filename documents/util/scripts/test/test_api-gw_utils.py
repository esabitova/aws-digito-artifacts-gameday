import datetime
import json
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from dateutil.tz import tzlocal

import documents.util.scripts.src.apigw_utils as apigw_utils
from documents.util.scripts.test.mock_sleep import MockSleep

BOTO3_CONFIG: object = Config(retries={'max_attempts': 20, 'mode': 'standard'})

USAGE_PLAN_ID: str = "jvgy9s"
USAGE_PLAN_QUOTA_LIMIT = 50000
USAGE_PLAN_QUOTA_PERIOD: str = "WEEK"
NEW_USAGE_PLAN_QUOTA_LIMIT = 30000
NEW_HUGECHANGE_USAGE_PLAN_LIMIT = 5000
NEW_USAGE_PLAN_QUOTA_PERIOD: str = "WEEK"

REST_API_GW_ID: str = "0djifyccl6"
REST_API_GW_STAGE_NAME: str = "DummyStage"
REST_API_GW_DEPLOYMENT_ID_V1: str = "j4ujo3"
REST_API_GW_DEPLOYMENT_ID_V2: str = "m2uen1"
REST_API_GW_DEPLOYMENT_CREATED_DATE_V1: datetime = datetime.datetime(2021, 4, 21, 18, 8, 10, tzinfo=tzlocal())
REST_API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 7, 10, tzinfo=tzlocal())
REST_API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1: datetime = datetime.datetime(2021, 4, 21, 18, 9, 10, tzinfo=tzlocal())

QUOTA_SERVICE_CODE: str = 'apigateway'
QUOTA_RATE_LIMIT: float = 10000.0
QUOTA_RATE_LIMIT_CODE: str = 'L-8A5B8E43'
QUOTA_BURST_LIMIT: float = 5000.0
QUOTA_BURST_LIMIT_CODE: str = 'L-CDF5615A'

USAGE_PLAN_THROTTLE_RATE_LIMIT: float = 100.0
USAGE_PLAN_STAGE_THROTTLE_RATE_LIMIT: float = 90.0
NEW_THROTTLE_RATE_LIMIT: float = 80.0
LESS_THROTTLE_RATE_LIMIT: float = 49.0
MORE_THROTTLE_RATE_LIMIT: float = 151.0
HUGE_THROTTLE_RATE_LIMIT: float = 11000.0

USAGE_PLAN_THROTTLE_BURST_LIMIT: int = 100
USAGE_PLAN_STAGE_THROTTLE_BURST_LIMIT: int = 90
NEW_THROTTLE_BURST_LIMIT: int = 80
LESS_THROTTLE_BURST_LIMIT: int = 49
MORE_THROTTLE_BURST_LIMIT: int = 151
HUGE_THROTTLE_BURST_LIMIT: int = 6000

VPC_ID = 'vpc-05b0d23b42d9d9c5d'
VPC_ENDPOINT_ID = 'vpce-0720374816acdd7f9'
VPC_ENDPOINT_IDS = [VPC_ENDPOINT_ID]
ORIGINAL_SECURITY_GROUP_ID = 'sg-0421e6a37e188fd3f'
ORIGINAL_SECURITY_GROUP_NAME = 'ApiGatewayVpcEndpoint'
DUMMY_SECURITY_GROUP_ID = 'sg-0421e6a37e186ae1d'
DUMMY_SECURITY_GROUP_NAME = 'dummy-sg-' + VPC_ENDPOINT_ID
DUMMY_SECURITY_GROUPS = [{"GroupId": DUMMY_SECURITY_GROUP_ID,
                          "GroupName": DUMMY_SECURITY_GROUP_NAME}]

VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING = {
    VPC_ENDPOINT_ID: [{"GroupId": ORIGINAL_SECURITY_GROUP_ID,
                       "GroupName": ORIGINAL_SECURITY_GROUP_NAME}]
}


def get_sample_https_status_code_403_response():
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 403
        }
    }


def get_sample_get_usage_plan_response(
        throttle_burst_limit=USAGE_PLAN_THROTTLE_BURST_LIMIT,
        throttle_rate_limit=USAGE_PLAN_THROTTLE_RATE_LIMIT,
        stage_throttle_burst_limit=USAGE_PLAN_STAGE_THROTTLE_BURST_LIMIT,
        stage_throttle_rate_limit=USAGE_PLAN_STAGE_THROTTLE_RATE_LIMIT,
        quota_limit=USAGE_PLAN_QUOTA_LIMIT,
        quota_period=USAGE_PLAN_QUOTA_PERIOD):
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "quota": {
            "limit": quota_limit,
            "period": quota_period
        },
        "throttle": {
            "burstLimit": throttle_burst_limit,
            "rateLimit": throttle_rate_limit
        },
        "apiStages": [
            {
                "apiId": REST_API_GW_ID,
                "stage": REST_API_GW_STAGE_NAME,
                "throttle": {
                    "*/*": {
                        "burstLimit": stage_throttle_burst_limit,
                        "rateLimit": stage_throttle_rate_limit
                    }
                }
            }
        ]
    }


def get_sample_update_usage_plan_response():
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "quota": {
            "limit": NEW_USAGE_PLAN_QUOTA_LIMIT,
            "period": NEW_USAGE_PLAN_QUOTA_PERIOD
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


def get_sample_get_stage_response():
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "deploymentId": REST_API_GW_DEPLOYMENT_ID_V1,
        "stageName": REST_API_GW_STAGE_NAME
    }


def get_sample_update_stage_response():
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "deploymentId": REST_API_GW_DEPLOYMENT_ID_V2,
        "stageName": REST_API_GW_STAGE_NAME
    }


def get_sample_get_deployment_response(deployment_id, created_date):
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        "id": deployment_id,
        "createdDate": created_date
    }


def get_sample_get_deployments_response_with_1_deployment():
    return {
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


def get_sample_get_deployments_response_with_2_deployments():
    return {
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


def get_sample_get_deployments_response_with_6_deployments():
    return {
        "ResponseMetadata": {"HTTPStatusCode": 200},
        "items": [
            {
                'id': 'zpju28',
                'description': 'Dummy deployment 6',
                'createdDate': datetime.datetime(
                    2021, 4, 21, 18, 11, 10, tzinfo=tzlocal()
                )
            },
            {
                'id': 'zo5n6k',
                'description': 'Dummy deployment 5',
                'createdDate': datetime.datetime(
                    2021, 4, 21, 18, 10, 10, tzinfo=tzlocal()
                )
            },
            {
                'id': 'zk1f7c',
                'description': 'Dummy deployment 4',
                'createdDate': datetime.datetime(
                    2021, 4, 21, 18, 9, 10, tzinfo=tzlocal()
                )
            },
            {
                'id': REST_API_GW_DEPLOYMENT_ID_V1,
                'description': 'Dummy deployment 3',
                'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_V1,
            },
            {
                'id': REST_API_GW_DEPLOYMENT_ID_V2,
                'description': 'Dummy deployment 2',
                'createdDate': REST_API_GW_DEPLOYMENT_CREATED_DATE_LESS_THAN_V1,
            },
            {
                'id': 'xfjve2',
                'description': 'Dummy deployment 1',
                'createdDate': datetime.datetime(
                    2021, 4, 21, 18, 6, 10, tzinfo=tzlocal()
                )
            },
        ],
    }


def get_sample_get_service_quota_response(quota_code: str, limit: float):
    return {
        "ResponseMetadata": {
            "HTTPStatusCode": 200
        },
        'Quota': {
            'ServiceCode': QUOTA_SERVICE_CODE,
            'QuotaCode': quota_code,
            'Value': limit
        }
    }


def get_sample_get_service_quota_response_side_effect():
    return [get_sample_get_service_quota_response(QUOTA_RATE_LIMIT_CODE, QUOTA_RATE_LIMIT),
            get_sample_get_service_quota_response(QUOTA_BURST_LIMIT_CODE, QUOTA_BURST_LIMIT)]


def get_sample_get_rest_api_response(vps_endpoint_ids):
    return {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
        },
        'id': REST_API_GW_ID,
        'endpointConfiguration': {
            'types': ['PRIVATE'],
            'vpcEndpointIds': vps_endpoint_ids
        }
    }


def get_sample_describe_vpc_endpoints_response():
    return {
        'ResponseMetadata': {
            'HTTPStatusCode': 200,
        },
        'VpcEndpoints': [
            {
                'VpcEndpointId': VPC_ENDPOINT_ID,
                'VpcId': VPC_ID,
                'Groups': [
                    {
                        'GroupId': ORIGINAL_SECURITY_GROUP_ID,
                        'GroupName': ORIGINAL_SECURITY_GROUP_NAME
                    }
                ]
            }
        ]
    }


def get_sample_describe_security_groups_response(security_groups):
    return {
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        },
        'SecurityGroups': security_groups
    }


def get_sample_create_security_group_response():
    return {
        'GroupId': DUMMY_SECURITY_GROUP_ID,
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        }
    }


def get_sample_modify_vpc_endpoint_response(return_value):
    return {
        'Return': return_value,
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        }
    }


@pytest.mark.unit_test
class TestApigwUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigw = MagicMock()
        self.mock_service_quotas = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'apigateway': self.mock_apigw,
            'service-quotas': self.mock_service_quotas,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigw.get_usage_plan.return_value = get_sample_get_usage_plan_response()
        self.mock_apigw.update_usage_plan.return_value = get_sample_update_usage_plan_response()
        self.mock_apigw.get_stage.return_value = get_sample_get_stage_response()
        self.mock_apigw.update_stage.return_value = get_sample_update_stage_response()
        self.mock_ec2.describe_vpc_endpoints.return_value = get_sample_describe_vpc_endpoints_response()

    def tearDown(self):
        self.patcher.stop()

    def test_check_limit_and_period(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }

        output = apigw_utils.check_limit_and_period(events, None)
        self.assertIsNotNone(output)
        self.assertEqual("ok", output['Result'])

    @patch('time.sleep')
    def test_set_limit_and_period(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        self.mock_apigw.get_usage_plan.side_effect = [
            get_sample_get_usage_plan_response(quota_limit=USAGE_PLAN_QUOTA_LIMIT,
                                               quota_period=USAGE_PLAN_QUOTA_PERIOD),
            get_sample_get_usage_plan_response(quota_limit=NEW_USAGE_PLAN_QUOTA_LIMIT,
                                               quota_period=NEW_USAGE_PLAN_QUOTA_PERIOD),
        ]
        output = apigw_utils.set_limit_and_period(events, None)
        self.assertIsNotNone(output)
        self.assertEqual(NEW_USAGE_PLAN_QUOTA_LIMIT, output['Limit'])
        self.assertEqual(NEW_USAGE_PLAN_QUOTA_PERIOD, output['Period'])

    @patch('time.sleep')
    def test_wait_limit_and_period_updated_timeout(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD,
            'MaxRetries': 3
        }
        with pytest.raises(TimeoutError) as exception_info:
            apigw_utils.wait_limit_and_period_updated(events, None)
        self.assertTrue(exception_info.match('.*'))

    def test_get_deployment(self):
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V2, REST_API_GW_DEPLOYMENT_CREATED_DATE_MORE_THAN_V1
        )
        output = apigw_utils.get_deployment(BOTO3_CONFIG, REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V2)
        self.mock_apigw.get_deployment.assert_called_with(
            restApiId=REST_API_GW_ID,
            deploymentId=REST_API_GW_DEPLOYMENT_ID_V2
        )
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['id'])

    def test_get_deployments(self):
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()
        output = apigw_utils.get_deployments(BOTO3_CONFIG, REST_API_GW_ID)
        self.mock_apigw.get_deployments.assert_called_with(
            restApiId=REST_API_GW_ID,
            limit=25
        )
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['items'][0]['id'])

    def test_get_stage(self):
        output = apigw_utils.get_stage(BOTO3_CONFIG, REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.mock_apigw.get_stage.assert_called_with(
            restApiId=REST_API_GW_ID,
            stageName=REST_API_GW_STAGE_NAME
        )
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['deploymentId'])

    def test_find_deployment_id_for_update_with_provided_id(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V2
        }
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V2, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw_utils.find_deployment_id_for_update(events, None)
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_with_provided_deployment_id_same_as_current(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Provided deployment ID and current deployment ID should not be the same'))

    def test_find_deployment_id_for_update_without_provided_id(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME
        }
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_6_deployments()
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V1, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        output = apigw_utils.find_deployment_id_for_update(events, None)
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdToApply'])
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V1, output['OriginalDeploymentId'])

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_available_deployments(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME
        }
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_1_deployment()

        with pytest.raises(ValueError) as exception_info:
            apigw_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'There are no deployments found to apply in RestApiGateway ID: '
                                             f'{REST_API_GW_ID}, except current deployment ID: '
                                             f'{REST_API_GW_DEPLOYMENT_ID_V1}'))

    def test_find_deployment_id_for_update_without_provided_deployment_id_and_without_previous_deployments(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME
        }
        self.mock_apigw.get_deployments.return_value = get_sample_get_deployments_response_with_2_deployments()
        self.mock_apigw.get_deployment.return_value = get_sample_get_deployment_response(
            REST_API_GW_DEPLOYMENT_ID_V1, REST_API_GW_DEPLOYMENT_CREATED_DATE_V1
        )
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match(f'Could not find any existing deployment which has createdDate less than '
                                             f'current deployment ID: {REST_API_GW_DEPLOYMENT_ID_V1}'))

    def test_update_deployment(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V2
        }
        output = apigw_utils.update_deployment(events, None)
        self.mock_apigw.update_stage.assert_called_with(
            restApiId=REST_API_GW_ID,
            stageName=REST_API_GW_STAGE_NAME,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/deploymentId',
                    'value': REST_API_GW_DEPLOYMENT_ID_V2,
                },
            ]
        )
        self.assertIsNotNone(output)
        self.assertEqual(REST_API_GW_DEPLOYMENT_ID_V2, output['DeploymentIdNewValue'])

    def test_get_service_quota(self):
        self.mock_service_quotas.get_service_quota.return_value = get_sample_get_service_quota_response(
            QUOTA_RATE_LIMIT_CODE,
            QUOTA_RATE_LIMIT
        )
        output = apigw_utils.get_service_quota(BOTO3_CONFIG, QUOTA_SERVICE_CODE, QUOTA_RATE_LIMIT_CODE)
        self.mock_service_quotas.get_service_quota.assert_called_with(
            ServiceCode=QUOTA_SERVICE_CODE,
            QuotaCode=QUOTA_RATE_LIMIT_CODE
        )
        self.assertIsNotNone(output)
        self.assertEqual(QUOTA_RATE_LIMIT, output['Quota']['Value'])

    def test_update_usage_plan(self):
        output = apigw_utils.update_usage_plan(USAGE_PLAN_ID, [])
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
        output = apigw_utils.update_usage_plan(USAGE_PLAN_ID, [])
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
            apigw_utils.update_usage_plan(USAGE_PLAN_ID, [], 5)
        self.assertTrue(exception_info.match('Failed to perform API call successfully for 5 times'))

    def test_update_usage_plan_with_unknown_exception(self):
        self.mock_apigw.update_usage_plan.side_effect = ClientError(
            error_response={"Error": {"Code": "UnknownException"}},
            operation_name='UpdateUsagePlan'
        )
        with self.assertRaises(Exception) as e:
            apigw_utils.update_usage_plan(USAGE_PLAN_ID, [])

        self.assertEqual(e.exception.response['Error']['Code'], 'UnknownException')

    def test_validate_throttling_config_without_provided_stage_name(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        output = apigw_utils.validate_throttling_config(events, None)
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['OriginalRateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['OriginalBurstLimit'])

    def test_validate_throttling_config_with_new_rate_limit_increased_more_than_50_percent(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': MORE_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_rate_limit_decreased_more_than_50_percent(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': LESS_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_burst_limit_increased_more_than_50_percent(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': MORE_THROTTLE_BURST_LIMIT
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Burst rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    def test_validate_throttling_config_with_new_burst_limit_decreased_more_than_50_percent(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': LESS_THROTTLE_BURST_LIMIT
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Burst rate limit is going to be changed more than 50%, please use smaller'
                                             ' increments or use ForceExecution parameter to disable validation'))

    @patch('time.sleep')
    def test_set_throttling_config_with_provided_stage_name(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        self.mock_apigw.get_usage_plan.side_effect = [
            get_sample_get_usage_plan_response(stage_throttle_burst_limit=USAGE_PLAN_THROTTLE_BURST_LIMIT,
                                               stage_throttle_rate_limit=USAGE_PLAN_THROTTLE_RATE_LIMIT),
            get_sample_get_usage_plan_response(stage_throttle_burst_limit=NEW_THROTTLE_BURST_LIMIT,
                                               stage_throttle_rate_limit=NEW_THROTTLE_RATE_LIMIT),
        ]
        output = apigw_utils.set_throttling_config(events, None)
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

    @patch('time.sleep')
    def test_set_throttling_config_without_provided_stage_name(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        self.mock_apigw.get_usage_plan.side_effect = [
            get_sample_get_usage_plan_response(throttle_burst_limit=USAGE_PLAN_THROTTLE_BURST_LIMIT,
                                               throttle_rate_limit=USAGE_PLAN_THROTTLE_RATE_LIMIT),
            get_sample_get_usage_plan_response(throttle_burst_limit=NEW_THROTTLE_BURST_LIMIT,
                                               throttle_rate_limit=NEW_THROTTLE_RATE_LIMIT),
        ]
        output = apigw_utils.set_throttling_config(events, None)
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

    @patch('time.sleep')
    def test_set_throttling_config_without_provided_stage_name_for_rollback_case(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT,
            'RestApiGwStageName': '{{ GetInputsFromPreviousExecution.RestApiGwStageName }}',
            'RestApiGwId': '{{ GetInputsFromPreviousExecution.RestApiGwId }}',
            'RestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'RestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        self.mock_apigw.get_usage_plan.side_effect = [
            get_sample_get_usage_plan_response(throttle_burst_limit=USAGE_PLAN_THROTTLE_BURST_LIMIT,
                                               throttle_rate_limit=USAGE_PLAN_THROTTLE_RATE_LIMIT),
            get_sample_get_usage_plan_response(throttle_burst_limit=NEW_THROTTLE_BURST_LIMIT,
                                               throttle_rate_limit=NEW_THROTTLE_RATE_LIMIT),
        ]
        output = apigw_utils.set_throttling_config(events, None)
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

    def test_set_throttling_config_with_huge_rate_limit(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': HUGE_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match(f'Given value of RestApiGwThrottlingRate: {HUGE_THROTTLE_RATE_LIMIT}, '
                                             f'can not be more than service quota Throttle rate: {QUOTA_RATE_LIMIT}'))

    def test_set_throttling_config_with_huge_burst_limit(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': HUGE_THROTTLE_BURST_LIMIT
        }
        self.mock_service_quotas.get_service_quota.side_effect = get_sample_get_service_quota_response_side_effect()
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match(f'Given value of RestApiGwThrottlingBurst: {HUGE_THROTTLE_BURST_LIMIT}, '
                                             f'can not be more than service quota Throttle burst rate: '
                                             f'{QUOTA_BURST_LIMIT}'))

    @patch('time.sleep')
    def test_wait_throttling_config_updated_timeout(self, patched_sleep):
        mock_sleep = MockSleep()
        patched_sleep.side_effect = mock_sleep.sleep
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': NEW_THROTTLE_RATE_LIMIT,
            'RestApiGwThrottlingBurst': NEW_THROTTLE_BURST_LIMIT
        }
        with pytest.raises(TimeoutError) as exception_info:
            apigw_utils.wait_throttling_config_updated(events, None)
        self.assertTrue(exception_info.match('.*'))

    def test_get_throttling_config_with_provided_stage_name(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID
        }
        output = apigw_utils.get_throttling_config(events, None)
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_STAGE_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_STAGE_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_get_throttling_config_without_provided_stage_name(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID
        }
        output = apigw_utils.get_throttling_config(events, None)
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_get_throttling_config_with_provided_wrong_stage_name(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': 'WrongStageName',
            'RestApiGwId': REST_API_GW_ID
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.get_throttling_config(events, None)
        self.assertTrue(exception_info.match('Stage name WrongStageName not found in get_usage_plan'))

    def test_get_throttling_config_with_provided_stage_name_and_unknown_resource_path(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwResourcePath': 'UnknownResourcePath'
        }
        output = apigw_utils.get_throttling_config(events, None)
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_get_throttling_config_with_provided_stage_name_and_unknown_http_method(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwHttpMethod': 'GET'
        }
        output = apigw_utils.get_throttling_config(events, None)
        self.mock_apigw.get_usage_plan.assert_called_with(usagePlanId=USAGE_PLAN_ID)
        self.assertIsNotNone(output)
        self.assertEqual(USAGE_PLAN_THROTTLE_RATE_LIMIT, output['RateLimit'])
        self.assertEqual(USAGE_PLAN_THROTTLE_BURST_LIMIT, output['BurstLimit'])

    def test_assert_inputs_before_throttling_rollback(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': '',
            'RestApiGwId': '',
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': '{{ GetInputsFromPreviousExecution.RestApiGwStageName }}',
            'OriginalRestApiGwId': '{{ GetInputsFromPreviousExecution.RestApiGwId }}',
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        apigw_utils.assert_inputs_before_throttling_rollback(events, None)

    def test_assert_inputs_before_throttling_rollback_with_provided_stage_name(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': REST_API_GW_STAGE_NAME,
            'OriginalRestApiGwId': REST_API_GW_ID,
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        apigw_utils.assert_inputs_before_throttling_rollback(events, None)

    def test_get_endpoint_security_group_config_without_provided_security_group_ids(self):
        events = {'RestApiGwId': REST_API_GW_ID}
        self.mock_apigw.get_rest_api.return_value = get_sample_get_rest_api_response([VPC_ENDPOINT_ID])
        self.mock_ec2.describe_vpc_endpoints.return_value = get_sample_describe_vpc_endpoints_response()
        output = apigw_utils.get_endpoint_security_group_config(events, None)
        self.assertEqual(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING,
                         json.loads(output['VpcEndpointsSecurityGroupsMappingOriginalValue']))

    def test_get_endpoint_security_group_config_with_provided_security_group_ids(self):
        events = {'RestApiGwId': REST_API_GW_ID,
                  'SecurityGroupIdListToUnassign': [ORIGINAL_SECURITY_GROUP_ID]}
        self.mock_apigw.get_rest_api.return_value = get_sample_get_rest_api_response([VPC_ENDPOINT_ID])
        output = apigw_utils.get_endpoint_security_group_config(events, None)
        self.assertEqual(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING,
                         json.loads(output['VpcEndpointsSecurityGroupsMappingOriginalValue']))

    def test_get_endpoint_security_group_config_with_provided_wrong_security_group_ids(self):
        events = {'RestApiGwId': REST_API_GW_ID,
                  'SecurityGroupIdListToUnassign': ['wrong-security_group-id']}
        self.mock_apigw.get_rest_api.return_value = get_sample_get_rest_api_response([VPC_ENDPOINT_ID])
        with pytest.raises(Exception) as exception_info:
            apigw_utils.get_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Provided security groups were not found in any configured VPC endpoint'))

    def test_get_endpoint_security_group_config_when_apigw_has_no_configured_endpoints(self):
        events = {'RestApiGwId': REST_API_GW_ID}
        self.mock_apigw.get_rest_api.return_value = get_sample_get_rest_api_response([])
        with pytest.raises(Exception) as exception_info:
            apigw_utils.get_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Provided REST API gateway does not have any configured VPC endpoint'))

    def test_update_endpoint_security_group_config_replace_with_dummy_sg(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'ReplaceWithDummySg'
        }
        self.mock_ec2.describe_security_groups.return_value = get_sample_describe_security_groups_response([])
        self.mock_ec2.create_security_group.return_value = get_sample_create_security_group_response()
        self.mock_ec2.modify_vpc_endpoint.return_value = get_sample_modify_vpc_endpoint_response(True)
        apigw_utils.update_endpoint_security_group_config(events, None)

        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[{'Name': 'group-name',
                      'Values': [DUMMY_SECURITY_GROUP_NAME]}]
        )
        self.mock_ec2.describe_vpc_endpoints.assert_called_with(
            VpcEndpointIds=[VPC_ENDPOINT_ID]
        )
        self.mock_ec2.create_security_group.assert_called_with(
            Description='Dummy SG',
            GroupName=DUMMY_SECURITY_GROUP_NAME,
            TagSpecifications=[{'ResourceType': 'security-group',
                                'Tags': [{'Key': 'Digito',
                                          'Value': 'api-gw:test:simulate_network_unavailable'}]
                                }],
            VpcId=VPC_ID
        )
        self.mock_ec2.modify_vpc_endpoint.assert_called_with(
            VpcEndpointId=VPC_ENDPOINT_ID,
            AddSecurityGroupIds=[DUMMY_SECURITY_GROUP_ID],
            RemoveSecurityGroupIds=[ORIGINAL_SECURITY_GROUP_ID]
        )

    def test_update_endpoint_security_group_config_replace_with_dummy_sg_when_dummy_sg_already_exists(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'ReplaceWithDummySg'
        }
        self.mock_ec2.describe_security_groups.return_value = get_sample_describe_security_groups_response(
            [{'GroupId': DUMMY_SECURITY_GROUP_ID}]
        )
        self.mock_ec2.create_security_group.return_value = get_sample_create_security_group_response()
        self.mock_ec2.modify_vpc_endpoint.return_value = get_sample_modify_vpc_endpoint_response(True)
        apigw_utils.update_endpoint_security_group_config(events, None)

        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[{'Name': 'group-name', 'Values': [DUMMY_SECURITY_GROUP_NAME]}]
        )
        self.mock_ec2.describe_vpc_endpoints.assert_not_called()
        self.mock_ec2.create_security_group.assert_not_called()
        self.mock_ec2.modify_vpc_endpoint.assert_called_with(
            VpcEndpointId=VPC_ENDPOINT_ID,
            AddSecurityGroupIds=[DUMMY_SECURITY_GROUP_ID],
            RemoveSecurityGroupIds=[ORIGINAL_SECURITY_GROUP_ID]
        )

    def test_update_endpoint_security_group_config_replace_with_original_sg(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'ReplaceWithOriginalSg'
        }
        self.mock_ec2.describe_security_groups.return_value = get_sample_describe_security_groups_response(
            [{'GroupId': DUMMY_SECURITY_GROUP_ID}]
        )
        self.mock_ec2.modify_vpc_endpoint.return_value = get_sample_modify_vpc_endpoint_response(True)
        apigw_utils.update_endpoint_security_group_config(events, None)

        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[{'Name': 'group-name',
                      'Values': [DUMMY_SECURITY_GROUP_NAME]}]
        )
        self.mock_ec2.modify_vpc_endpoint.assert_called_with(
            VpcEndpointId=VPC_ENDPOINT_ID,
            AddSecurityGroupIds=[ORIGINAL_SECURITY_GROUP_ID],
            RemoveSecurityGroupIds=[DUMMY_SECURITY_GROUP_ID]
        )
        self.mock_ec2.delete_security_group.assert_called_with(GroupId=DUMMY_SECURITY_GROUP_ID)

    def test_update_endpoint_security_group_config_replace_with_original_sg_when_dummy_sg_not_present(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'ReplaceWithOriginalSg'
        }
        self.mock_ec2.describe_security_groups.return_value = get_sample_describe_security_groups_response([])
        self.mock_ec2.modify_vpc_endpoint.return_value = get_sample_modify_vpc_endpoint_response(True)

        apigw_utils.update_endpoint_security_group_config(events, None)

        self.mock_ec2.describe_security_groups.assert_called_with(
            Filters=[{'Name': 'group-name',
                      'Values': [DUMMY_SECURITY_GROUP_NAME]}]
        )
        self.mock_ec2.modify_vpc_endpoint.assert_called_with(
            VpcEndpointId=VPC_ENDPOINT_ID,
            AddSecurityGroupIds=[ORIGINAL_SECURITY_GROUP_ID],
            RemoveSecurityGroupIds=[]
        )
        self.mock_ec2.delete_security_group.assert_not_called()

    def test_update_endpoint_security_group_config_replace_with_original_sg_failed_modify_vpc_endpoint_responses(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'ReplaceWithOriginalSg'
        }
        self.mock_ec2.modify_vpc_endpoint.return_value = get_sample_modify_vpc_endpoint_response(False)
        self.mock_ec2.describe_security_groups.return_value = get_sample_describe_security_groups_response(
            [{'GroupId': DUMMY_SECURITY_GROUP_ID}]
        )
        with pytest.raises(Exception) as exception_info:
            apigw_utils.update_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Could not modify VPC endpoint'))


@pytest.mark.unit_test
class TestApigwUtilValueExceptions(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_apigw = MagicMock()
        self.mock_service_quotas = MagicMock()
        self.side_effect_map = {
            'apigateway': self.mock_apigw,
            'service-quotas': self.mock_service_quotas
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_apigw.get_usage_plan.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.update_usage_plan.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_deployment.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_deployments.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.get_stage.return_value = get_sample_https_status_code_403_response()
        self.mock_apigw.update_stage.return_value = get_sample_https_status_code_403_response()
        self.mock_service_quotas.get_service_quota.return_value = get_sample_https_status_code_403_response()

    def tearDown(self):
        self.patcher.stop()

    def test_error_check_limit_and_period(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to get usage plan limit and period'))

    def test_error_set_limit_and_period(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to update usage plan limit and period'))

    def test_error_https_status_code_200(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.assert_https_status_code_200(get_sample_https_status_code_403_response(), 'Error message')
        self.assertTrue(exception_info.match('Error message'))

    def test_error_get_deployment(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.get_deployment(BOTO3_CONFIG, REST_API_GW_ID, REST_API_GW_DEPLOYMENT_ID_V1)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployment with restApiId: {REST_API_GW_ID} '
                                             f'and deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_deployments(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.get_deployments(BOTO3_CONFIG, REST_API_GW_ID)
        self.assertTrue(exception_info.match(f'Failed to perform get_deployments with restApiId: {REST_API_GW_ID} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_stage(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.get_stage(BOTO3_CONFIG, REST_API_GW_ID, REST_API_GW_STAGE_NAME)
        self.assertTrue(exception_info.match(f'Failed to perform get_stage with restApiId: {REST_API_GW_ID} '
                                             f'and stageName: {REST_API_GW_STAGE_NAME} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_update_deployment(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match(f'Failed to perform update_stage with restApiId: {REST_API_GW_ID}, '
                                             f'stageName: {REST_API_GW_STAGE_NAME} and '
                                             f'deploymentId: {REST_API_GW_DEPLOYMENT_ID_V1} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_get_service_quota(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.get_service_quota(BOTO3_CONFIG, QUOTA_SERVICE_CODE, QUOTA_RATE_LIMIT_CODE)
        self.assertTrue(exception_info.match(f'Failed to perform get_service_quota with '
                                             f'ServiceCode: {QUOTA_SERVICE_CODE} and '
                                             f'QuotaCode: {QUOTA_RATE_LIMIT_CODE}'))

    def test_error_get_throttling_config(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME,
        }
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.get_throttling_config(events, None)
        self.assertTrue(exception_info.match(f'Failed to get usage plan with id {USAGE_PLAN_ID} '
                                             f'Response is: {get_sample_https_status_code_403_response()}'))

    def test_error_update_usage_plan(self):
        with pytest.raises(ValueError) as exception_info:
            apigw_utils.update_usage_plan(USAGE_PLAN_ID, [])
        self.assertTrue(exception_info.match('Failed to perform API call'))


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
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_HUGECHANGE_USAGE_PLAN_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }

        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('.*'))


@pytest.mark.unit_test
class TestApigwUtilKeyExceptions(unittest.TestCase):
    def test_check_limit_and_period_error_input_1(self):
        events = {
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_check_limit_and_period_error_input_2(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_check_limit_and_period_error_input_3(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))

    def test_set_limit_and_period_error_input_1(self):
        events = {
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_set_limit_and_period_error_input_2(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaPeriod': NEW_USAGE_PLAN_QUOTA_PERIOD
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_set_limit_and_period_error_input_3(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwQuotaLimit': NEW_USAGE_PLAN_QUOTA_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))

    def test_find_deployment_id_for_update_error_input_1(self):
        events = {'RestApiGwId': REST_API_GW_ID}

        with pytest.raises(KeyError) as exception_info:
            apigw_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires RestStageName in events'))

    def test_find_deployment_id_for_update_error_input_2(self):
        events = {'RestStageName': REST_API_GW_STAGE_NAME}

        with pytest.raises(KeyError) as exception_info:
            apigw_utils.find_deployment_id_for_update(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_update_deployment_error_input_1(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestStageName': REST_API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestDeploymentId in events'))

    def test_update_deployment_error_input_2(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestStageName in events'))

    def test_update_deployment_error_input_3(self):
        events = {
            'RestStageName': REST_API_GW_STAGE_NAME,
            'RestDeploymentId': REST_API_GW_DEPLOYMENT_ID_V1
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.update_deployment(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_set_throttling_config_error_input_1(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_set_throttling_config_error_input_2(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': ''
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('RestApiGwId should not be empty'))

    def test_set_throttling_config_error_input_3(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId in events'))

    def test_set_throttling_config_error_input_4(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingRate in events'))

    def test_set_throttling_config_error_input_5(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.set_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingBurst in events'))

    def test_validate_throttling_config_error_input_1(self):
        events = {
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingRate in events'))

    def test_validate_throttling_config_error_input_2(self):
        events = {
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingBurst in events'))

    def test_validate_throttling_config_error_input_3(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId in events'))

    def test_validate_throttling_config_error_input_4(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingBurst': QUOTA_BURST_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingRate in events'))

    def test_validate_throttling_config_error_input_5(self):
        events = {
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwThrottlingRate': QUOTA_RATE_LIMIT
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.validate_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwThrottlingBurst in events'))

    def test_get_throttling_config_error_input_1(self):
        events = {}
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.get_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId in events'))

    def test_get_throttling_config_error_input_2(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.get_throttling_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_get_throttling_config_error_input_3(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': ''
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.get_throttling_config(events, None)
        self.assertTrue(exception_info.match('RestApiGwId should not be empty'))

    def test_assert_inputs_before_throttling_rollback_error_input_1(self):
        events = {
            'RestApiGwUsagePlanId': 'WrongRestApiGwUsagePlanId',
            'RestApiGwStageName': '',
            'RestApiGwId': '',
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': '{{ GetInputsFromPreviousExecution.RestApiGwStageName }}',
            'OriginalRestApiGwId': '{{ GetInputsFromPreviousExecution.RestApiGwId }}',
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.assert_inputs_before_throttling_rollback(events, None)
        self.assertTrue(exception_info.match(f'Provided RestApiGwUsagePlanId: WrongRestApiGwUsagePlanId is not equal to'
                                             f' original RestApiGwUsagePlanId: {USAGE_PLAN_ID}'))

    def test_assert_inputs_before_throttling_rollback_error_input_2(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': 'WrongRestApiGwStageName',
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': REST_API_GW_STAGE_NAME,
            'OriginalRestApiGwId': REST_API_GW_ID,
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.assert_inputs_before_throttling_rollback(events, None)
        self.assertTrue(exception_info.match(f'Provided RestApiGwStageName: WrongRestApiGwStageName is not equal to '
                                             f'original RestApiGwStageName: {REST_API_GW_STAGE_NAME}'))

    def test_assert_inputs_before_throttling_rollback_error_input_3(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': 'WrongRestApiGwId',
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': REST_API_GW_STAGE_NAME,
            'OriginalRestApiGwId': REST_API_GW_ID,
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.assert_inputs_before_throttling_rollback(events, None)
        self.assertTrue(exception_info.match(f'Provided RestApiGwId: WrongRestApiGwId is not equal to '
                                             f'original RestApiGwId: {REST_API_GW_ID}'))

    def test_assert_inputs_before_throttling_rollback_error_input_4(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwResourcePath': 'WrongRestApiGwResourcePath',
            'RestApiGwHttpMethod': '*',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': REST_API_GW_STAGE_NAME,
            'OriginalRestApiGwId': REST_API_GW_ID,
            'OriginalRestApiGwResourcePath': 'app',
            'OriginalRestApiGwHttpMethod': '{{ GetInputsFromPreviousExecution.RestApiGwHttpMethod }}'
        }
        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.assert_inputs_before_throttling_rollback(events, None)
        self.assertTrue(exception_info.match('Provided RestApiGwResourcePath: WrongRestApiGwResourcePath is not equal '
                                             'to original RestApiGwResourcePath: app'))

    def test_assert_inputs_before_throttling_rollback_error_input_5(self):
        events = {
            'RestApiGwUsagePlanId': USAGE_PLAN_ID,
            'RestApiGwStageName': REST_API_GW_STAGE_NAME,
            'RestApiGwId': REST_API_GW_ID,
            'RestApiGwResourcePath': '*',
            'RestApiGwHttpMethod': 'PUT',
            'OriginalRestApiGwUsagePlanId': USAGE_PLAN_ID,
            'OriginalRestApiGwStageName': REST_API_GW_STAGE_NAME,
            'OriginalRestApiGwId': REST_API_GW_ID,
            'OriginalRestApiGwResourcePath': '{{ GetInputsFromPreviousExecution.RestApiGwResourcePath }}',
            'OriginalRestApiGwHttpMethod': 'GET'
        }
        with pytest.raises(AssertionError) as exception_info:
            apigw_utils.assert_inputs_before_throttling_rollback(events, None)
        self.assertTrue(exception_info.match('Provided RestApiGwHttpMethod: PUT is not equal to '
                                             'original RestApiGwHttpMethod: GET'))

    def test_get_endpoint_security_group_config_error_input_1(self):
        events = {}
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.get_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwId in events'))

    def test_update_endpoint_security_group_config_error_input_1(self):
        events = {}
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.update_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Requires VpcEndpointsSecurityGroupsMapping in events'))

    def test_update_endpoint_security_group_config_error_input_2(self):
        events = {
            'VpcEndpointsSecurityGroupsMapping': json.dumps(VPC_ENDPOINTS_SECURITY_GROUPS_MAPPING),
            'Action': 'WrongAction'
        }
        with pytest.raises(KeyError) as exception_info:
            apigw_utils.update_endpoint_security_group_config(events, None)
        self.assertTrue(exception_info.match('Possible values for Action: ReplaceWithOriginalSg, ReplaceWithDummySg'))
