import unittest
import pytest
from unittest.mock import patch, MagicMock
import resource_manager.src.util.common_test_utils as common_test_utils
import resource_manager.src.util.boto3_client_factory as client_factory
SERVICE_NAME = 'some_service'


@pytest.mark.unit_test
class TestCommonTestUtil(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_ec2 = MagicMock()
        self.session_mock = MagicMock()
        self.side_effect_map = {
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()
        client_factory.clients = {}
        client_factory.resources = {}

    def test_put_to_ssm_test_cache(self):
        cache = {}
        cache_key = "key"
        cache_property = "property"
        value = "value"
        common_test_utils.put_to_ssm_test_cache(cache, cache_key, cache_property, value)
        self.assertEqual({'key': {'property': 'value'}}, cache)

        cache = {}
        cache_key = None
        cache_property = "property"
        value = "value"
        common_test_utils.put_to_ssm_test_cache(cache, cache_key, cache_property, value)
        self.assertEqual({'property': 'value'}, cache)

        cache = {'key': {'property2': 'value2'}}
        cache_key = "key"
        cache_property = "property"
        value = "value"
        common_test_utils.put_to_ssm_test_cache(cache, cache_key, cache_property, value)
        self.assertEqual({'key': {'property': 'value', 'property2': 'value2'}}, cache)

    def test_extract_all_from_input_parameters(self):
        cache = {}
        alarms = {}
        input_parameters = """|a|b|
|{{cfn-output:test_stack>test_key}}|c|"""
        cf_output = {'test_stack': {'test_key': 'test_val'}}
        res = common_test_utils.extract_all_from_input_parameters(cf_output, cache, input_parameters, alarms)

        self.assertEqual({'a': 'test_val', 'b': 'c'}, res)

    def test_do_cache_by_method_of_service(self):
        self.client.some_method.return_value = {'Key2': 'Key2Value', 'Key3': 'Key3Value1'}
        actual_ssm_test_cache = {}
        expected_ssm_test_cache = {'before': {'Key2': 'Key2Value', 'Key3': 'Key3Value1'}}
        common_test_utils.do_cache_by_method_of_service("before", "some_method",
                                                        {'Input-Key1': 'Value1', 'Input-Key2': ['Value1'],
                                                         'Output-Key2': '$.Key2', 'Output-Key3': ['$.Key3']},
                                                        self.client, actual_ssm_test_cache)
        self.assertEqual(expected_ssm_test_cache, actual_ssm_test_cache)

    def test_do_cache_by_method_of_service_raise(self):
        self.assertRaises(AssertionError,
                          common_test_utils.do_cache_by_method_of_service, "before", "some_method",
                          {'Input-Key1': 'Value1', 'Input-Key2': ['Value1'],
                           'Output-Key2': '$.Key2', 'Output-Key3': ['$.Key3_1', '$.Key3_2']},
                          self.client, {})

    def test_extract_and_cache_param_values(self):
        cf_output = {'test_stack': {'test_key': 'test_val'}}
        input_parameters = """|a|b|
|{{cfn-output:test_stack>test_key}}|c|"""
        param_list = 'a,b'
        resource_manager = MagicMock()
        resource_manager.get_cfn_output_params.return_value = cf_output
        ssm_test_cache = {}
        common_test_utils.extract_and_cache_param_values(
            input_parameters,
            param_list,
            resource_manager,
            ssm_test_cache,
            'test'
        )
        self.assertEqual({'test': {'a': 'test_val', 'b': 'c'}}, ssm_test_cache)

    def test_check_security_group_exists_no_sg(self):
        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': []
        }
        res = common_test_utils.check_security_group_exists(self.session_mock, 'test')
        self.assertEqual(False, res)

    def test_check_security_group_exists(self):
        self.mock_ec2.describe_security_groups.return_value = {
            'SecurityGroups': [
                {
                    "GroupName": "test"
                }
            ]
        }
        res = common_test_utils.check_security_group_exists(self.session_mock, 'test')
        self.assertEqual(True, res)
