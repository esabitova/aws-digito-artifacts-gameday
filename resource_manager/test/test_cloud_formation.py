import unittest
import pytest
from unittest.mock import MagicMock, call, patch
from resource_manager.src.cloud_formation import CloudFormationTemplate
from botocore.exceptions import ClientError
import resource_manager.src.util.boto3_client_factory as client_factory
from documents.util.scripts.test.mock_sleep import MockSleep


@pytest.mark.unit_test
class TestCloudFormation(unittest.TestCase):

    def setUp(self):
        self.session_mock = MagicMock()
        self.cf_service_mock = MagicMock()
        self.client_side_effect_map = {
            'cloudformation': self.cf_service_mock,
        }
        self.session_mock.client.side_effect = lambda service_name, config=None: \
            self.client_side_effect_map.get(service_name)

        self.cf_resource = MagicMock()
        self.resource_side_effect_map = {
            'cloudformation': self.cf_resource
        }
        self.session_mock.resource.side_effect = lambda service_name, config=None: \
            self.resource_side_effect_map.get(service_name)

        self.cfn_helper = CloudFormationTemplate(self.session_mock)

    def tearDown(self):
        # Clean client factory cache after each test.
        client_factory.clients = {}
        client_factory.resources = {}

    @patch('time.sleep')
    @patch('time.time')
    def test_deploy_cf_stack_new_success(self, patched_time, patched_sleep):
        mock_sleep = MockSleep()
        patched_time.side_effect = mock_sleep.time
        patched_sleep.side_effect = mock_sleep.sleep

        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'IN_PROGRESS'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        self.cfn_helper.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

        self.cf_service_mock.create_stack.assert_called_once_with(StackName='test_stack_name',
                                                                  TemplateURL='test_template_url',
                                                                  Capabilities=['CAPABILITY_IAM'],
                                                                  Parameters=[{'ParameterKey': 'test_in_param',
                                                                               'ParameterValue': 'test_in_val'}],
                                                                  EnableTerminationProtection=True)
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

        self.cfn_helper.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

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

        self.cfn_helper.deploy_cf_stack('test_template_url', 'test_stack_name', test_in_param='test_in_val')

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

        self.assertRaises(Exception, self.cfn_helper.deploy_cf_stack,
                          'test_template_url', 'test_stack_name', test_in_param='test_in_val')

    def test_deploy_cf_stack_create_fail(self):
        self.cf_service_mock.describe_stacks.side_effect = [
            {'Stacks': [{'StackStatus': 'COMPLETED'}]},
            {'Stacks': [{'StackStatus': 'COMPLETED'}]}
        ]
        err_response = {'Error': {'Type': 'Sender', 'Code': 'UnexpectedError', 'Message': 'Unexpected failure.'}}

        self.cf_service_mock.create_stack.side_effect = ClientError(error_response=err_response,
                                                                    operation_name='CreateStack')

        self.assertRaises(Exception, self.cfn_helper.deploy_cf_stack, 'test_template_url', 'test_stack_name',
                          test_in_param='test_in_val')

    def test_delete_cf_stack_success(self):
        self.cfn_helper.delete_cf_stack('test_stack_name')

        self.cf_service_mock.update_termination_protection.assert_called_once_with(
            StackName='test_stack_name', EnableTerminationProtection=False)
        self.cf_service_mock.delete_stack.assert_called_once()
        self.cf_service_mock.describe_stacks.assert_called_once()

    def test_describe_cf_stack_success(self):
        stack_name = "test_stack_name"
        self.cfn_helper.describe_cf_stack(stack_name)

        self.cf_service_mock.describe_stacks.assert_called_once_with(StackName=stack_name)

    def test_describe_cf_stack_events(self):
        stack_name = "test_stack_name"
        event1 = {'StackId': 'dummy', 'LogicalResourceId': 'res1', 'ResourceStatus': 'UPDATE_COMPLETE'}
        self.cf_service_mock.describe_stack_events.return_value = {'StackEvents': [event1]}
        res = self.cfn_helper.describe_cf_stack_events(stack_name)

        self.cf_service_mock.describe_stack_events.assert_called_once_with(StackName=stack_name)
        assert res == [event1]

    def test_describe_cf_stack_events_with_more(self):
        stack_name = "test_stack_name"
        event1 = {'StackId': 'dummy', 'LogicalResourceId': 'res1', 'ResourceStatus': 'UPDATE_COMPLETE'},
        event2 = {'StackId': 'dummy', 'LogicalResourceId': 'res2', 'ResourceStatus': 'UPDATE_COMPLETE'},
        event3 = {'StackId': 'dummy', 'LogicalResourceId': 'res3', 'ResourceStatus': 'UPDATE_COMPLETE'},
        self.cf_service_mock.describe_stack_events.side_effect = [
            {'StackEvents': [event1, event2], 'NextToken':'next'},
            {'StackEvents': [event3], }
        ]
        res = self.cfn_helper.describe_cf_stack_events(stack_name)

        assert self.cf_service_mock.describe_stack_events.call_count == 2
        self.cf_service_mock.describe_stack_events.assert_has_calls([
            call(StackName=stack_name),
            call(StackName=stack_name, NextToken='next')
        ])
        assert res == [event1, event2, event3]
