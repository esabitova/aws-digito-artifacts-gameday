import unittest
import pytest
from test import test_data_provider
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import MagicMock
from src import route_through_appliance


@pytest.mark.unit_test
class TestSsmExecutionUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_route_tables.return_value = test_data_provider.get_sample_route_table_response()

    def tearDown(self):
        self.patcher.stop()

    def test_get_existing_routes_success(self):
        events = {}
        events['ApplicationSubnetIds'] = test_data_provider.APPLICATION_SUBNET_ID

        existing_routes = route_through_appliance.get_existing_routes(events, None)
        self.assertIsNotNone(existing_routes['ExistingRouteTableResponse'])

    def test_route_through_appliance(self):
        get_existing_routes_events = {}
        get_existing_routes_events['ApplicationSubnetIds'] = test_data_provider.APPLICATION_SUBNET_ID

        events = {}
        events['ExistingRouteTableResponse'] = route_through_appliance.get_existing_routes(
            get_existing_routes_events, None)['ExistingRouteTableResponse']
        events['ApplianceInstanceId'] = test_data_provider.INSTANCE_ID

        route_through_appliance.route_through_appliance(events, None)

        self.assertEqual(2, self.mock_ec2.replace_route.call_count)

        self.mock_ec2.replace_route.assert_called_with(
            DestinationCidrBlock=route_through_appliance.INTERNET_DESTINATION,
            InstanceId=test_data_provider.INSTANCE_ID,
            RouteTableId=test_data_provider.ROUTE_TABLE_ID)

    def test_cleanup_to_previous_route(self):
        get_existing_routes_events = {}
        get_existing_routes_events['ApplicationSubnetIds'] = test_data_provider.APPLICATION_SUBNET_ID

        events = {}
        events['ExistingRouteTableResponse'] = route_through_appliance.get_existing_routes(
            get_existing_routes_events, None)['ExistingRouteTableResponse']

        route_through_appliance.cleanup_to_previous_route(events, None)
        self.assertEqual(2, self.mock_ec2.replace_route.call_count)

        expected_calls = [call(DestinationCidrBlock=route_through_appliance.INTERNET_DESTINATION,
                               NatGatewayId=test_data_provider.NAT_GATEWAY_ID, RouteTableId='rtb-12345'),
                          call(DestinationCidrBlock=test_data_provider.INTERNET_DESTINATION,
                               GatewayId=test_data_provider.IGW_ID, RouteTableId=test_data_provider.ROUTE_TABLE_ID)]
        self.assertEqual(expected_calls, self.mock_ec2.replace_route.call_args_list)
