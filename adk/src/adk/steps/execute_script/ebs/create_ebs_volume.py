from typing import List, Callable

from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.output import Output
from adk.src.adk.parent_steps.python_step import PythonStep

import boto3


class CreateEbsVolume(PythonStep):
    def get_helper_functions(self) -> List[Callable]:
        return []

    @staticmethod
    def script_handler(params: dict, context) -> dict:
        if params['TargetVolumeType'] == 'gp2':
            response = boto3.client('ec2').create_volume(
                SnapshotId=params['EBSSnapshotIdentifier'],
                AvailabilityZone=params['TargetAvailabilityZone'],
                VolumeType=params['TargetVolumeType']
            )
        else:
            response = boto3.client('ec2').create_volume(
                SnapshotId=params['EBSSnapshotIdentifier'],
                AvailabilityZone=params['TargetAvailabilityZone'],
                VolumeType=params['TargetVolumeType'],
                Iops=params['TargetVolumeIOPS']
            )
        return {'VolumeId': response['VolumeId']}

    def get_outputs(self) -> List[Output]:
        return [Output('CreatedVolumeId', DataType.String, '$.Payload.VolumeId')]

    def get_inputs(self) -> List[str]:
        return ['EBSSnapshotIdentifier',
                'TargetAvailabilityZone',
                'CalculateIopsAndVolType.TargetVolumeType',
                'CalculateIopsAndVolType.TargetVolumeIOPS']

    def get_description(self) -> str:
        return 'Create the new volume by calling ' \
               + '[CreateVolume](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateVolume.html)'
