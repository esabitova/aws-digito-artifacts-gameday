import json
import unittest
from test import test_data_provider
from unittest.mock import MagicMock, call, patch

import pytest
from documents.util.scripts.src import route_through_appliance
from documents.util.scripts.test.test_data_provider \
    import ROUTE_TABLE_ID, NAT_GATEWAY_ID, INTERNET_DESTINATION


@pytest.mark.unit_test
class TestRouteThroughApplianceUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.mock_ec2.describe_route_tables.return_value = test_data_provider.get_sample_route_table_response()
        self.mock_ec2.delete_route.return_value = test_data_provider.get_sample_delete_route_response()
        self.mock_ec2.create_route.return_value = test_data_provider.get_sample_create_route_response()

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

    def test___get_nat_routes_filter_private_subnet_none(self):
        nat_id = 'abc'
        private_subnet_id = None

        result = route_through_appliance._get_nat_routes_filter(nat_id, private_subnet_id)

        self.assertTrue(len(result) == 1)
        self.assertDictEqual(result[0], {'Name': 'route.nat-gateway-id', 'Values': [nat_id]})

    def test___get_nat_routes_filter_private_subnet_not_none(self):
        nat_id = NAT_GATEWAY_ID
        private_subnet_id = 'subnet-id'

        result = route_through_appliance._get_nat_routes_filter(nat_id, private_subnet_id)

        self.assertTrue(len(result) == 2)
        self.assertDictEqual(result[0], {'Name': 'route.nat-gateway-id', 'Values': [nat_id]})
        self.assertDictEqual(result[1], {'Name': 'association.subnet-id', 'Values': [private_subnet_id]})

    def test___get_nat_routes_filter_destination_ipv4_cidr_block_not_none(self):
        nat_id = NAT_GATEWAY_ID
        destination_ipv4_cidr_block = 'destination_ipv4_cidr_block'

        result = route_through_appliance._get_nat_routes_filter(
            nat_id, destination_ipv4_cidr_block=destination_ipv4_cidr_block)

        self.assertTrue(len(result) == 2)
        self.assertDictEqual(result[0], {'Name': 'route.nat-gateway-id', 'Values': [nat_id]})
        self.assertDictEqual(result[1], {'Name': 'route.destination-cidr-block',
                             'Values': [destination_ipv4_cidr_block]})

    def test__get_ipv4_routes_to_nat(self):
        self.mock_ec2.describe_route_tables.return_value = \
            test_data_provider.get_sample_route_table_response_filtered_by_nat()

        nat_id = NAT_GATEWAY_ID
        private_subnet_id = 'subnet-id'

        result = route_through_appliance._get_ipv4_routes_to_nat(self.mock_ec2,
                                                                 nat_id,
                                                                 private_subnet_id)
        self.assertTrue(len(result) == 1)
        self.assertEqual(result[0]['RouteTableId'], ROUTE_TABLE_ID)
        self.assertTrue(len(result[0]['Routes']) == 1)
        self.assertEqual(result[0]['Routes'][0]['DestinationCidrBlock'],
                         route_through_appliance.INTERNET_DESTINATION)

    @patch('documents.util.scripts.src.route_through_appliance._get_ipv4_routes_to_nat',
           return_value=[{"RouteTableId": ROUTE_TABLE_ID}])
    def test_get_nat_gw_routes(self, mock_get_routes):

        result = json.loads(route_through_appliance.get_nat_gw_routes(events={
            'NatGatewayId': NAT_GATEWAY_ID,
            'PrivateSubnetId': ''
        }, context={})['Response'])
        print(result)
        self.assertTrue(len(result) == 1)
        self.assertEqual(result[0]['RouteTableId'], ROUTE_TABLE_ID)
        mock_get_routes.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                           nat_gw_id=NAT_GATEWAY_ID,
                                           private_subnet_id='')

    def test_get_nat_gw_routes_nat_not_provided(self):
        with self.assertRaises(KeyError) as context:
            route_through_appliance.get_nat_gw_routes(events={
                'PrivateSubnetId': ''
            }, context={})

        self.assertTrue('Requires NatGatewayId' in context.exception.args)

    def test__delete_route(self):
        route_through_appliance._delete_route(boto3_ec2_client=self.mock_ec2,
                                              route_table_id=ROUTE_TABLE_ID,
                                              destination_ipv4_cidr_block=INTERNET_DESTINATION)

        self.mock_ec2.delete_route.assert_called_with(RouteTableId=ROUTE_TABLE_ID,
                                                      DestinationCidrBlock=INTERNET_DESTINATION)

    def test__create_route(self):
        route_through_appliance._create_route(boto3_ec2_client=self.mock_ec2,
                                              route_table_id=ROUTE_TABLE_ID,
                                              destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                              nat_gw_id=NAT_GATEWAY_ID)

        self.mock_ec2.create_route.assert_called_with(RouteTableId=ROUTE_TABLE_ID,
                                                      DestinationCidrBlock=INTERNET_DESTINATION,
                                                      NatGatewayId=NAT_GATEWAY_ID)

    @patch('documents.util.scripts.src.route_through_appliance._create_route',
           return_value=test_data_provider.get_sample_create_route_response())
    @patch('documents.util.scripts.src.route_through_appliance._get_ipv4_routes_to_nat',
           return_value=[{'route': 'my_route'}])
    def test__create_route_and_wait(self, route_to_nat_mock, create_route_mock):
        route_through_appliance._create_route_and_wait(boto3_ec2_client=self.mock_ec2,
                                                       route_table_id=ROUTE_TABLE_ID,
                                                       destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                                       nat_gw_id=NAT_GATEWAY_ID)

        create_route_mock.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             route_table_id=ROUTE_TABLE_ID,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                             nat_gw_id=NAT_GATEWAY_ID)

        route_to_nat_mock.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             nat_gw_id=NAT_GATEWAY_ID,
                                             private_subnet_id=None,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION)

    @patch('resource_manager.src.util.dynamo_db_utils.time.sleep',
           return_value=None)
    @patch('documents.util.scripts.src.route_through_appliance._create_route',
           return_value=test_data_provider.get_sample_create_route_response())
    @patch('documents.util.scripts.src.route_through_appliance._get_ipv4_routes_to_nat',
           side_effect=[None, {'Something': 'Something'}])
    def test__create_route_and_wait_timeout(self, route_to_nat_mock, create_route_mock, time_sleep_mock):
        with self.assertRaises(TimeoutError):
            route_through_appliance._create_route_and_wait(boto3_ec2_client=self.mock_ec2,
                                                           route_table_id=ROUTE_TABLE_ID,
                                                           destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                                           nat_gw_id=NAT_GATEWAY_ID,
                                                           wait_timeout_seconds=0)

        create_route_mock.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             route_table_id=ROUTE_TABLE_ID,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                             nat_gw_id=NAT_GATEWAY_ID)

        route_to_nat_mock.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             nat_gw_id=NAT_GATEWAY_ID,
                                             private_subnet_id=None,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION)

    @ patch('documents.util.scripts.src.route_through_appliance._delete_route')
    @ patch('documents.util.scripts.src.route_through_appliance._get_ipv4_routes_to_nat',
            return_value=[])
    def test_delete_nat_gw_routes(self, mock_get_routes, mock_delete_route):

        result = json.loads(route_through_appliance.delete_nat_gw_routes(events={
            'OriginalValue':
            f"[{{\"RouteTableId\": \"{ROUTE_TABLE_ID}\", "
            f"\"Routes\": [{{\"DestinationCidrBlock\": \"{INTERNET_DESTINATION}\"}}]}}]",
            'NatGatewayId': NAT_GATEWAY_ID,
        }, context={})['Response'])

        self.assertTrue(len(result) == 0)
        mock_delete_route.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             route_table_id=ROUTE_TABLE_ID,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION)
        mock_get_routes.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                           nat_gw_id=NAT_GATEWAY_ID,
                                           private_subnet_id=None)

    def test_delete_nat_gw_routes_nat_not_provided(self):
        with self.assertRaises(KeyError) as context:
            route_through_appliance.delete_nat_gw_routes(events={
                'PrivateSubnetId': '',
                'OriginalValue': '[]'
            }, context={})

        self.assertTrue('Requires NatGatewayId' in context.exception.args)

    def test_delete_nat_gw_routes_original_value_not_provided(self):
        with self.assertRaises(KeyError) as context:
            route_through_appliance.delete_nat_gw_routes(events={
                'NatGatewayId': NAT_GATEWAY_ID,
            }, context={})

        self.assertTrue('Requires OriginalValue' in context.exception.args)

    @ patch('documents.util.scripts.src.route_through_appliance._create_route')
    @ patch('documents.util.scripts.src.route_through_appliance._get_ipv4_routes_to_nat',
            return_value=[{"RouteTableId": ROUTE_TABLE_ID}])
    def test_create_nat_gw_routes(self, mock_get_routes, mock_create_route):

        result = json.loads(route_through_appliance.create_nat_gw_routes(events={
            'OriginalValue':
            f"[{{\"RouteTableId\": \"{ROUTE_TABLE_ID}\", "
            f"\"Routes\": [{{\"DestinationCidrBlock\": \"{INTERNET_DESTINATION}\"}}]}}]",
            'NatGatewayId': NAT_GATEWAY_ID,
        }, context={})['Response'])
        print(result)
        self.assertTrue(len(result) == 1)
        self.assertEqual(result[0]['RouteTableId'], ROUTE_TABLE_ID)
        mock_create_route.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                             route_table_id=ROUTE_TABLE_ID,
                                             destination_ipv4_cidr_block=INTERNET_DESTINATION,
                                             nat_gw_id=NAT_GATEWAY_ID)
        mock_get_routes.assert_called_with(boto3_ec2_client=self.mock_ec2,
                                           nat_gw_id=NAT_GATEWAY_ID,
                                           private_subnet_id=None)

    def test__check_if_route_already_exists_true(self):
        existing_routes = [
            {
                "RouteTableId": ROUTE_TABLE_ID,
                "Routes": [{"DestinationCidrBlock": INTERNET_DESTINATION}]
            }
        ]
        exists = route_through_appliance._check_if_route_already_exists(route_table_id=ROUTE_TABLE_ID,
                                                                        cidr_ipv4=INTERNET_DESTINATION,
                                                                        current_routes=existing_routes)
        self.assertTrue(exists)

    def test__check_if_route_already_exists_false(self):
        existing_routes = [
            {
                "RouteTableId": ROUTE_TABLE_ID,
            }
        ]
        exists = route_through_appliance._check_if_route_already_exists(route_table_id=ROUTE_TABLE_ID,
                                                                        cidr_ipv4=INTERNET_DESTINATION,
                                                                        current_routes=existing_routes)
        self.assertFalse(exists)

    def test_create_nat_gw_routes_nat_not_provided(self):
        with self.assertRaises(KeyError) as context:
            route_through_appliance.create_nat_gw_routes(events={
                'PrivateSubnetId': '',
                'OriginalValue': '[]'
            }, context={})

        self.assertTrue('Requires NatGatewayId' in context.exception.args)

    def test_create_nat_gw_routes_original_value_not_provided(self):
        with self.assertRaises(KeyError) as context:
            route_through_appliance.create_nat_gw_routes(events={
                'NatGatewayId': NAT_GATEWAY_ID,
            }, context={})

        self.assertTrue('Requires OriginalValue' in context.exception.args)
