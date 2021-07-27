import unittest
import pytest
import resource_manager.src.tools.resource_tool as resource_tool
import resource_manager.src.util.boto3_client_factory as client_factory
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from resource_manager.src.tools.resource_tool import ResourceTool
from resource_manager.src.resource_model import ResourceModel
from resource_manager.test.util.mock_sleep import MockSleep


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
        self.mock_cfn_resource = MagicMock()
        self.clients_map = {
            'sts': self.mock_sts_service,
            'cloudformation': self.mock_cfn_service
        }
        self.resources_map = {
            's3': self.mock_s3_resource,
            'cloudformation': self.mock_cfn_resource
        }
        self.mock_session.client.side_effect = lambda service_name, config=None: self.clients_map.get(service_name)
        self.mock_session.resource.side_effect = lambda service_name, config=None: self.resources_map.get(service_name)
        self.mock_sts_service.get_caller_identity.return_value = dict(Account='mock_aws_account_id')
        self.mock_s3_bucket = MagicMock()
        self.mock_s3_resource.Bucket.return_value = self.mock_s3_bucket

        self.resource_a = MagicMock()
        self.resource_a.configure_mock(cf_template_name='path/to/template_a.yml',
                                       cf_stack_name='template_a_stack_a_1',
                                       status=ResourceModel.Status.AVAILABLE.name)
        self.resource_b = MagicMock()
        self.resource_b.configure_mock(cf_template_name='path/to/template_b.yml',
                                       cf_stack_name='template_a_stack_b_1',
                                       status=ResourceModel.Status.AVAILABLE.name)
        self.resource_c = MagicMock()
        self.resource_c.configure_mock(cf_template_name='path/to/template_b.yml',
                                       cf_stack_name='template_a_stack_b_2',
                                       status=ResourceModel.Status.AVAILABLE.name)
        self.resource_d = MagicMock()
        self.resource_d.configure_mock(cf_template_name='path/to/template_a.yml',
                                       cf_stack_name='template_a_stack_a_2',
                                       status=ResourceModel.Status.EXECUTE_FAILED.name)
        self.err_message = lambda stack_name: f'Stack with id {stack_name} does not exist'

    def tearDown(self):
        self.session_patcher.stop()
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_list_command_success(self, scan):
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]
        resource_tool.main(['-c', 'LIST'])
        scan.assert_called_once()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    def test_list_command_by_status_success(self, scan):
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]
        resource_tool.main(['-c', 'LIST', '-s', 'AVAILABLE'])
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

        self.assertEqual(scan.call_count, 2)
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.assertEqual(self.resource_a.status, ResourceModel.Status.DELETED.name)
        self.assertEqual(self.resource_b.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_c.status, ResourceModel.Status.AVAILABLE.name)

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_by_status_command_success(self, configure, scan):
        error_response = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_2')}}
        self.mock_cfn_service.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c, self.resource_d]

        resource_tool.main(['-c', 'DESTROY', '-t', 'template_a', '-s', 'EXECUTE_FAILED'])

        self.assertEqual(scan.call_count, 2)
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.assertEqual(self.resource_a.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_d.status, ResourceModel.Status.DELETED.name)
        self.assertEqual(self.resource_b.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_c.status, ResourceModel.Status.AVAILABLE.name)

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_all_command_success(self, configure, scan):
        error_1 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_1')}}
        error_2 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_b_1')}}
        error_3 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_b_2')}}

        self.mock_cfn_service.describe_stacks.side_effect = [ClientError(error_1, 'DescribeStacks'),
                                                             ClientError(error_2, 'DescribeStacks'),
                                                             ClientError(error_3, 'DescribeStacks')]

        self.mock_cfn_resource.Stack.side_effect = [self.resource_a, self.resource_b, self.resource_c]

        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]

        resource_tool.main(['-c', 'DESTROY_ALL'])
        self.assertEqual(scan.call_count, 2)
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.assertEqual(self.mock_cfn_service.delete_stack.call_count, 3)
        self.assertEqual(self.resource_a.status, ResourceModel.Status.DELETED.name)
        self.assertEqual(self.resource_b.status, ResourceModel.Status.DELETED.name)
        self.assertEqual(self.resource_c.status, ResourceModel.Status.DELETED.name)

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_all_by_status_command_success(self, configure, scan):
        error_response = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_2')}}
        self.mock_cfn_service.describe_stacks.side_effect = ClientError(error_response, 'DescribeStacks')

        self.mock_cfn_resource.Stack.side_effect = [self.resource_a, self.resource_b, self.resource_c, self.resource_d]
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c, self.resource_d]

        resource_tool.main(['-c', 'DESTROY_ALL', '-s', 'EXECUTE_FAILED'])
        self.assertEqual(scan.call_count, 2)
        self.mock_s3_bucket.delete_objects.assert_called_once()
        self.assertEqual(self.mock_cfn_service.delete_stack.call_count, 1)
        self.assertEqual(self.resource_a.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_b.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_c.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_d.status, ResourceModel.Status.DELETED.name)

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    def test_destroy_all_not_existing_templates_command_success(self, configure, scan):
        scan.return_value = [self.resource_a, self.resource_b, self.resource_c]

        resource_tool.main(['-c', 'DESTROY', '-t', 'not_existing_template'])
        scan.assert_called_once()
        self.mock_s3_bucket.delete_objects.assert_not_called()

        self.assertEqual(self.resource_a.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_b.status, ResourceModel.Status.AVAILABLE.name)
        self.assertEqual(self.resource_c.status, ResourceModel.Status.AVAILABLE.name)

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    @patch('time.sleep')
    def test_destroy_all_command_with_dependencies_fail(self, sleep_mock, configure, scan):
        sleep_mock.side_effect = MockSleep().sleep
        error_1 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_1')}}
        error_2 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_b_stack_a_1')}}

        self.mock_cfn_service.describe_stacks.side_effect = [ClientError(error_1, 'DescribeStacks'),
                                                             ClientError(error_2, 'DescribeStacks')]
        self.mock_cfn_service.delete_stack.side_effect = [Exception('dummy_exception')]

        resource_a = MagicMock()
        resource_a.configure_mock(cf_template_name='path/to/template_a.yml',
                                  cf_stack_name='template_a_stack_a_1',
                                  status=ResourceModel.Status.AVAILABLE.name)
        resource_b = MagicMock()
        resource_b.configure_mock(cf_template_name='path/to/template_b.yml',
                                  cf_stack_name='template_b_stack_a_1',
                                  cfn_dependency_stacks='[template_a_stack_a_1]',
                                  status=ResourceModel.Status.AVAILABLE.name)

        scan.return_value = [resource_a, resource_b]

        self.assertRaises(Exception, resource_tool.main, ['-c', 'DESTROY_ALL'])
        self.mock_cfn_service.delete_stack.assert_called_once()
        self.assertEqual(resource_a.status, ResourceModel.Status.DELETE_FAILED.name)
        self.assertEqual(resource_b.status, ResourceModel.Status.DELETE_FAILED.name)
        self.assertTrue(scan.call_count >= 2)
        self.mock_s3_bucket.delete_objects.assert_not_called()

    @patch('resource_manager.src.resource_model.ResourceModel.scan')
    @patch('resource_manager.src.resource_model.ResourceModel.configure')
    @patch('time.sleep')
    def test_destroy_all_command_with_dependencies_success(self, sleep_mock, configure, scan):
        sleep_mock.side_effect = MockSleep().sleep
        error_1 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_a_stack_a_1')}}
        error_2 = {'Error': {'Code': 'ValidationError', 'Message': self.err_message('template_b_stack_a_1')}}

        self.mock_cfn_service.describe_stacks.side_effect = [ClientError(error_1, 'DescribeStacks'),
                                                             ClientError(error_2, 'DescribeStacks')]

        resource_a = MagicMock()
        resource_a.configure_mock(cf_template_name='path/to/template_a.yml',
                                  cf_stack_name='template_a_stack_a_1',
                                  status=ResourceModel.Status.AVAILABLE.name)
        resource_b = MagicMock()
        resource_b.configure_mock(cf_template_name='path/to/template_b.yml',
                                  cf_stack_name='template_b_stack_a_1',
                                  cfn_dependency_stacks='[template_a_stack_a_1]',
                                  status=ResourceModel.Status.AVAILABLE.name)

        scan.return_value = [resource_a, resource_b]

        resource_tool.main(['-c', 'DESTROY_ALL'])
        self.assertEqual(self.mock_cfn_service.delete_stack.call_count, 2)
        self.assertEqual(resource_a.status, ResourceModel.Status.DELETED.name)
        self.assertEqual(resource_b.status, ResourceModel.Status.DELETED.name)
        self.assertTrue(scan.call_count >= 2)
        self.mock_s3_bucket.delete_objects.assert_called_once()

    def test_find_resource_dependents_success(self):
        resource_to_delete = MagicMock()
        resource_to_delete.configure_mock(cf_template_name='ParentTemplateTest.yml',
                                          cf_stack_name='ParentStackTest')
        r1 = MagicMock()
        r1.configure_mock(cf_template_name='ChildTemplateTest1.yml',
                          cf_stack_name='ChildStackTest1',
                          cfn_dependency_stacks=['ParentStackTest'])
        r2 = MagicMock()
        r2.configure_mock(cf_template_name='ChildTemplateTest2.yml',
                          cf_stack_name='ChildStackTest2',
                          cfn_dependency_stacks=['ParentStackTest'])
        all_resources = [r1, r2]

        rt = ResourceTool(self.mock_session)
        dependents = rt._find_resource_dependents(resource_to_delete, all_resources)
        self.assertEqual(len(dependents), 2)
