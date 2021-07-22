import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.parent_steps.automation.assert_resource_step import AssertResourceStep


@pytest.mark.unit_test
class TestRunner(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.client = self.patcher.start()
        self.mock_autoscaling = MagicMock()
        self.mock_ec2 = MagicMock()
        self.side_effect_map = {
            'autoscaling': self.mock_autoscaling,
            'ec2': self.mock_ec2
        }
        self.client.side_effect = lambda service_name, config=None: self.side_effect_map.get(service_name)
        self.assert_resource_step = AssertResourceStep(
            name="AssertEc2Running",
            service="ec2",
            camel_case_api="DescribeInstances",
            api_params={
                'Filters': [{
                    'Name': 'instance-id',
                    'Values': ['{{ InstanceId }}']
                }]},
            selector='$.Reservations[0].Instances[0].State.Name',
            desired_values=['running', 'started']
        )

    def tearDown(self):
        self.patcher.stop()

    def test_found_selector_passes(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]}
        step_input = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.assert_resource_step.execute_step(step_input)

    def test_missing_selector_throws(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'NO_NAME': 'running'}}]}]}
        step_input = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.assertRaises(Exception, self.assert_resource_step.execute_step, step_input)

    def test_no_desired_values_throws(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'FAILED'}}]}]}
        step_input = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.assertRaises(Exception, self.assert_resource_step.execute_step, step_input)

    def test_missing_input_throws(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]}
        self.assertRaises(Exception, self.assert_resource_step.execute_step, {})

    def test_assert_resource_yaml(self):
        assert_resource_step = AssertResourceStep(
            name="AssertEc2Running",
            service="ec2",
            camel_case_api="DescribeInstances",
            api_params={
                'Filters': [{
                    'Name': 'instance-id',
                    'Values': ['{{ InstanceId }}']
                }]},
            selector='$.Reservations[0].Instances[0].State.Name',
            desired_values=['running', 'started'])
        self.assertEqual('name: AssertEc2Running\n'
                         'action: aws:assertAwsResourceProperty\n'
                         'inputs:\n'
                         '  Service: ec2\n'
                         '  Api: DescribeInstances\n'
                         '  PropertySelector: $.Reservations[0].Instances[0].State.Name\n'
                         '  DesiredValues:\n'
                         '  - running\n'
                         '  - started\n'
                         '  Filters:\n'
                         '  - Name: instance-id\n'
                         '    Values:\n'
                         '    - \'{{ InstanceId }}\'\n'
                         , assert_resource_step.get_yaml())
