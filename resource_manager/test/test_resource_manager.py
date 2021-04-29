import unittest
import pytest
import resource_manager.src.config as config
import resource_manager.src.util.yaml_util as yaml_util
from unittest.mock import patch, MagicMock, call, mock_open
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.resource_model import ResourceModel


@pytest.mark.unit_test
class TestResourceManager(unittest.TestCase):

    def setUp(self):
        self.os_path_patcher = patch('os.path')
        self.os_path_mock = self.os_path_patcher.start()
        self.test_template_name = 'test_cf_template_name'
        self.test_bucket_name = 'test_bucket_name'
        self.dummy_test_session_id = 'dummy_test_session_id'
        self.os_path_mock.isfile.return_value = True
        self.s3_helper_mock = MagicMock()
        self.s3_helper_mock.get_bucket_name.return_value = self.test_bucket_name
        self.s3_helper_mock.get_file_content.return_value = None
        self.cfn_helper_mock = MagicMock()

        self.rm = ResourceManager(self.cfn_helper_mock, self.s3_helper_mock, dict(), self.dummy_test_session_id)

        self.file_data_dummy = '{"AWSTemplateFormatVersion": "2010-09-09",' \
                               '"Description": "Assume Roles for SSM automation execution.",' \
                               '"Outputs": {},' \
                               '"Resources": {}}'
        self.cfn_content_sha1 = yaml_util.get_yaml_content_sha1_hash(yaml_util.loads_yaml(self.file_data_dummy))
        self.cfn_input_param_sha1 = yaml_util.get_yaml_content_sha1_hash({'test_param': 'test_param_value'})
        self.mock_file_patcher = patch('builtins.open', mock_open(read_data=self.file_data_dummy))
        self.mock_file = self.mock_file_patcher.start()

    def tearDown(self):
        self.os_path_patcher.stop()
        self.mock_file_patcher.stop()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_by_template_name_missing_template_index_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        create_mock.return_value = r2

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        resource = self.rm.pull_resource_by_template(self.test_template_name, 2,
                                                     ResourceManager.ResourceType.ON_DEMAND, 5)
        self.assertEqual(resource.cf_stack_index, 0)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND.name,
                                 test_param='test_param_value')
        resource = self.rm.pull_resource_by_template(self.test_template_name, 2,
                                                     ResourceManager.ResourceType.ON_DEMAND, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_cfn_param_sha1_not_equal_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1="not_equal_param_sha1")
        query_mock.return_value = [r1, r2]

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND.name,
                                 test_param='test_param_value')
        resource = self.rm.pull_resource_by_template(self.test_template_name, 2,
                                                     ResourceManager.ResourceType.ON_DEMAND, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        self.assertEqual(r2.save.call_count, 2)
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_cfn_template_sha1_not_equal_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1="not_equal_cfn_template_sha1",
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)
        query_mock.return_value = [r1, r2]

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND.name,
                                 test_param='test_param_value')
        resource = self.rm.pull_resource_by_template(self.test_template_name, 2,
                                                     ResourceManager.ResourceType.ON_DEMAND, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        self.assertEqual(r2.save.call_count, 2)
        r1.save.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_by_template_name_create_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = r2

        self.rm.add_cfn_template(self.test_template_name, ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        resource = self.rm.pull_resource_by_template(self.test_template_name, 2,
                                                     ResourceManager.ResourceType.ON_DEMAND, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_timeout_fail(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1, r2]

        self.rm.add_cfn_template(self.test_template_name, ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        self.assertRaises(Exception, self.rm.pull_resource_by_template, self.test_template_name, 2, 5)

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.LEASED.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        self.rm.add_cfn_template(self.test_template_name, ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        self.rm.add_cfn_template(self.test_template_name + '_1', ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')

        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for resource in resources:
            self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    def test_pull_resources_create_success(self, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0,
                          status=ResourceModel.Status.AVAILABLE.name,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1,
                          status=ResourceModel.Status.LEASED.name,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1)

        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': []
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        mock = MagicMock()
        mock.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = mock

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        self.rm.add_cfn_template(self.test_template_name + '_1',
                                 ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')

        resources = self.rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for resource in resources:
            self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)

        self.s3_helper_mock.upload_file.assert_called_once()
        self.cfn_helper_mock.deploy_cf_stack.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_get_cf_output_params_success(self, query_mock):

        base_names = {
            'test_cf_template_name': self.test_template_name + '.yml',
            'test_cf_template_name_1': self.test_template_name + '_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda path: base_names.get(path)

        file_names = {
            self.test_template_name + '.yml': (self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name + '_1', 'yml'),
        }
        self.os_path_mock.splitext.side_effect = lambda base_name: file_names.get(base_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_1',
                                                                      'OutputValue': 'test_value_1'}]})
        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name,
                          cf_template_name=self.test_template_name,
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_2',
                                                                      'OutputValue': 'test_value_2'}]})
        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name + '_1',
                          type=ResourceManager.ResourceType.ON_DEMAND.name,
                          cf_template_sha1=self.cfn_content_sha1,
                          cf_input_parameters_sha1=self.cfn_input_param_sha1,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_3',
                                                                      'OutputValue': 'test_value_3'}]})
        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        self.rm.add_cfn_template(self.test_template_name,
                                 ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')
        self.rm.add_cfn_template(self.test_template_name + '_1',
                                 ResourceManager.ResourceType.ON_DEMAND,
                                 test_param='test_param_value')

        resources_params = self.rm.get_cfn_output_params()
        self.assertEqual(len(resources_params), 2)
        self.assertIsNotNone(resources_params.get(self.test_template_name + '_1'))
        self.assertIsNotNone(resources_params.get(self.test_template_name))

        self.assertIsNotNone(resources_params.get(self.test_template_name).get('test_key_1'))
        self.assertIsNotNone(resources_params.get(self.test_template_name + '_1').get('test_key_3'))
        self.assertEqual(resources_params.get(self.test_template_name + '_1')['test_key_3'], 'test_value_3')
        self.assertEqual(resources_params.get(self.test_template_name)['test_key_1'], 'test_value_1')
        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id=self.dummy_test_session_id)
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id=self.dummy_test_session_id)
        scan_mock.return_value = [r1, r2]

        self.rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_no_session_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id='dummy_test_session_id_a')
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id='dummy_test_session_id_b')
        scan_mock.return_value = [r1, r2]
        rm = ResourceManager(self.cfn_helper_mock, self.s3_helper_mock, dict(), None)
        rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_fix_stalled_resources_no_deletion_success(self, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(status=ResourceModel.Status.LEASED.name,
                          test_session_id=self.dummy_test_session_id)
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name,
                          test_session_id='dummy_bad_test_session_id')
        scan_mock.return_value = [r1, r2]

        self.rm.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.delete_table')
    def test_destroy_all_resources_success(self, delete_table_mock, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(cf_stack_name='stack_name_1')

        r2 = MagicMock()
        r2.configure_mock(cf_stack_name='stack_name_2')
        scan_mock.return_value = [r1, r2]

        self.rm.destroy_all_resources()

        self.cfn_helper_mock.delete_cf_stack.assert_has_calls([call('stack_name_1'), call('stack_name_2')])
        self.s3_helper_mock.delete_bucket.assert_called_once()
        self.s3_helper_mock.get_bucket_name.assert_called_once()
        delete_table_mock.assert_called_once()

    def test_resource_type_from_string_success(self):
        actual_type = ResourceManager.ResourceType.from_string('ON_DEMAND')
        self.assertEqual(actual_type, ResourceManager.ResourceType.ON_DEMAND)

    def test_resource_type_from_string_fail(self):
        self.assertRaises(Exception, ResourceManager.ResourceType.from_string, 'NOT_SUPPORTED')

    def test_get_resource_pool_size_custom_success(self):
        expected_pool_size = 10
        custom_pool_size = dict(TesTemplateA=expected_pool_size)
        rm = ResourceManager(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id')
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceManager.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_custom_override_config_success(self):
        expected_pool_size = 10
        config.pool_size['TesTemplateA'] = 5
        custom_pool_size = dict(TesTemplateA=expected_pool_size)
        rm = ResourceManager(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id')
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceManager.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)

    def test_get_resource_pool_size_config_success(self):
        expected_pool_size = 6
        custom_pool_size = dict()
        config.pool_size['TesTemplateA'] = expected_pool_size
        rm = ResourceManager(self.cfn_helper_mock, self.s3_helper_mock, custom_pool_size, 'dummy_test_session_id')
        actual_pool_size = rm._get_resource_pool_size('TesTemplateA', ResourceManager.ResourceType.ON_DEMAND)
        self.assertEqual(actual_pool_size, expected_pool_size)
