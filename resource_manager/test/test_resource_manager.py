import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from resource_manager.src.resource_manager import ResourceManager
from resource_manager.src.resource_model import ResourceModel


@pytest.mark.unit_test
class TestResourceManager(unittest.TestCase):

    def setUp(self):
        self.os_path_patcher = patch('os.path')
        self.os_path_mock = self.os_path_patcher.start()
        self.test_template_name = 'test_cf_template_name'
        self.os_path_mock.isfile.return_value = True

        self.client_patcher = patch('boto3.client')
        self.client = self.client_patcher.start()
        self.mock_cloudformation = MagicMock()
        self.client_side_effect_map = {
            'cloudformation': self.mock_cloudformation,
        }
        self.client.side_effect = lambda service_name: self.client_side_effect_map.get(service_name)

        self.resource_patcher = patch('boto3.resource')
        self.resource = self.resource_patcher.start()
        self.cf_resource = MagicMock()
        self.resource_side_effect_map = {
            'cloudformation': self.cf_resource
        }
        self.resource.side_effect = lambda service_name: self.resource_side_effect_map.get(service_name)

    def tearDown(self):
        self.os_path_patcher.stop()
        self.client_patcher.stop()
        self.resource_patcher.stop()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    @patch('resource_manager.src.cloud_formation.CloudFormationTemplate.deploy_cf_stack')
    @patch('resource_manager.src.s3.S3.upload_file')
    def test_pull_resources_by_template_name_missing_template_index_success(self, s3_mock, cf_mock,
                                                                            create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=1, status=ResourceModel.Status.AVAILABLE.name)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=0)
        create_mock.return_value = r2

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        resource = rm.pull_resource_by_template_name(self.test_template_name, 2, 5)
        self.assertEqual(resource.cf_stack_index, 0)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        s3_mock.assert_called_once()
        cf_mock.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.LEASED.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.AVAILABLE.name)
        query_mock.return_value = [r1, r2]

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        resource = rm.pull_resource_by_template_name(self.test_template_name, 2, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    @patch('resource_manager.src.cloud_formation.CloudFormationTemplate.deploy_cf_stack')
    @patch('resource_manager.src.s3.S3.upload_file')
    def test_pull_resources_by_template_name_create_success(self, s3_mock, cf_mock,
                                                            create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1]

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = r2

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        resource = rm.pull_resource_by_template_name(self.test_template_name, 2, 5)
        self.assertEqual(resource.cf_stack_index, 1)
        self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r2.save.assert_called_once()

        s3_mock.assert_called_once()
        cf_mock.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_by_template_name_timeout_fail(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.LEASED.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name)
        query_mock.return_value = [r1, r2]

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        self.assertRaises(Exception, rm.pull_resource_by_template_name, self.test_template_name, 2, 5)

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_pull_resources_success(self, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')
        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name)

        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)

        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        rm.add_cf_template(self.test_template_name+'_1', test_param='test_param_value')

        resources = rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for resource in resources:
            self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)
        r3.save.assert_called_once()
        r1.save.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    @patch('resource_manager.src.resource_model.ResourceModel.create')
    @patch('resource_manager.src.cloud_formation.CloudFormationTemplate.deploy_cf_stack')
    @patch('resource_manager.src.s3.S3.upload_file')
    def test_pull_resources_create_success(self, s3_mock, cf_mock, create_mock, query_mock):
        self.os_path_mock.splitext.return_value = (self.test_template_name, 'yml')

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)

        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name)

        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': []
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        mock = MagicMock()
        mock.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name)
        create_mock.return_value = mock

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        rm.add_cf_template(self.test_template_name + '_1', test_param='test_param_value')

        resources = rm.pull_resources()
        self.assertEqual(len(resources), 2)
        for resource in resources:
            self.assertEqual(resource.status, ResourceModel.Status.LEASED.name)

        s3_mock.assert_called_once()
        cf_mock.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.query')
    def test_get_cf_output_params_success(self, query_mock):

        base_names = {
            'resource_manager/cloud_formation_templates/test_cf_template_name': self.test_template_name+'.yml',
            'resource_manager/cloud_formation_templates/test_cf_template_name_1': self.test_template_name+'_1.yml'
        }
        self.os_path_mock.basename.side_effect = lambda path: base_names.get(path)

        file_names = {
            self.test_template_name + '.yml':(self.test_template_name, 'yml'),
            self.test_template_name + '_1.yml': (self.test_template_name+'_1', 'yml'),
        }
        self.os_path_mock.splitext.side_effect = lambda base_name: file_names.get(base_name)

        r1 = MagicMock()
        r1.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_1',
                                                                      'OutputValue': 'test_value_1'}]})
        r2 = MagicMock()
        r2.configure_mock(cf_stack_index=1, status=ResourceModel.Status.LEASED.name,
                          cf_template_name=self.test_template_name,
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_2',
                                                                      'OutputValue': 'test_value_2'}]})
        r3 = MagicMock()
        r3.configure_mock(cf_stack_index=0, status=ResourceModel.Status.AVAILABLE.name,
                          cf_template_name=self.test_template_name + '_1',
                          attribute_values={'cf_output_parameters': [{'OutputKey': 'test_key_3',
                                                                      'OutputValue': 'test_value_3'}]})
        client_side_effect_map = {
            self.test_template_name: [r1, r2],
            self.test_template_name + '_1': [r3]
        }
        query_mock.side_effect = lambda cf_template_name: client_side_effect_map.get(cf_template_name)

        rm = ResourceManager()
        rm.add_cf_template(self.test_template_name, test_param='test_param_value')
        rm.add_cf_template(self.test_template_name + '_1', test_param='test_param_value')

        resources_params = rm.get_cf_output_params()
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
        r1.configure_mock(status=ResourceModel.Status.LEASED.name)
        r2 = MagicMock()
        r2.configure_mock(status=ResourceModel.Status.CREATING.name)
        scan_mock.return_value = [r1, r2]

        ResourceManager.fix_stalled_resources()

        self.assertEqual(r1.status, ResourceModel.Status.AVAILABLE.name)
        r2.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.delete_table')
    @patch('resource_manager.src.cloud_formation.CloudFormationTemplate.delete_cf_stack')
    @patch('resource_manager.src.s3.S3.delete_bucket')
    @patch('resource_manager.src.s3.S3.get_bucket_name')
    def test_destroy_all_resources_success(self, get_bucket_name_mock, delete_bucket_mock,
                                           delete_stack_mock, delete_table_mock, scan_mock):
        r1 = MagicMock()
        r1.configure_mock(cf_stack_name='stack_name_1')

        r2 = MagicMock()
        r2.configure_mock(cf_stack_name='stack_name_2')
        scan_mock.return_value = [r1, r2]

        ResourceManager.destroy_all_resources()

        delete_stack_mock.assert_has_calls([call('stack_name_1'), call('stack_name_2')])
        delete_table_mock.assert_called_once()
        get_bucket_name_mock.assert_called_once()
        delete_bucket_mock.assert_called_once()



    def test_my_test(self):
        items = [('a','b'), ('z','g')]
        print(items.pop())

