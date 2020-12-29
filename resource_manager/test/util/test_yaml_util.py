import unittest
import pytest
from unittest.mock import patch, mock_open
import resource_manager.src.util.yaml_util as yaml_util

@pytest.mark.unit_test
class TestYamlUtil(unittest.TestCase):

    def setUp(self):
        self.file_data_dummy_1 = '{"AWSTemplateFormatVersion": "2010-09-09",' \
                                 '"Description": "Assume Roles for SSM automation execution.",' \
                                 '"Outputs": {"ClusterId" : {"Description":"Test Description"}},' \
                                 '"Resources": {}}'
        self.file_data_dummy_2 = '{"AWSTemplateFormatVersion": "2010-09-09",' \
                                 '"Description": "Assume Roles for SSM automation execution.",' \
                                 '"Outputs": {"ClusterId" : {"Description":"Test Description 1"}},' \
                                 '"Resources": {}}'
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy_1))
        self.mock_file = self.mock_file_patcher.start()

    def tearDown(self):
        self.mock_file_patcher.stop()

    def test_file_loads_yaml_success(self):
        result = yaml_util.file_loads_yaml('test')
        self.assertIsNotNone(result)

    def test_is_equal_false_success(self):
        cont_1 = yaml_util.loads_yaml(self.file_data_dummy_1)
        cont_2 = yaml_util.loads_yaml(self.file_data_dummy_2)
        self.assertFalse(yaml_util.is_equal(cont_1, cont_2))

    def test_is_equal_true_success(self):
        cont_1 = yaml_util.loads_yaml(self.file_data_dummy_1)
        cont_2 = yaml_util.loads_yaml(self.file_data_dummy_1)
        self.assertTrue(yaml_util.is_equal(cont_1, cont_2))


