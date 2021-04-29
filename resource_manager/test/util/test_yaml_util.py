import unittest
import pytest
import os
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

    def tearDown(self):
        pass

    def test_file_loads_yaml_success(self):
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy_1))
        self.mock_file = self.mock_file_patcher.start()

        result = yaml_util.file_loads_yaml('test')
        self.assertIsNotNone(result)

        self.mock_file_patcher.stop()

    def test_is_equal_false_success(self):
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy_1))
        self.mock_file = self.mock_file_patcher.start()

        cont_1 = yaml_util.loads_yaml(self.file_data_dummy_1)
        cont_2 = yaml_util.loads_yaml(self.file_data_dummy_2)
        self.assertFalse(yaml_util.is_equal(cont_1, cont_2))

        self.mock_file_patcher.stop()

    def test_is_equal_true_success(self):
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy_1))
        self.mock_file = self.mock_file_patcher.start()

        cont_1 = yaml_util.loads_yaml(self.file_data_dummy_1)
        cont_2 = yaml_util.loads_yaml(self.file_data_dummy_1)
        self.assertTrue(yaml_util.is_equal(cont_1, cont_2))

        self.mock_file_patcher.stop()

    def test_get_yaml_content_sha1_hash_equal_success(self):
        expected_hash = yaml_util.get_yaml_content_sha1_hash(self.file_data_dummy_1)
        actual_hash = yaml_util.get_yaml_content_sha1_hash(self.file_data_dummy_1)
        self.assertEqual(expected_hash, actual_hash)

    def test_get_yaml_content_sha1_hash_not_equal_success(self):
        expected_hash = yaml_util.get_yaml_content_sha1_hash(self.file_data_dummy_1)
        actual_hash = yaml_util.get_yaml_content_sha1_hash(self.file_data_dummy_2)
        self.assertNotEqual(expected_hash, actual_hash)

    def test_get_yaml_file_sha1_hash_equal_success(self):
        cfn_template_path_1 = os.path.dirname(os.path.abspath(__file__)) + '/../data/TestCfnTemplate_1.yml'
        expected_hash = yaml_util.get_yaml_file_sha1_hash(cfn_template_path_1)
        actual_hash = yaml_util.get_yaml_file_sha1_hash(cfn_template_path_1)
        self.assertEqual(expected_hash, actual_hash)

    def test_get_yaml_file_sha1_hash_not_equal_success(self):
        cfn_template_path_1 = os.path.dirname(os.path.abspath(__file__)) + '/../data/TestCfnTemplate_1.yml'
        cfn_template_path_2 = os.path.dirname(os.path.abspath(__file__)) + '/../data/TestCfnTemplate_2.yml'
        temp_hash_1 = yaml_util.get_yaml_file_sha1_hash(cfn_template_path_1)
        temp_hash_2 = yaml_util.get_yaml_file_sha1_hash(cfn_template_path_2)
        self.assertNotEqual(temp_hash_1, temp_hash_2)
