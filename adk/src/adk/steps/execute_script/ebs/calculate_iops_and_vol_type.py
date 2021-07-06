from typing import List, Callable
import boto3

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep


class CalculateIopsAndVolType(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return []

    @staticmethod
    def script_handler(params: dict, context) -> dict:
        if params['VolumeId'] != "vol-ffffffff":
            describe_response = boto3.client('ec2').describe_volumes(Filters=[{
                'Name': 'volume-id',
                'Values': [params['VolumeId']]
            }])
            default_vol_type = describe_response['Volumes'][0]['VolumeType']
            default_vol_iops = describe_response['Volumes'][0]['Iops']
        else:
            default_vol_type = 'gp2'
            default_vol_iops = 3000
        return {
            'TargetVolumeType':
                params['VolumeType'] if params['VolumeType'] != '' else default_vol_type,
            'TargetVolumeIOPS': params['VolumeIOPS'] if params['VolumeIOPS'] > 0 else default_vol_iops
        }

    def get_outputs(self) -> List[Output]:
        return [
            Output(name='TargetVolumeType', output_type=DataType.String, selector='$.Payload.TargetVolumeType'),
            Output(name='TargetVolumeIOPS', output_type=DataType.Integer, selector='$.Payload.TargetVolumeIOPS')
        ]

    def get_inputs(self) -> List[str]:
        return ['EbsDescribeSnapshot.VolumeId', 'VolumeType', 'VolumeIOPS']

    def get_description(self) -> str:
        return 'Calculate the target VolumeType and IOPS. ' \
               'Requested Params override Original params, use defaults if neither exists'
