import unittest
from unittest.mock import patch, MagicMock

import pytest

from adk.src.adk.builtin_steps.automation.execute_script.ebs.calculate_iops_and_vol_type import CalculateIopsAndVolType


@pytest.mark.unit_test
class TestCalculateIopsAndVolType(unittest.TestCase):
    # Allow viewing long diffs
    maxDiff = None

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

    def tearDown(self):
        self.patcher.stop()

    def test_should_use_provided(self):
        params = {
            'EbsDescribeSnapshot.VolumeId': 'MyVolumeId',
            'VolumeType': 'MyVolumeType',
            'VolumeIOPS': 4
        }
        self.mock_ec2.describe_volumes.return_value = {'Volumes': [{'VolumeType': 'io2', 'Iops': 30}]}
        CalculateIopsAndVolType().invoke(params)
        self.assertEqual(4, params['CalculateIopsAndVolType.TargetVolumeIOPS'])
        self.assertEqual('MyVolumeType', params['CalculateIopsAndVolType.TargetVolumeType'])

    def test_should_default_to_existing(self):
        params = {
            'EbsDescribeSnapshot.VolumeId': 'MyVolumeId',
            'VolumeType': '',
            'VolumeIOPS': 0
        }
        self.mock_ec2.describe_volumes.return_value = {'Volumes': [{'VolumeType': 'io2', 'Iops': 30}]}
        CalculateIopsAndVolType().invoke(params)
        self.assertEqual(30, params['CalculateIopsAndVolType.TargetVolumeIOPS'])
        self.assertEqual('io2', params['CalculateIopsAndVolType.TargetVolumeType'])

    def test_should_not_invoke_vol_ffffffff(self):
        params = {
            'EbsDescribeSnapshot.VolumeId': 'vol-ffffffff',
            'VolumeType': '',
            'VolumeIOPS': 0
        }
        self.mock_ec2.describe_volumes.assert_not_called()
        CalculateIopsAndVolType().invoke(params)
        self.assertEqual(3000, params['CalculateIopsAndVolType.TargetVolumeIOPS'])
        self.assertEqual('gp2', params['CalculateIopsAndVolType.TargetVolumeType'])

    def test_should_print_yaml(self):
        output_yaml = CalculateIopsAndVolType().get_yaml()
        print(output_yaml)
        self.assertEqual(
            'description: Calculate the target VolumeType and IOPS. Requested Params override Original\n'
            '  params, use defaults if neither exists\n'
            'name: CalculateIopsAndVolType\n'
            'action: aws:executeScript\n'
            'inputs:\n'
            '  Runtime: python3.6\n'
            '  Handler: script_handler\n'
            '  Script: |\n'
            '    import boto3\n'
            '\n'
            '    def script_handler(params: dict, context) -> dict:\n'
            '        if params[\'VolumeId\'] != "vol-ffffffff":\n'
            '            describe_response = boto3.client(\'ec2\').describe_volumes(Filters=[{\n'
            '                \'Name\': \'volume-id\',\n'
            '                \'Values\': [params[\'VolumeId\']]\n'
            '            }])\n'
            '            default_vol_type = describe_response[\'Volumes\'][0][\'VolumeType\']\n'
            '            default_vol_iops = describe_response[\'Volumes\'][0][\'Iops\']\n'
            '        else:\n'
            '            default_vol_type = \'gp2\'\n'
            '            default_vol_iops = 3000\n'
            '        return {\n'
            '            \'TargetVolumeType\':\n'
            '                params[\'VolumeType\'] if params[\'VolumeType\'] != \'\' else default_vol_type,\n'
            '            \'TargetVolumeIOPS\': params[\'VolumeIOPS\'] if params[\'VolumeIOPS\'] > 0 else '
            'default_vol_iops\n'
            '        }\n'
            '  InputPayload:\n'
            '    VolumeId: \'{{ EbsDescribeSnapshot.VolumeId }}\'\n'
            '    VolumeType: \'{{ VolumeType }}\'\n'
            '    VolumeIOPS: \'{{ VolumeIOPS }}\'\n'
            'outputs:\n'
            '- Name: TargetVolumeType\n'
            '  Selector: $.Payload.TargetVolumeType\n'
            '  Type: String\n'
            '- Name: TargetVolumeIOPS\n'
            '  Selector: $.Payload.TargetVolumeIOPS\n'
            '  Type: Integer\n', output_yaml)
