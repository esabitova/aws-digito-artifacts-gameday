import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.automation.aws_api_step import AwsApiStep


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
        self.aws_api = AwsApiStep(
            name="GetEc2State",
            service="ec2",
            camel_case_api="DescribeInstances",
            api_params={
                'Filters': [{
                    'Name': 'instance-id',
                    'Values': ['{{ InstanceId }}']
                }]},
            description="Ec2 Describe Instance Api",
            outputs=[Output('State', DataType.String, '$.Reservations[0].Instances[0].State.Name')]
        )

    def tearDown(self):
        self.patcher.stop()

    def test_aws_api_yaml(self):
        self.assertEqual(
            'description: Ec2 Describe Instance Api\n'
            'name: GetEc2State\n'
            'action: aws:executeAwsApi\n'
            'inputs:\n'
            '  Service: ec2\n'
            '  Api: DescribeInstances\n'
            '  Filters:\n'
            '  - Name: instance-id\n'
            '    Values:\n'
            '    - \'{{ InstanceId }}\'\n'
            'outputs:\n'
            '- Name: State\n'
            '  Selector: $.Reservations[0].Instances[0].State.Name\n'
            '  Type: String\n', self.aws_api.get_yaml())

    def test_found_selector_passes(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'Name': 'running'}}]}]}
        params = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.aws_api.invoke(params)
        self.assertEqual('running', params['GetEc2State.State'])

    def test_missing_selector_throws(self):
        self.mock_ec2.describe_instances.return_value = {'Reservations': [{'Instances': [
            {'InstanceType': 't1.nano', 'State': {'NO_NAME': 'running'}}]}]}
        step_input = {"InstanceId": 'i-0acf3aed3b36c6f51'}
        self.assertRaises(Exception, self.aws_api.invoke, step_input)
