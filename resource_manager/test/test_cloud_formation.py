import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from resource_manager.src.cloud_formation import CloudFormationTemplate
from botocore.exceptions import ClientError


@pytest.mark.unit_test
class TestCloudFormation(unittest.TestCase):

    def setUp(self):
        self.client_patcher = patch('boto3.client')
        self.client = self.client_patcher.start()
        self.cf_service_mock = MagicMock()
        self.client_side_effect_map = {
            'cloudformation': self.cf_service_mock,
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
        self.client_patcher.stop()
        self.resource_patcher.stop()

    def test_deploy_cf_stack_new_success(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'IN_PROGRESS'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        CloudFormationTemplate.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

        self.cf_service_mock.create_stack.assert_called_once()
        self.cf_service_mock.describe_stacks.assert_has_calls([call(StackName='test_stack_name'),
                                                               call(StackName='test_stack_name'),
                                                               call(StackName='test_stack_name')])

    def test_deploy_cf_stack_update_success(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        err_response = {'Error': {'Type': 'Sender', 'Code': 'AlreadyExistsException'}}
        self.cf_service_mock.create_stack.side_effect = ClientError(error_response=err_response,
                                                                    operation_name='CreateStack')

        CloudFormationTemplate.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

        self.cf_service_mock.create_stack.assert_called_once()
        self.cf_service_mock.update_stack.assert_called_once()
        self.cf_service_mock.describe_stacks.assert_has_calls([call(StackName='test_stack_name'),
                                                               call(StackName='test_stack_name')])

    def test_deploy_cf_stack_update_nothing_to_update_success(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        err_response_1 = {'Error': {'Type': 'Sender', 'Code': 'AlreadyExistsException'}}
        self.cf_service_mock.create_stack.side_effect = ClientError(error_response=err_response_1,
                                                                    operation_name='CreateStack')

        err_response_2 = {'Error': {'Type': 'Sender', 'Code': 'ValidationError',
                                    'Message': 'No updates are to be performed.'}}
        self.cf_service_mock.update_stack.side_effect = ClientError(error_response=err_response_2,
                                                                    operation_name='UpdateStack')

        CloudFormationTemplate.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

        self.cf_service_mock.create_stack.assert_called_once()
        self.cf_service_mock.update_stack.assert_called_once()
        self.cf_service_mock.describe_stacks.assert_has_calls([call(StackName='test_stack_name')])

    def test_deploy_cf_stack_update_fail(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        err_response_1 = {'Error': {'Type': 'Sender', 'Code': 'AlreadyExistsException'}}
        self.cf_service_mock.create_stack.side_effect = ClientError(error_response=err_response_1,
                                                                    operation_name='CreateStack')

        err_response_2 = {'Error': {'Type': 'Sender', 'Code': 'UnexpectedError', 'Message': 'Unexpected failure.'}}
        self.cf_service_mock.update_stack.side_effect = ClientError(error_response=err_response_2,
                                                                    operation_name='UpdateStack')

        self.assertRaises(Exception,  CloudFormationTemplate.deploy_cf_stack,
                          'test_template_url', 'test_stack_name', test_in_param='test_in_val')

    def test_deploy_cf_stack_create_fail(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        err_response = {'Error': {'Type': 'Sender', 'Code': 'UnexpectedError', 'Message': 'Unexpected failure.'}}
        self.cf_service_mock.create_stack.side_effect = ClientError(error_response=err_response,
                                                                    operation_name='CreateStack')

        self.assertRaises(Exception, CloudFormationTemplate.deploy_cf_stack, 'test_template_url', 'test_stack_name',
                          test_in_param='test_in_val')

    def test_delete_cf_stack_success(self):
        CloudFormationTemplate.delete_cf_stack('test_stack_name')

        self.cf_service_mock.delete_stack.assert_called_once()
        self.cf_service_mock.get_waiter.assert_called_once()
