import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from documents.util.scripts.src.apigw_util import check_limit_and_period
from documents.util.scripts.src.apigw_util import set_limit_and_period

USAGE_PLAN_ID: str = "jvgy9s"
USAGE_PLAN_LIMIT = 50000
USAGE_PLAN_PERIOD: str = "WEEK"
NEW_USAGE_PLAN_LIMIT = 50000
NEW_HUGECHANGE_USAGE_PLAN_LIMIT = 5000
NEW_USAGE_PLAN_PERIOD: str = "WEEK"


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


def get_sample_error_get_usage_plan_response():
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

    def tearDown(self):
        self.patcher.stop()

    def test_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        output = check_limit_and_period(events, None)
        self.assertEqual("ok", output['Result'])

    def test_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        output = set_limit_and_period(events, None)
        self.assertEqual(NEW_USAGE_PLAN_LIMIT, output['Limit'])
        self.assertEqual(NEW_USAGE_PLAN_PERIOD, output['Period'])

    def test_input1_check_limit_and_period(self):
        events = {}
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_input2_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_input3_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT

        with pytest.raises(KeyError) as exception_info:
            check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))

    def test_input1_set_limit_and_period(self):
        events = {}
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwUsagePlanId  in events'))

    def test_input2_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(KeyError) as exception_info:
            set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaLimit  in events'))

    def test_input3_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT

        with pytest.raises(KeyError) as exception_info:
            set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Requires RestApiGwQuotaPeriod  in events'))


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
        self.mock_apigw.get_usage_plan.return_value = get_sample_error_get_usage_plan_response()
        self.mock_apigw.update_usage_plan.return_value = get_sample_error_get_usage_plan_response()

    def tearDown(self):
        self.patcher.stop()

    def test_error_check_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(ValueError) as exception_info:
            check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to get usage plan limit and period'))

    def test_error_set_limit_and_period(self):
        events = {}
        events['RestApiGwUsagePlanId'] = USAGE_PLAN_ID
        events['RestApiGwQuotaLimit'] = NEW_USAGE_PLAN_LIMIT
        events['RestApiGwQuotaPeriod'] = NEW_USAGE_PLAN_PERIOD

        with pytest.raises(ValueError) as exception_info:
            set_limit_and_period(events, None)
        self.assertTrue(exception_info.match('Failed to update usage plan limit and period'))


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
            check_limit_and_period(events, None)
        self.assertTrue(exception_info.match('.*'))
