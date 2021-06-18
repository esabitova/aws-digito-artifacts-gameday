import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.parent_steps.wait_for_resource_step import WaitForResourceStep


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
        self.wait_for_resource_step = WaitForResourceStep(
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
        self.wait_for_resource_step.execute_step(step_input)

    @patch('time.sleep', return_value=None)
    def test_missing_selector_sleeps_until_desired_found(self, mocked_sleep):
        self.mock_ec2.describe_instances.side_effect = [
            {'Reservations': [{'Instances': [{'InstanceType': 't1.nano', 'State': {'NO_NAME': 'running'}}]}]},
            {'Reservations': [{'Instances': [{'InstanceType': 't1.nano', 'State': {'Name': 'FAIL'}}]}]},
            {'Reservations': [{'Instances': [{'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]}]
        step_input = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.wait_for_resource_step.execute_step(step_input)
        self.assertEqual(mocked_sleep.call_count, 2)

    def test_assert_resource_yaml(self):
        self.assertEqual('name: AssertEc2Running\n'
                         'action: aws:waitForAwsResourceProperty\n'
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
                         , self.wait_for_resource_step.get_yaml())
