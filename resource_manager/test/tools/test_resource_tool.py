import unittest
import pytest
import resource_manager.src.tools.resource_tool as resource_tool
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError


@pytest.mark.unit_test
class TestResourceTool(unittest.TestCase):

    def setUp(self):
        self.mock_session = MagicMock()
        self.mock_session.configure_mock(region_name='test_region_name')
        self.session_patcher = patch('boto3.Session', MagicMock(return_value=self.mock_session))
        self.boto3_mock_session = self.session_patcher.start()
        self.mock_sts_service = MagicMock()
        self.mock_cfn_service = MagicMock()
        self.mock_s3_resource = MagicMock()
        self.clients_map = {
            'sts': self.mock_sts_service,
            'cloudformation': self.mock_cfn_service
        }
        self.resources_map = {
            's3': self.mock_s3_resource,
        }
        self.mock_session.client.side_effect = lambda service_name: self.clients_map.get(service_name)
        self.mock_session.resource.side_effect = lambda service_name: self.resources_map.get(service_name)
        self.mock_sts_service.get_caller_identity.return_value = dict(Account='mock_aws_account_id')
        self.mock_s3_bucket = MagicMock()
        self.mock_s3_resource.Bucket.return_value = self.mock_s3_bucket

        self.resource_a = MagicMock()
        self.resource_a.configure_mock(cf_template_name='path/to/template_a.yml',
                                       cf_stack_name='template_a_stack_a_1')
        self.resource_b = MagicMock()
        self.resource_b.configure_mock(cf_template_name='path/to/template_b.yml',
                                       cf_stack_name='template_a_stack_b_1')
        self.resource_c = MagicMock()
        self.resource_c.configure_mock(cf_template_name='path/to/template_b.yml',
                                       cf_stack_name='template_a_stack_b_2')
        self.err_message = lambda stack_name: f'Stack with id {stack_name} does not exist'

    def tearDown(self):
        self.session_patcher.stop()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_list_command_success(self, scan):
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]
        resource_tool.main(['-c', 'LIST'])
        scan.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_destroy_command_no_templates_fail(self, scan):
        self.assertRaises(SystemExit, resource_tool.main, ['-c', 'DESTROY'])

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_no_commands_given_fail(self, scan):
        self.assertRaises(SystemExit, resource_tool.main, [])

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_command_success(self, configure, scan):
        error_response = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_1')}}
        self.mock_cfn_service.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]

        resource_tool.main(['-c', 'DESTROY', '-t', 'template_a'])
        scan.assert_called_once()
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.resource_a.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_all_command_success(self, configure, scan):
        error_1 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_1')}}
        error_2 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_b_1')}}
        error_3 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_b_2')}}

        self.mock_cfn_service.describe_stacks.side_effect = [ClientError(error_1, 'DescribeStacks'),
                                                             ClientError(error_2, 'DescribeStacks'),
                                                             ClientError(error_3, 'DescribeStacks')]

        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]

        resource_tool.main(['-c', 'DESTROY_ALL'])
        scan.assert_called_once()
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.resource_a.delete.assert_called_once()
        self.resource_b.delete.assert_called_once()
        self.resource_c.delete.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_all_not_existing_templates_command_success(self, configure, scan):
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]

        resource_tool.main(['-c', 'DESTROY', '-t', 'not_existing_template'])
        scan.assert_called_once()
        self.mock_s3_bucket.delete_objects.assert_not_called()
        self.resource_a.delete.assert_not_called()
        self.resource_b.delete.assert_not_called()
        self.resource_c.delete.assert_not_called()
