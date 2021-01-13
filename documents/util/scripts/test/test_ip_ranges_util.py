import unittest
import pytest
from unittest.mock import patch
from unittest.mock import MagicMock
from test import test_data_provider
from src.ip_ranges_util import get_ip_ranges


@pytest.mark.unit_test
class TestIpRangesUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('urllib3.PoolManager')
        self.http = self.patcher.start()
        self.mock_http = MagicMock()
        self.http.side_effect = self.mock_http

        self.mock_http.return_value.request.return_value = test_data_provider.get_sample_aws_ip_ranges()

    def tearDown(self):
        self.patcher.stop()

    def test_get_ip_ranges_all_input_provided_success(self):
        events = {}
        events['AwsServiceName'] = 'DYNAMODB'
        events['Region'] = 'us-west-2'
        events['DestinationIpAddressRanges'] = [test_data_provider.ADDITIONAL_IP_PREFIX_1,
                                                test_data_provider.ADDITIONAL_IP_PREFIX_2]

        output = get_ip_ranges(events, None)
        self.assertEqual(" ".join([test_data_provider.DYNAMODB_USW2_IP_PREFIX,
                                   test_data_provider.ADDITIONAL_IP_PREFIX_1,
                                   test_data_provider.ADDITIONAL_IP_PREFIX_2]),
                         output['IpAddressRanges'])

    def test_get_ip_ranges_no_input_provided_success(self):
        events = {}
        events['AwsServiceName'] = ''
        events['Region'] = 'us-west-2'
        events['DestinationIpAddressRanges'] = []

        output = get_ip_ranges(events, None)
        self.assertEqual('', output['IpAddressRanges'])
