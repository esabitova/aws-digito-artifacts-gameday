import unittest
from unittest.mock import MagicMock, patch

import pytest

from resource_manager.src.util.common_test_utils import do_cache_by_method_of_service, extract_all_from_input_parameters

SERVICE_NAME = 'some_service'


@pytest.mark.unit_test
class TestCommonTestUtils(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.session_mock = MagicMock()
        self.mock_some_service = MagicMock()
        self.side_effect_map = {
            SERVICE_NAME: self.mock_some_service
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.side_effect_map.get(service_name)

    def tearDown(self):
        self.patcher.stop()

    def test_do_cache_by_method_of_service(self):
        self.client.some_method.return_value = {'Key2': 'Key2Value', 'Key3': 'Key3Value1'}
        actual_ssm_test_cache = {}
        expected_ssm_test_cache = {'before': {'Key2': ['Key2Value'], 'Key3': ['Key3Value1']}}
        do_cache_by_method_of_service("before", "some_method",
                                      {'Input-Key1': 'Value1', 'Input-Key2': ['Value1'],
                                       'Output-Key2': '$.Key2', 'Output-Key3': ['$.Key3']},
                                      self.client, actual_ssm_test_cache)
        self.assertEquals(expected_ssm_test_cache, actual_ssm_test_cache)

    def test_do_cache_by_method_of_service_raise(self):
        self.assertRaises(AssertionError,
                          do_cache_by_method_of_service, "before", "some_method",
                          {'Input-Key1': 'Value1', 'Input-Key2': ['Value1'],
                           'Output-Key2': '$.Key2', 'Output-Key3': ['$.Key3_1', '$.Key3_2']},
                          self.client, {})

    def test_extract_all_from_input_parameters(self):
        input_parameters = """\
|Key1|Key2|
|{{cache:before>key}}|{{cache:after>key}}|"""

        actual_parameters = extract_all_from_input_parameters({},
                                                              {'before': {'key': 'value'}, 'after': {'key': 'value'}},
                                                              input_parameters,
                                                              {})
        expected_parameters = {'Key1': 'value',
                               'Key2': 'value'}
        self.assertEquals(expected_parameters, actual_parameters)
